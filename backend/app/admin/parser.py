"""Leitura da sintaxe dos comandos (docs/ADMIN_COMMANDS.md).

    /<grupo> <verbo> [argumentos] [--opção valor]

- Textos com espaço vão entre aspas: npc "Ana Clara"
- Opções começam com --: --qty 3, --confirm AB12, --last 20
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field


class CommandSyntaxError(ValueError):
    """Comando mal escrito (aspas abertas, opção sem valor...)."""


@dataclass(frozen=True)
class Command:
    group: str  # "admin" | "debug"
    verb: str
    args: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)
    raw: str = ""

    @property
    def name(self) -> str:
        return f"/{self.group} {self.verb}"


def parse_command(text: str) -> Command:
    raw = (text or "").strip()
    try:
        tokens = shlex.split(raw, posix=True)
    except ValueError as exc:
        raise CommandSyntaxError(f"Comando mal escrito: {exc}.") from None
    if not tokens or tokens[0] not in ("/admin", "/debug"):
        raise CommandSyntaxError("Comandos começam com /admin ou /debug.")
    group = tokens[0][1:]
    if len(tokens) == 1:
        return Command(group, "help", raw=raw)

    verb, rest = tokens[1].lower(), tokens[2:]
    args: list[str] = []
    options: dict[str, str] = {}
    index = 0
    while index < len(rest):
        token = rest[index]
        if token.startswith("--") and len(token) > 2:
            if index + 1 >= len(rest) or rest[index + 1].startswith("--"):
                raise CommandSyntaxError(f"A opção {token} precisa de um valor.")
            options[token[2:].lower()] = rest[index + 1]
            index += 2
        else:
            args.append(token)
            index += 1
    return Command(group, verb, args, options, raw)
