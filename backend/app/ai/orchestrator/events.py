"""O que o orquestrador informa enquanto um turno acontece (vira SSE na API)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TurnStarted:
    turn: dict[str, Any]
    player_message: dict[str, Any]
    replay: bool = False  # True: turno já concluído antes; nada foi gerado de novo


@dataclass(frozen=True)
class MechanicsApplied:
    """O motor aplicou as operações do turno; `messages` são os avisos [SISTEMA]/[TESTE] do jogador."""

    messages: list[dict[str, Any]]
    intent: str | None = None


@dataclass(frozen=True)
class NarrationDelta:
    text: str


@dataclass(frozen=True)
class TurnCompleted:
    turn: dict[str, Any]
    narration_message: dict[str, Any]


@dataclass(frozen=True)
class TurnFailed:
    turn: dict[str, Any]
    message: str
    retryable: bool


TurnEvent = TurnStarted | MechanicsApplied | NarrationDelta | TurnCompleted | TurnFailed
