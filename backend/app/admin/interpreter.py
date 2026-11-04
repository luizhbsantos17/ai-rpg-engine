"""Interpretador de comandos /admin e /debug (SPEC 16).

Fluxo: sessão válida → leitura da sintaxe → comando do catálogo → (destrutivo? pede código) →
executa numa transação → registra em admin_audit. Alterações passam pelo pipeline de operações
do motor com origem "admin" (mesma validação e o mesmo log de eventos da IA).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.admin.commands import COMMANDS, AdminContext, AdminError
from app.admin.parser import Command, CommandSyntaxError, parse_command
from app.admin.sessions import AdminSessions
from app.admin.targets import AdminTargetError
from app.persistence.db import Database
from app.persistence.models import AdminAudit
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.errors import NotFoundError


@dataclass
class AdminResult:
    ok: bool
    command: str
    lines: list[str] = field(default_factory=list)
    confirmation_code: str | None = None
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "command": self.command, "lines": self.lines,
                "confirmation_code": self.confirmation_code, "data": self.data}


def canonical(command: Command) -> str:
    """Texto do comando sem --confirm (o código confirma exatamente o mesmo comando)."""
    options = " ".join(f"--{k} {v}" for k, v in sorted(command.options.items()) if k != "confirm")
    return " ".join([command.name, *command.args, options]).strip()


class AdminInterpreter:
    def __init__(self, db: Database, sessions: AdminSessions):
        self.db = db
        self.sessions = sessions

    def execute(self, owner_id: str, campaign_id: str, token: str | None, text: str) -> AdminResult:
        self.sessions.check(token)  # AdminAccessError se não houver sessão
        try:
            command = parse_command(text)
        except CommandSyntaxError as exc:
            return AdminResult(False, text.strip(), [str(exc)])
        spec = COMMANDS.get((command.group, command.verb))
        if spec is None:
            return AdminResult(False, command.name, [f"Comando desconhecido: {command.name}. Use /admin help."])

        if spec.destructive:
            code = command.options.get("confirm")
            if not code or not self.sessions.confirm(token, code, canonical(command)):
                new_code = self.sessions.ask_confirmation(token, canonical(command))
                return AdminResult(False, command.name, [
                    f"{command.name} é destrutivo: {spec.description}",
                    f"Para confirmar, repita o comando com --confirm {new_code} (vale por 2 minutos).",
                ], confirmation_code=new_code)

        try:
            # Erro no meio do comando sai do "with": a transação inteira é desfeita (nada pela metade).
            with self.db.transaction() as session:
                if CampaignRepository(session, owner_id).get(campaign_id) is None:
                    raise NotFoundError("Campanha não encontrada.")
                data = CampaignData(session, campaign_id)
                outcome = spec.handler(AdminContext(data=data, command=command))
                if spec.audited:
                    data.admin_audit.add(AdminAudit(
                        command=canonical(command), result="\n".join(outcome.lines)[:4000],
                        changed_state=outcome.changed, undo_operations=outcome.undo,
                    ))
        except (AdminError, AdminTargetError) as exc:
            return AdminResult(False, command.name, [str(exc)])
        return AdminResult(True, command.name, outcome.lines, data=outcome.data)
