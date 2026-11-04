"""Usuário local da versão single-player.

Toda campanha tem dono (`owner_id`) desde já, para que hospedagem e multiplayer
futuros não exijam reestruturar os dados. Na v1, o dono é sempre este usuário.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.persistence.models import User
from app.persistence.repositories import UserRepository

LOCAL_USER_NAME = "Jogador local"


def ensure_local_user(session: Session) -> User:
    """Devolve o usuário local, criando-o na primeira execução."""
    users = UserRepository(session)
    return users.first() or users.create(LOCAL_USER_NAME)
