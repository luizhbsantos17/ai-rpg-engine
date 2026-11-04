"""Acesso a todos os dados de UMA campanha, numa mesma transação."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.persistence.repositories.narrative import (
    AiRequestRepository,
    EventRepository,
    MessageRepository,
    TurnRepository,
)
from app.persistence.repositories.world import (
    AttributeRepository,
    DefinitionRepository,
    DiceRollRepository,
    EntityRepository,
    ItemRepository,
    SkillRepository,
)


class CampaignData:
    """Agrupa os repositórios de uma campanha. Todos compartilham a sessão e o campaign_id."""

    def __init__(self, session: Session, campaign_id: str):
        self.session = session
        self.campaign_id = campaign_id
        self.turns = TurnRepository(session, campaign_id)
        self.messages = MessageRepository(session, campaign_id)
        self.events = EventRepository(session, campaign_id)
        self.ai_requests = AiRequestRepository(session, campaign_id)
        self.definitions = DefinitionRepository(session, campaign_id)
        self.entities = EntityRepository(session, campaign_id)
        self.attributes = AttributeRepository(session, campaign_id)
        self.skills = SkillRepository(session, campaign_id)
        self.items = ItemRepository(session, campaign_id)
        self.dice_rolls = DiceRollRepository(session, campaign_id)

    def savepoint(self):
        """Transação interna: se a operação falhar, desfaz só ela (o resto do turno continua)."""
        return self.session.begin_nested()
