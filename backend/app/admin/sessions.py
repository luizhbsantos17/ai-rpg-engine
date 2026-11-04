"""Sessões administrativas: senha do .env (ADMIN_PASSWORD) → código temporário (SPEC 16.3).

Vale mesmo rodando no próprio computador, e prepara a futura hospedagem com autenticação.
Os códigos ficam só na memória do servidor: reiniciar o programa encerra todas as sessões.
"""

from __future__ import annotations

import hmac
import secrets
import threading
import time
from dataclasses import dataclass, field

SESSION_SECONDS = 30 * 60
CONFIRM_SECONDS = 120


class AdminAccessError(Exception):
    """Sem sessão válida, senha errada ou modo administrador desligado."""


@dataclass
class _Session:
    expires_at: float
    pending: dict[str, tuple[str, float]] = field(default_factory=dict)  # código -> (comando, validade)


class AdminSessions:
    def __init__(self, password: str | None, clock=time.monotonic):
        self._password = password
        self._clock = clock
        self._sessions: dict[str, _Session] = {}
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return bool(self._password)

    def login(self, password: str) -> str:
        if not self.enabled:
            raise AdminAccessError("Modo administrador desligado: defina ADMIN_PASSWORD no arquivo .env.")
        if not hmac.compare_digest(str(password).encode("utf-8"), self._password.encode("utf-8")):
            raise AdminAccessError("Senha de administrador incorreta.")
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = _Session(self._clock() + SESSION_SECONDS)
        return token

    def check(self, token: str | None) -> None:
        session = self._session(token)
        session.expires_at = self._clock() + SESSION_SECONDS  # uso renova a sessão

    def logout(self, token: str | None) -> None:
        with self._lock:
            self._sessions.pop(token or "", None)

    def ask_confirmation(self, token: str, command_text: str) -> str:
        code = secrets.token_hex(2).upper()
        self._session(token).pending[code] = (command_text, self._clock() + CONFIRM_SECONDS)
        return code

    def confirm(self, token: str, code: str, command_text: str) -> bool:
        session = self._session(token)
        entry = session.pending.pop(code.upper(), None)
        return entry is not None and entry[0] == command_text and entry[1] >= self._clock()

    def _session(self, token: str | None) -> _Session:
        with self._lock:
            session = self._sessions.get(token or "")
            if session is None or session.expires_at < self._clock():
                self._sessions.pop(token or "", None)
                raise AdminAccessError("Sessão de administrador ausente ou expirada. Entre de novo com a senha.")
            return session
