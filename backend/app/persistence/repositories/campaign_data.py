"""Acesso a todos os dados de UMA campanha, numa mesma transação."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.persistence.repositories.narrative import (
    AiRequestRepository,
    EventRepository,
    MessageRepository,
    TurnRepository,
)


class CampaignData:
    """Agrupa os repositórios de uma campanha. Todos compartilham a sessão e o campaign_id."""

    def __init__(self, session: Session, campaign_id: str):
        self.campaign_id = campaign_id
        self.turns = TurnRepository(session, campaign_id)
        self.messages = MessageRepository(session, campaign_id)
        self.events = EventRepository(session, campaign_id)
        self.ai_requests = AiRequestRepository(session, campaign_id)
