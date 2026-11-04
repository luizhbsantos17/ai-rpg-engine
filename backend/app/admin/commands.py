"""Catálogo de comandos administrativos e de debug (docs/ADMIN_COMMANDS.md).

Consultas só leem. Alterações viram operações do motor com origem "admin" (validadas e registradas
como as da IA); quando possível guardam as operações inversas para `/admin undo`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.admin.parser import Command
from app.admin.targets import AdminTargetError, by_name, resolve_target
from app.engine.operations import OperationContext, OperationOutcome, apply_operations
from app.engine.time import format_world_time
from app.persistence.models import Entity, ItemInstance
from app.persistence.repositories import CampaignData
from app.persistence.snapshots import (
    SnapshotError,
    export_campaign,
    list_snapshots,
    read_snapshot,
    restore_campaign,
    write_snapshot,
)

MAX_TEXT = 600


class AdminError(Exception):
    pass


@dataclass
class AdminContext:
    data: CampaignData
    command: Command
    owner_id: str = ""
    data_dir: Path | None = None  # onde ficam os snapshots (data/backups/<campanha>/)


@dataclass
class AdminOutcome:
    lines: list[str]
    changed: bool = False
    undo: list[dict[str, Any]] | None = None
    data: dict[str, Any] | None = None


@dataclass(frozen=True)
class CommandSpec:
    handler: Callable[[AdminContext], AdminOutcome]
    description: str
    usage: str
    destructive: bool = False
    audited: bool = True


COMMANDS: dict[tuple[str, str], CommandSpec] = {}


def command(group: str, verb: str, description: str, usage: str, destructive: bool = False, audited: bool = True):
    def register(fn):
        COMMANDS[(group, verb)] = CommandSpec(fn, description, usage, destructive, audited)
        return fn

    return register


# ---------------------------------------------------------------- utilidades

def _apply(ctx: AdminContext, operations: list[dict[str, Any]]) -> list[OperationOutcome]:
    campaign = ctx.data.campaign()
    op_ctx = OperationContext(ctx.data, source="admin", campaign_seed=campaign.rng_seed,
                              world_time=campaign.world_clock, seed_scope="admin")
    outcomes = apply_operations(op_ctx, operations)
    rejected = [o for o in outcomes if o.status == "rejected"]
    if rejected:
        raise AdminError("Recusado pelo motor: " + "; ".join(o.reason or "" for o in rejected))
    return outcomes


def _int_option(ctx: AdminContext, name: str, default: int) -> int:
    raw = ctx.command.options.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise AdminError(f"--{name} precisa ser um número inteiro.") from None
    if value < 1:
        raise AdminError(f"--{name} precisa ser maior que zero.")
    return value


def _definition_key(ctx: AdminContext, kind: str, key_or_name: str) -> str:
    if ctx.data.definitions.current(kind, key_or_name) is not None:
        return key_or_name
    matches = [d.key for d in ctx.data.definitions.list_current(kind)
               if str(d.data.get("name", "")).lower() == key_or_name.lower()]
    if len(matches) == 1:
        return matches[0]
    raise AdminError(f"Não existe {kind} \"{key_or_name}\". Veja /debug inspect_rules {kind}.")


def _entity_summary(ctx: AdminContext, entity: Entity) -> list[str]:
    data = ctx.data
    location = data.entities.get(entity.location_id) if entity.location_id else None
    lines = [f"{entity.name} ({entity.kind}) · status {entity.status} · nível de simulação {entity.sim_tier} · id {entity.id}",
             f"Local: {location.name if location else '—'}"]
    attributes = data.attributes.for_entity(entity.id)
    lines.append("Atributos: " + (", ".join(
        f"{a.definition_key}={a.value}" + (f"/{a.max_value}" if a.max_value is not None else "") for a in attributes
    ) or "—"))
    lines.append("Habilidades: " + (", ".join(f"{s.definition_key} nv {s.level}" for s in data.skills.for_entity(entity.id)) or "—"))
    lines.append("Itens: " + (", ".join(f"{i.definition_key}×{i.quantity} ({i.id[:8]})" for i in data.items.held_by(entity.id)) or "—"))
    effects = data.effects.active_for(entity.id)
    if effects:
        lines.append("Efeitos: " + ", ".join(
            e.definition_key + (f" até {format_world_time(e.ends_at)}" if e.ends_at is not None else "") for e in effects))
    disguises = data.disguises.active_for(entity.id)
    if disguises:
        lines.append("Ocultações: " + ", ".join(
            f"{d.field}→\"{d.presented_value}\"" if d.presented_value else f"{d.field} oculto" for d in disguises))
    return lines


# ---------------------------------------------------------------- ajuda

@command("admin", "help", "Lista os comandos ou explica um.", "/admin help [comando]", audited=False)
@command("debug", "help", "Lista os comandos ou explica um.", "/debug help [comando]", audited=False)
def help_command(ctx: AdminContext) -> AdminOutcome:
    if ctx.command.args:
        wanted = ctx.command.args[0].lstrip("/").lower()
        for (group, verb), spec in COMMANDS.items():
            if wanted in (verb, f"{group} {verb}"):
                flag = " (destrutivo: pede confirmação)" if spec.destructive else ""
                return AdminOutcome([f"{spec.usage}{flag}", spec.description])
        raise AdminError(f"Comando \"{wanted}\" não existe.")
    lines = []
    for (group, verb), spec in sorted(COMMANDS.items()):
        if verb != "help":
            lines.append(f"{spec.usage}{' ⚠' if spec.destructive else ''} — {spec.description}")
    return AdminOutcome(lines + ["⚠ = destrutivo (pede código de confirmação)."])


# ---------------------------------------------------------------- consultas /admin

@command("admin", "status", "Ficha VERDADEIRA completa (padrão: protagonista).", "/admin status [alvo]", audited=False)
def status(ctx: AdminContext) -> AdminOutcome:
    entity, _ = resolve_target(ctx.data, ctx.command.args or ["player"])
    return AdminOutcome(_entity_summary(ctx, entity))


@command("admin", "inspect", "Estado verdadeiro + o que a entidade sabe e lembra.", "/admin inspect <alvo>", audited=False)
def inspect(ctx: AdminContext) -> AdminOutcome:
    entity, _ = resolve_target(ctx.data, ctx.command.args)
    lines = _entity_summary(ctx, entity)
    known = ctx.data.knowledge.known_by(entity.id)
    lines.append("Sabe: " + (", ".join(f"{k.subject[:8]}.{k.field}={k.known_value} ({k.level})" for k in known) or "—"))
    memories = ctx.data.memories.recall(entity.id, 5)
    lines.append("Lembra: " + (" | ".join(m.content[:150] for m in memories) or "—"))
    return AdminOutcome(lines)


@command("admin", "audit", "Últimos comandos administrativos.", "/admin audit [--last n]", audited=False)
def audit(ctx: AdminContext) -> AdminOutcome:
    rows = ctx.data.admin_audit.latest(_int_option(ctx, "last", 15))
    return AdminOutcome([f"{r.created_at:%d/%m %H:%M} {r.command}{' (desfeito)' if r.undone else ''}" for r in rows]
                        or ["Nenhum comando ainda."])


# ---------------------------------------------------------------- alterações /admin

@command("admin", "set", "Altera um atributo. Recursos aceitam valor/máximo.", "/admin set <alvo>.<atributo> <valor>")
def set_value(ctx: AdminContext) -> AdminOutcome:
    if len(ctx.command.args) < 2 or "." not in ctx.command.args[0]:
        raise AdminError("Uso: /admin set player.forca 20  ·  /admin set \"Ana\".vida 15/20")
    target_text, key = ctx.command.args[0].rsplit(".", 1)
    entity = _path_target(ctx, target_text)
    raw = ctx.command.args[1]
    value, maximum = (raw.split("/", 1) + [None])[:2] if "/" in raw else (raw, None)
    current = ctx.data.attributes.get_for(entity.id, key)
    # Copiar ANTES de aplicar: a operação altera este mesmo registro.
    previous = (current.value, current.max_value) if current is not None else None
    op = {"op": "attribute.set", "entity": entity.id, "key": key, "value": value, "reason": "comando admin"}
    if maximum is not None:
        op["max"] = maximum
    _apply(ctx, [op])
    undo = None
    if previous is not None:
        undo_op = {"op": "attribute.set", "entity": entity.id, "key": key, "value": previous[0], "reason": "admin undo"}
        if previous[1] is not None:
            undo_op["max"] = previous[1]
        undo = [undo_op]
    before = previous[0] if previous else "—"
    return AdminOutcome([f"{entity.name}.{key}: {before} → {raw}"], changed=True, undo=undo)


def _path_target(ctx: AdminContext, text: str) -> Entity:
    if text.lower() == "player":
        return resolve_target(ctx.data, ["player"])[0]
    entity = ctx.data.entities.get(text)
    return entity if entity is not None else by_name(ctx.data, text.strip('"'))


@command("admin", "give", "Concede habilidade ou item.", "/admin give <alvo> skill|item <chave ou nome> [--qty n] [--level n]")
def give(ctx: AdminContext) -> AdminOutcome:
    entity, used = resolve_target(ctx.data, ctx.command.args)
    kind, name = _kind_and_name(ctx, used)
    if kind == "skill":
        key = _definition_key(ctx, "skill", name)
        level = _int_option(ctx, "level", 1)
        _apply(ctx, [{"op": "skill.grant", "entity": entity.id, "key": key, "level": level, "reason": "comando admin"}])
        return AdminOutcome([f"{entity.name} recebeu a habilidade {key} (nível {level})."], changed=True,
                            undo=[{"op": "skill.revoke", "entity": entity.id, "key": key, "reason": "admin undo"}])
    key = _definition_key(ctx, "item", name)
    quantity = _int_option(ctx, "qty", 1)
    outcome = _apply(ctx, [{"op": "item.create", "key": key, "owner": entity.id, "quantity": quantity,
                            "reason": "comando admin"}])[0]
    return AdminOutcome([f"{entity.name} recebeu {key} ×{quantity}."], changed=True,
                        undo=[{"op": "item.destroy", "item": outcome.result["item_id"], "quantity": quantity,
                               "reason": "admin undo"}])


@command("admin", "remove", "Remove habilidade ou todos os itens de um tipo.", "/admin remove <alvo> skill|item <chave ou nome>",
         destructive=True)
def remove(ctx: AdminContext) -> AdminOutcome:
    entity, used = resolve_target(ctx.data, ctx.command.args)
    kind, name = _kind_and_name(ctx, used)
    if kind == "skill":
        key = _definition_key(ctx, "skill", name)
        _apply(ctx, [{"op": "skill.revoke", "entity": entity.id, "key": key, "reason": "comando admin"}])
        return AdminOutcome([f"{entity.name} perdeu a habilidade {key}."], changed=True)
    key = _definition_key(ctx, "item", name)
    items = [i for i in ctx.data.items.held_by(entity.id) if i.definition_key == key]
    if not items:
        raise AdminError(f"{entity.name} não tem {key}.")
    _apply(ctx, [{"op": "item.destroy", "item": i.id, "reason": "comando admin"} for i in items])
    return AdminOutcome([f"{entity.name} perdeu todos os {key}."], changed=True)


def _kind_and_name(ctx: AdminContext, used: int) -> tuple[str, str]:
    rest = ctx.command.args[used:]
    if len(rest) < 2 or rest[0].lower() not in ("skill", "item"):
        raise AdminError(f"Uso: {COMMANDS[(ctx.command.group, ctx.command.verb)].usage}")
    return rest[0].lower(), rest[1]


@command("admin", "teleport", "Move uma entidade para um local.", "/admin teleport <alvo> <local>")
def teleport(ctx: AdminContext) -> AdminOutcome:
    entity, used = resolve_target(ctx.data, ctx.command.args)
    destination, _ = resolve_target(ctx.data, ctx.command.args, used)
    previous = entity.location_id
    _apply(ctx, [{"op": "entity.move", "entity": entity.id, "to": destination.id, "reason": "comando admin"}])
    undo = [{"op": "entity.move", "entity": entity.id, "to": previous, "reason": "admin undo"}] if previous else None
    return AdminOutcome([f"{entity.name} foi para {destination.name}."], changed=True, undo=undo)


@command("admin", "create", "Cria um personagem no local do protagonista.", "/admin create npc \"Nome\" [--desc \"...\"] [--kind creature]")
def create(ctx: AdminContext) -> AdminOutcome:
    args = ctx.command.args
    if len(args) < 2 or args[0].lower() != "npc":
        raise AdminError("Uso: /admin create npc \"Nome\" [--desc \"...\"]")
    player = ctx.data.entities.player()
    op: dict[str, Any] = {"op": "entity.create", "kind": ctx.command.options.get("kind", "character"), "name": args[1],
                          "data": {"description": ctx.command.options.get("desc", "")}, "sim_tier": 1,
                          "reason": "comando admin"}
    if player is not None and player.location_id:
        op["location"] = player.location_id
    outcome = _apply(ctx, [op])[0]
    entity_id = outcome.result["entity_id"]
    return AdminOutcome([f"Criado: {args[1]} (id {entity_id})."], changed=True,
                        undo=[{"op": "entity.remove", "entity": entity_id, "reason": "admin undo"}])


@command("admin", "kill", "Marca uma entidade como morta (sem aplicar regra de morte).", "/admin kill <alvo>", destructive=True)
def kill(ctx: AdminContext) -> AdminOutcome:
    entity, _ = resolve_target(ctx.data, ctx.command.args)
    _apply(ctx, [{"op": "entity.update", "entity": entity.id, "status": "dead", "reason": "comando admin"}])
    return AdminOutcome([f"{entity.name} está morto(a)."], changed=True)


@command("admin", "world.time", "Avança o relógio do mundo (processa agendamentos e efeitos).",
         "/admin world.time advance <duração>", destructive=True)
def world_time(ctx: AdminContext) -> AdminOutcome:
    args = ctx.command.args
    if len(args) != 2 or args[0].lower() != "advance":
        raise AdminError("Uso: /admin world.time advance 30d")
    result = _apply(ctx, [{"op": "time.advance", "duration": args[1], "reason": "comando admin"}])[0].result
    lines = [f"Tempo: {result['from_text']} → {result['to_text']}."]
    lines += [f"Disparou: {t['summary']}" for t in result["triggered"]]
    return AdminOutcome(lines, changed=True)


@command("admin", "undo", "Desfaz o último comando administrativo reversível.", "/admin undo")
def undo(ctx: AdminContext) -> AdminOutcome:
    last = ctx.data.admin_audit.last_undoable()
    if last is None:
        raise AdminError("Nada para desfazer.")
    _apply(ctx, last.undo_operations)
    last.undone = True
    ctx.data.session.flush()
    return AdminOutcome([f"Desfeito: {last.command}"], changed=True)


# ---------------------------------------------------------------- snapshots (D-014)

@command("admin", "snapshot", "Backups desta campanha: create [\"rótulo\"], list, restore <id>.",
         "/admin snapshot create [\"rótulo\"] | list | restore <id>")
def snapshot(ctx: AdminContext) -> AdminOutcome:
    args = ctx.command.args
    action = args[0].lower() if args else "list"
    if action == "list":
        items = list_snapshots(ctx.data_dir, ctx.data.campaign_id)
        return AdminOutcome([f"{i['id']}  {i['label']}" for i in items] or ["Nenhum snapshot ainda."])
    if action == "create":
        label = args[1] if len(args) > 1 else "manual"
        snapshot_id = write_snapshot(ctx.data_dir, export_campaign(ctx.data.session, ctx.data.campaign_id), label)
        return AdminOutcome([f"Snapshot criado: {snapshot_id}"])
    raise AdminError("Use: /admin snapshot create [\"rótulo\"] · /admin snapshot list · /admin snapshot.restore <id>")


@command("admin", "snapshot.restore", "Volta a campanha para um snapshot (as outras não mudam).",
         "/admin snapshot.restore <id>", destructive=True)
def snapshot_restore(ctx: AdminContext) -> AdminOutcome:
    if not ctx.command.args:
        raise AdminError("Use: /admin snapshot.restore <id>  (veja os ids com /admin snapshot list)")
    try:
        saved = read_snapshot(ctx.data_dir, ctx.data.campaign_id, ctx.command.args[0])
        restore_campaign(ctx.data.session, saved, ctx.owner_id, replace_existing=True)
    except SnapshotError as exc:
        raise AdminError(str(exc)) from None
    return AdminOutcome([f"Campanha restaurada para o snapshot {ctx.command.args[0]} ({saved.get('label', '')}).",
                         "Um snapshot do estado anterior foi guardado antes."], changed=True)


# ---------------------------------------------------------------- /debug (somente leitura)

@command("debug", "show_context", "Mensagens enviadas à IA na última chamada.", "/debug show_context [--role narrator]", audited=False)
def show_context(ctx: AdminContext) -> AdminOutcome:
    role = ctx.command.options.get("role", "narrator")
    request = next((r for r in ctx.data.ai_requests.latest(50) if r.role == role), None)
    if request is None or not request.request_messages:
        raise AdminError(f"Nenhuma chamada '{role}' registrada ainda.")
    lines = [f"Chamada {role} · modelo {request.model} · {request.tokens_in} tokens de entrada"]
    for message in request.request_messages:
        content = message["content"]
        lines.append(f"[{message['role']}] {content[:MAX_TEXT]}{'…' if len(content) > MAX_TEXT else ''}")
    return AdminOutcome(lines)


@command("debug", "show_events", "Log de eventos.", "/debug show_events [--last n]", audited=False)
def show_events(ctx: AdminContext) -> AdminOutcome:
    events = ctx.data.events.list_ordered(last=_int_option(ctx, "last", 20))
    return AdminOutcome([f"#{e.seq} [{e.source}] {e.type} {json.dumps(e.payload, ensure_ascii=False)[:200]}" for e in events]
                        or ["Nenhum evento."])


@command("debug", "show_memory", "Resumos da campanha, ou memórias e conhecimento de um alvo.", "/debug show_memory [alvo]",
         audited=False)
def show_memory(ctx: AdminContext) -> AdminOutcome:
    if not ctx.command.args:
        summaries = ctx.data.summaries.latest(10)
        return AdminOutcome([f"Turnos {s.from_turn}–{s.to_turn}: {s.content[:MAX_TEXT]}" for s in summaries]
                            or ["Nenhum resumo ainda."])
    entity, _ = resolve_target(ctx.data, ctx.command.args)
    memories = ctx.data.memories.recall(entity.id, 20)
    known = ctx.data.knowledge.known_by(entity.id)
    return AdminOutcome([f"Memórias de {entity.name}:"] + [f"- ({m.importance}) {m.content[:200]}" for m in memories]
                        + [f"Conhecimento: {k.subject[:8]}.{k.field}={k.known_value} ({k.level}, {k.source})" for k in known])


@command("debug", "inspect_entity", "Dados brutos de uma entidade.", "/debug inspect_entity <alvo>", audited=False)
def inspect_entity(ctx: AdminContext) -> AdminOutcome:
    entity, _ = resolve_target(ctx.data, ctx.command.args)
    raw = {"id": entity.id, "kind": entity.kind, "name": entity.name, "status": entity.status,
           "location_id": entity.location_id, "is_player": entity.is_player, "sim_tier": entity.sim_tier, "data": entity.data}
    return AdminOutcome(_entity_summary(ctx, entity) + [json.dumps(raw, ensure_ascii=False)[:2000]], data=raw)


@command("debug", "inspect_rules", "Definições atuais (e versões).", "/debug inspect_rules [tipo]", audited=False)
def inspect_rules(ctx: AdminContext) -> AdminOutcome:
    kind = ctx.command.args[0] if ctx.command.args else None
    rows = ctx.data.definitions.list_current(kind)
    return AdminOutcome([f"{d.kind}/{d.key} v{d.version} [{d.created_by}]: {json.dumps(d.data, ensure_ascii=False)[:300]}"
                         for d in rows] or ["Nenhuma definição."])


@command("debug", "inspect_ai_requests", "Chamadas à IA: papel, modelo, tokens, tempo, erros.", "/debug inspect_ai_requests [--last n]",
         audited=False)
def inspect_ai_requests(ctx: AdminContext) -> AdminOutcome:
    rows = ctx.data.ai_requests.latest(_int_option(ctx, "last", 10))
    return AdminOutcome([f"{r.created_at:%H:%M:%S} {r.role} {r.provider}/{r.model} in={r.tokens_in} out={r.tokens_out} "
                         f"{r.duration_ms}ms" + (f" ERRO: {r.error[:150]}" if r.error else "") for r in rows]
                        or ["Nenhuma chamada ainda."])


@command("debug", "validate_world", "Procura inconsistências no estado da campanha.", "/debug validate_world", audited=False)
def validate_world(ctx: AdminContext) -> AdminOutcome:
    problems = find_inconsistencies(ctx.data)
    return AdminOutcome(problems or ["Nenhuma inconsistência encontrada."], data={"problems": problems})


def find_inconsistencies(data: CampaignData) -> list[str]:
    problems: list[str] = []
    entities = {e.id: e for e in data.entities.list(include_removed=True)}
    alive = {i for i, e in entities.items() if e.status != Entity.STATUS_REMOVED}
    for item in data.items.active_ids_conflicting():
        problems.append(f"Item {item.definition_key} ({item.id[:8]}) sem dono e sem local, ou com os dois.")
    for entity in entities.values():
        if entity.location_id and entity.location_id not in alive and entity.status != Entity.STATUS_REMOVED:
            problems.append(f"{entity.name} está num local que não existe mais.")
        for attribute in data.attributes.for_entity(entity.id):
            if data.definitions.current("attribute", attribute.definition_key) is None:
                problems.append(f"{entity.name}: atributo '{attribute.definition_key}' sem definição.")
            if attribute.max_value is not None:
                try:
                    if float(attribute.value) > float(attribute.max_value):
                        problems.append(f"{entity.name}: {attribute.definition_key} acima do máximo.")
                except ValueError:
                    problems.append(f"{entity.name}: {attribute.definition_key} com número inválido.")
        for skill in data.skills.for_entity(entity.id):
            if data.definitions.current("skill", skill.definition_key) is None:
                problems.append(f"{entity.name}: habilidade '{skill.definition_key}' sem definição.")
    for entity_id in alive:
        for item in data.items.held_by(entity_id):
            if item.status == ItemInstance.STATUS_ACTIVE and data.definitions.current("item", item.definition_key) is None:
                problems.append(f"Item '{item.definition_key}' sem definição.")
    if data.turns.find_processing() is not None:
        problems.append("Há uma jogada em andamento (ou travada).")
    if data.entities.player() is None and data.turns.count_completed():
        problems.append("A campanha já tem jogadas, mas nenhum protagonista.")
    return problems


__all__ = ["COMMANDS", "AdminContext", "AdminError", "AdminOutcome", "AdminTargetError"]
