"""Acesso a todos os dados de UMA campanha, numa mesma transação."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.persistence.repositories.narrative import (
    AiRequestRepository,
    EventRepository,
    MessageRepository,
    TurnRepository,
)
from app.persistence.models import Campaign
from app.persistence.repositories.world import (
    AttributeRepository,
    CanonRepository,
    DefinitionRepository,
    DiceRollRepository,
    EffectRepository,
    EntityRepository,
    ItemRepository,
    KnowledgeRepository,
    NpcMemoryRepository,
    RelationshipRepository,
    ScheduledEventRepository,
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
        self.canon = CanonRepository(session, campaign_id)
        self.schedule = ScheduledEventRepository(session, campaign_id)
        self.effects = EffectRepository(session, campaign_id)
        self.relationships = RelationshipRepository(session, campaign_id)
        self.knowledge = KnowledgeRepository(session, campaign_id)
        self.memories = NpcMemoryRepository(session, campaign_id)

    def campaign(self) -> Campaign:
        """A própria campanha (para o relógio do mundo). Permissão de dono já foi conferida antes."""
        campaign = self.session.get(Campaign, self.campaign_id)
        if campaign is None:
            raise LookupError("Campanha não existe mais.")
        return campaign

    def savepoint(self):
        """Transação interna: se a operação falhar, desfaz só ela (o resto do turno continua)."""
        return self.session.begin_nested()
