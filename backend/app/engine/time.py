"""Tempo do mundo: contado em minutos desde o início da campanha (campaigns.world_clock).

O relógio só anda por `time.advance` (SPEC 10.3): fechar o programa não avança nada.
Durações aceitam número de minutos ou texto: "30m", "4h", "2d", "1d12h".
"""

from __future__ import annotations

import re

from app.engine.errors import OperationRejected

MINUTES = {"m": 1, "h": 60, "d": 1440, "s": 10080}  # s = semana
MAX_ADVANCE_MINUTES = 100 * 365 * 1440  # um avanço de até 100 anos por operação
_PART = re.compile(r"(\d+)\s*([mhds])")


def parse_duration(raw: int | str) -> int:
    if isinstance(raw, bool):
        raise OperationRejected("Duração inválida.")
    if isinstance(raw, int):
        minutes = raw
    else:
        text = str(raw).strip().lower().replace(" ", "")
        if text.isdigit():
            minutes = int(text)
        else:
            parts = _PART.findall(text)
            if not parts or "".join(n + u for n, u in parts) != text:
                raise OperationRejected(f"Duração '{raw}' inválida. Use minutos ou algo como 30m, 4h, 2d, 1d12h.")
            minutes = sum(int(n) * MINUTES[u] for n, u in parts)
    if not 1 <= minutes <= MAX_ADVANCE_MINUTES:
        raise OperationRejected("A duração precisa ser de pelo menos 1 minuto (e no máximo 100 anos).")
    return minutes


def format_world_time(minutes: int) -> str:
    day, rest = divmod(max(0, minutes), 1440)
    hour, minute = divmod(rest, 60)
    return f"dia {day + 1}, {hour:02d}:{minute:02d}"


def format_duration(minutes: int) -> str:
    days, rest = divmod(minutes, 1440)
    hours, mins = divmod(rest, 60)
    parts = [f"{days}d" if days else "", f"{hours}h" if hours else "", f"{mins}min" if mins else ""]
    return " ".join(p for p in parts if p) or "0min"
