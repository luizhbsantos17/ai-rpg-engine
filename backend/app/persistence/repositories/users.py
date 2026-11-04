"""Repositório de usuários (tabela da plataforma, não pertence a uma campanha)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def first(self) -> User | None:
        return self.session.scalars(select(User).order_by(User.created_at).limit(1)).first()

    def get(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def create(self, name: str) -> User:
        user = User(name=name)
        self.session.add(user)
        self.session.flush()
        return user
