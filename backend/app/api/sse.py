"""Formatação de Server-Sent Events (SSE): texto enviado aos poucos ao navegador.

Cada evento é: "event: <nome>\\ndata: <json>\\n\\n".
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import asdict

from app.ai.orchestrator.events import NarrationDelta, TurnCompleted, TurnEvent, TurnFailed, TurnStarted

EVENT_NAMES = {
    TurnStarted: "turn",
    NarrationDelta: "delta",
    TurnCompleted: "done",
    TurnFailed: "error",
}


def format_sse(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def turn_events_to_sse(events: Iterator[TurnEvent]) -> Iterator[str]:
    try:
        for event in events:
            yield format_sse(EVENT_NAMES[type(event)], asdict(event))
    finally:
        # Se o navegador desconectar, fecha o turno na hora (ele registra a interrupção).
        events.close()
