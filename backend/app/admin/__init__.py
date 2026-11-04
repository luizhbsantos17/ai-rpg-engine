"""Modo administrador e debug (SPEC 16): interpretador de comandos próprio, separado da IA.

Só textos que COMEÇAM com /admin ou /debug são comandos. Eles nunca são enviados à IA,
nunca viram fala do jogador e exigem uma sessão administrativa (senha do .env).
"""

ADMIN_PREFIXES = ("/admin", "/debug")


def is_admin_command(text: str) -> bool:
    stripped = (text or "").lstrip()
    return any(stripped == p or stripped.startswith(p + " ") for p in ADMIN_PREFIXES)
