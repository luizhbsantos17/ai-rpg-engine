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
        else:
            lines.append(_applied_line(outcome.op, r))
    return [line for line in lines if line]


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
    if op in ("definition.create", "definition.amend"):
        return ""  # regras não precisam ser narradas
    return f"{op} aplicado."


def player_notices(outcomes: list[OperationOutcome], player_id: str | None) -> list[PlayerNotice]:
    if player_id is None:
        return []
    notices: list[PlayerNotice] = []
    for outcome in outcomes:
        if outcome.status != "applied":
            continue
        notice = _player_notice(outcome.op, outcome.result, player_id)
        if notice:
            notices.append(notice)
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
    if not mine and op not in ("item.create", "item.transfer"):
        return None
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
        return PlayerNotice("SISTEMA", f"Habilidade usada: {r['skill']}" + (f" · {costs}" if costs else "") + ".")
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
