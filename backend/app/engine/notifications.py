"""Textos sobre o que o motor fez num turno.

- `describe_for_narrator`: a verdade completa, para a IA narrar de acordo (ela é o mestre).
- `player_notices`: só o que o PROTAGONISTA percebe/sabe de si mesmo, como mensagens de
  sistema (SPEC 12.2). Estado de NPCs não aparece aqui (SPEC 6.1: status alheios são ocultos).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.engine.operations import OperationOutcome


@dataclass(frozen=True)
class PlayerNotice:
    tag: str  # SISTEMA | TESTE | ALERTA
    text: str

    def as_message(self) -> str:
        return f"[{self.tag}] {self.text}"


def describe_for_narrator(outcomes: list[OperationOutcome]) -> list[str]:
    lines: list[str] = []
    for outcome in outcomes:
        r = outcome.result
        if outcome.status == "rejected":
            lines.append(f"(não aconteceu — tentativa inválida de {outcome.op}: {outcome.reason})")
        elif outcome.status == "skipped":
            continue
        elif outcome.op == "check.request":
            lines.append(_check_line(r))
        elif outcome.op == "time.advance":
            lines.extend(_time_lines(r))
        else:
            lines.append(_applied_line(outcome.op, r))
        if outcome.status == "applied" and r.get("death"):
            lines.append(_death_line(r["death"]))
    return [line for line in lines if line]


DEATH_TEXT = {
    "permanent": "MORREU (morte permanente neste mundo)",
    "unconscious": "caiu INCONSCIENTE",
    "resurrection": "MORREU, mas pela regra deste mundo voltará à vida",
    "reincarnation": "MORREU e vai REENCARNAR",
    "narrative": "chegou ao limite da vida; aplique a regra de morte do mundo na narração",
}


def _death_line(d: dict[str, Any]) -> str:
    back = f" (volta em {d['returns_at']})" if d.get("returns_at") else ""
    rule = f" Regra: {d['description']}" if d.get("description") else ""
    return f"{d['name']} {DEATH_TEXT[d['mode']]}{back}.{rule}"


PLAYER_DEATH_TEXT = {
    "permanent": "Você morreu.",
    "unconscious": "Você perdeu a consciência.",
    "resurrection": "Você morreu… mas não para sempre.",
    "reincarnation": "Você morreu. Uma nova vida espera.",
    "narrative": "Você chegou ao limite.",
}


NARRATOR_LEVELS = {"confirmed": "descobriu", "partial": "descobriu em parte (percebe que há algo oculto)",
                   "estimated": "só estimou", "unknown": "não descobriu nada"}


def _assessment_line(r: dict[str, Any]) -> str:
    parts = []
    for f in r["findings"]:
        if f["level"] == "false":
            parts.append(f"{f['field']}: ENGANADO, acredita em \"{f['value']}\" (verdade: \"{f['truth']}\")")
        else:
            value = f" = {f['value']}" if f["value"] is not None else ""
            parts.append(f"{f['field']}: {NARRATOR_LEVELS[f['level']]}{value}")
    detected = f" {r['target']} PERCEBEU a tentativa." if r["detected"] else ""
    return f"Avaliação '{r['label']}' de {r['observer']} sobre {r['target']} (total {r['total']}): " + "; ".join(parts) + "." + detected


def _nested(outcomes: list[dict[str, Any]]) -> list[OperationOutcome]:
    return [OperationOutcome(**o) for o in outcomes]


def _time_lines(r: dict[str, Any]) -> list[str]:
    lines = [f"O tempo passou: {r['duration_text']} (agora {r['to_text']})."]
    for event in r["triggered"]:
        lines.append(f"Enquanto o tempo passava ({event['due_text']}): {event['summary']}")
        lines.extend("  " + line for line in describe_for_narrator(_nested(event["outcomes"])))
    lines.extend(f"Terminou o efeito {e['name']} em {e['target']}." for e in r["expired_effects"])
    return lines


def _check_line(r: dict[str, Any]) -> str:
    verdict = "SUCESSO" if r["success"] else "FALHA"
    if r["critical_success"]:
        verdict = "SUCESSO CRÍTICO"
    elif r["critical_failure"]:
        verdict = "FALHA CRÍTICA"
    target = f" contra {r['target']}" if r.get("target") else ""
    return (f"Teste '{r['label']}' de {r['actor']}{target}: dados {r['natural']} + modificador {r['modifier']} "
            f"= {r['total']} contra dificuldade {r['difficulty']} → {verdict}.")


def _applied_line(op: str, r: dict[str, Any]) -> str:
    if op == "entity.create":
        return f"Surgiu {r['name']} ({r['kind']})."
    if op == "entity.update":
        changes = r.get("changes", {})
        if "status" in changes and changes["status"]["to"] == "dead":
            return f"{r['name']} morreu."
        return f"{r['name']} mudou ({', '.join(changes)})."
    if op == "entity.remove":
        return f"{r['name']} saiu da história."
    if op == "entity.move":
        return f"{r['name']} foi para {r['to_name']}."
    if op in ("attribute.set", "attribute.modify", "resource.spend", "resource.restore"):
        maximum = f" (máx. {r['max']})" if r.get("max") else ""
        return f"{r['attribute']} de {r['name']}: {r.get('from')} → {r['to']}{maximum}."
    if op == "skill.grant":
        return f"{r['name']} adquiriu a habilidade {r['skill']} (nível {r['level']})."
    if op == "skill.evolve":
        return f"{r['skill']} de {r['name']} evoluiu do nível {r['from']} para {r['to']}."
    if op == "skill.revoke":
        return f"{r['name']} perdeu a habilidade '{r['key']}'."
    if op == "skill.use":
        target = f" em {r['target']}" if r.get("target") else ""
        costs = ", ".join(f"{c['amount']} de {c['resource']}" for c in r["costs"])
        return f"{r['name']} usou {r['skill']}{target}" + (f" (gastou {costs})." if costs else ".")
    if op == "item.create":
        return f"{r['holder']} recebeu {r['item']} ×{r['quantity']}."
    if op == "item.transfer":
        return f"{r['item']} ×{r['quantity']} foi para {r['to']}."
    if op == "item.destroy":
        return f"{r['item']} ×{r['destroyed']} foi destruído."
    if op == "event.record":
        return f"Acontecimento: {r['summary']}"
    if op == "canon.assert":
        return f"Fato do mundo estabelecido ({r['status']}): {r['statement']}"
    if op == "canon.amend":
        return f"Fato do mundo mudou: antes \"{r['previous']}\", agora \"{r['statement']}\"."
    if op == "knowledge.assess":
        return _assessment_line(r)
    if op == "disguise.apply":
        if r["falsified"]:
            return f"{r['name']} passa a mostrar '{r['field']}' FALSO como \"{r['presented_value']}\" (força {r['power']})."
        return f"{r['name']} passa a ocultar '{r['field']}' (força {r['power']})."
    if op == "disguise.remove":
        return f"{r['name']} deixou de ocultar '{r['field']}'."
    if op == "quest.create":
        hidden = " (oculta: o jogador ainda não sabe)" if r["hidden"] else ""
        return f"Nova missão{hidden}: {r['title']}."
    if op == "quest.update":
        parts = [f"objetivo cumprido: {text}" for text in r["completed_objectives"]]
        parts += [f"novo objetivo: {text}" for text in r["added_objectives"]]
        if r["status"] != r["previous_status"]:
            parts.append(f"situação: {r['status']}")
        if r["revealed"]:
            parts.append("revelada ao jogador")
        return f"Missão '{r['title']}': {'; '.join(parts)}."
    if op == "relationship.change":
        parts = [f"{k} {c['delta']:+g} (agora {c['to']:g})" for k, c in r["changes"].items()]
        parts += [f"+rótulo '{label}'" for label in r["added"]] + [f"-rótulo '{label}'" for label in r["removed"]]
        return f"O que {r['source']} sente por {r['target']} mudou: {', '.join(parts)} — porque {r['cause']}."
    if op == "effect.apply":
        until = f" até {r['ends_text']}" if r.get("ends_text") else ""
        return f"{r['name']} está sob o efeito {r['effect']}{until}."
    if op == "effect.remove":
        return f"O efeito {r['effect']} de {r['name']} terminou."
    if op in ("definition.create", "definition.amend", "event.schedule"):
        return ""  # regras e planos futuros não são narrados (agendamentos são segredos do mestre)
    return f"{op} aplicado."


def player_notices(outcomes: list[OperationOutcome], player_id: str | None) -> list[PlayerNotice]:
    if player_id is None:
        return []
    notices: list[PlayerNotice] = []
    for outcome in outcomes:
        if outcome.status != "applied":
            continue
        if outcome.op == "time.advance":
            notices.extend(_time_notices(outcome.result, player_id))
            continue
        notice = _player_notice(outcome.op, outcome.result, player_id)
        if notice:
            notices.append(notice)
        death = outcome.result.get("death")
        if death and death["entity_id"] == player_id:
            back = f" (até {death['returns_at']})" if death.get("returns_at") else ""
            notices.append(PlayerNotice("ALERTA", PLAYER_DEATH_TEXT[death["mode"]] + back))
    return notices


# O que o JOGADOR vê: informação falsa aparece como confirmada (ele não sabe que foi enganado).
PLAYER_LEVELS = {"confirmed": "confirmado", "false": "confirmado", "partial": "parcial", "estimated": "estimado"}


def _assessment_notice(r: dict[str, Any], player_id: str) -> PlayerNotice | None:
    if r["observer_id"] == player_id:
        parts = []
        for f in r["findings"]:
            if f["level"] == "unknown":
                parts.append(f"{f['field']}: não descoberto")
            else:
                parts.append(f"{f['field']} = {f['value']} ({PLAYER_LEVELS[f['level']]})")
        return PlayerNotice("ANÁLISE", f"{r['target']}: " + "; ".join(parts) + ".")
    if r["target_id"] == player_id and r["detected"]:
        return PlayerNotice("ALERTA", f"Você sentiu que {r['observer']} tentou avaliá-lo.")
    return None


QUEST_STATUS_TEXT = {"completed": "Missão concluída", "failed": "Missão falhou", "abandoned": "Missão abandonada",
                     "active": "Missão retomada"}


def _quest_notice(op: str, r: dict[str, Any]) -> PlayerNotice | None:
    """Missões ocultas não aparecem (até serem reveladas)."""
    if r["hidden"]:
        return None
    if op == "quest.create" or r.get("revealed"):
        return PlayerNotice("MISSÃO", f"Nova missão: {r['title']}.")
    if r["status"] != r["previous_status"]:
        return PlayerNotice("MISSÃO", f"{QUEST_STATUS_TEXT[r['status']]}: {r['title']}.")
    parts = [f"objetivo cumprido — {t}" for t in r["completed_objectives"]]
    parts += [f"novo objetivo — {t}" for t in r["added_objectives"]]
    return PlayerNotice("MISSÃO", f"{r['title']}: {'; '.join(parts)}.") if parts else None


def _time_notices(r: dict[str, Any], player_id: str) -> list[PlayerNotice]:
    """O jogador vê o relógio e o que o afeta diretamente; o resto dos agendamentos é narrado (ou não)."""
    notices = [PlayerNotice("SISTEMA", f"Tempo: {r['to_text']} (+{r['duration_text']}).")]
    for event in r["triggered"]:
        notices.extend(player_notices(_nested(event["outcomes"]), player_id))
    notices.extend(PlayerNotice("SISTEMA", f"Efeito terminou: {e['name']}.")
                   for e in r["expired_effects"] if e["target_id"] == player_id)
    return notices


def _player_notice(op: str, r: dict[str, Any], player_id: str) -> PlayerNotice | None:
    mine = r.get("entity_id") == player_id
    if op == "entity.create" and mine:
        return PlayerNotice("SISTEMA", f"Personagem criado: {r['name']}.")
    if op == "check.request" and player_id in (r.get("actor_id"), r.get("target_id")):
        verdict = "sucesso" if r["success"] else "falha"
        if r["critical_success"]:
            verdict = "sucesso crítico"
        elif r["critical_failure"]:
            verdict = "falha crítica"
        return PlayerNotice("TESTE", f"{r['label']}: {r['natural']} + {r['modifier']} = {r['total']} "
                                     f"(dificuldade {r['difficulty']}) → {verdict}.")
    if op in ("quest.create", "quest.update"):
        return _quest_notice(op, r)
    if op == "knowledge.assess":
        return _assessment_notice(r, player_id)
    if op in ("disguise.apply", "disguise.remove") and mine:
        verb = "ativa" if op == "disguise.apply" else "desfeita"
        return PlayerNotice("SISTEMA", f"Ocultação {verb}: {r['field']}.")
    if not mine and op not in ("item.create", "item.transfer"):
        return None
    if op == "effect.apply":
        until = f" (até {r['ends_text']})" if r.get("ends_text") else ""
        return PlayerNotice("ALERTA", f"Efeito: {r['effect']}{until}.")
    if op == "effect.remove":
        return PlayerNotice("SISTEMA", f"Efeito terminou: {r['effect']}.")
    if op in ("attribute.set", "attribute.modify", "resource.spend", "resource.restore"):
        maximum = f" / {r['max']}" if r.get("max") else ""
        return PlayerNotice("SISTEMA", f"{r['attribute']}: {r.get('from') or '—'} → {r['to']}{maximum}")
    if op == "skill.grant":
        return PlayerNotice("SISTEMA", f"Nova habilidade adquirida: {r['skill']} (nível {r['level']}).")
    if op == "skill.evolve":
        return PlayerNotice("SISTEMA", f"{r['skill']} evoluiu: nível {r['from']} → {r['to']}.")
    if op == "skill.revoke":
        return PlayerNotice("ALERTA", f"Habilidade perdida: {r['key']}.")
    if op == "skill.use":
        costs = ", ".join(f"−{c['amount']} {c['resource']} ({c['to']})" for c in r["costs"])
        ready = f" · pronta de novo em {r['ready_again']}" if r.get("ready_again") else ""
        return PlayerNotice("SISTEMA", f"Habilidade usada: {r['skill']}" + (f" · {costs}" if costs else "") + ready + ".")
    if op == "entity.update" and r.get("changes", {}).get("status", {}).get("to") == "dead":
        return PlayerNotice("ALERTA", "Você morreu.")
    if op == "entity.move":
        return PlayerNotice("SISTEMA", f"Local: {r['to_name']}.")
    if op == "item.create" and r.get("holder_id") == player_id:
        return PlayerNotice("SISTEMA", f"Item recebido: {r['item']} ×{r['quantity']}.")
    if op == "item.transfer" and r.get("to_id") == player_id:
        return PlayerNotice("SISTEMA", f"Item recebido: {r['item']} ×{r['quantity']}.")
    if op == "item.transfer" and r.get("from_id") == player_id:
        return PlayerNotice("SISTEMA", f"Item entregue: {r['item']} ×{r['quantity']} → {r['to']}.")
    return None
