"""Tarefas depois do turno que não devem atrasar a resposta ao jogador (resumo, cópia automática)."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from app.config import Settings

logger = logging.getLogger(__name__)


def run_in_background(settings: Settings, task: Callable[[], object], name: str, failure_message: str) -> None:
    """Roda `task` numa linha de execução separada. Nos testes roda na hora, para o resultado ser previsível."""
    if settings.app_env == "test":
        task()
        return
    threading.Thread(target=_safe, args=(task, failure_message), daemon=True, name=name).start()


def _safe(task: Callable[[], object], failure_message: str) -> None:
    try:
        task()
    except Exception:
        logger.exception(failure_message)
