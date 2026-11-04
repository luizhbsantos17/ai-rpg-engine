"""Usuário local da versão single-player.

Toda campanha tem dono (`owner_id`) desde já, para que hospedagem e multiplayer
futuros não exijam reestruturar os dados. Na v1, o dono é sempre este usuário.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import User

LOCAL_USER_NAME = "Jogador local"


def ensure_local_user(session: Session) -> User:
    """Devolve o usuário local, criando-o na primeira execução."""
    user = session.scalars(select(User).order_by(User.created_at).limit(1)).first()
    if user is None:
        user = User(name=LOCAL_USER_NAME)
        session.add(user)
        session.flush()
    return user
