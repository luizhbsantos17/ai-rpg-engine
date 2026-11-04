"""Modelos do banco. Importar este pacote registra todas as tabelas em `Base.metadata`."""

from app.persistence.models.audit import AiRequest, DiceRollRecord
from app.persistence.models.base import Base
from app.persistence.models.canon import CanonFact
from app.persistence.models.knowledge import Disguise, Knowledge, NpcMemory
from app.persistence.models.memory import FTS_TABLE, Summary
from app.persistence.models.narrative import Event, Message, Turn
from app.persistence.models.platform import Campaign, CampaignIntro, User
from app.persistence.models.quests import Quest
from app.persistence.models.rules import Definition
from app.persistence.models.schedule import ScheduledEvent
from app.persistence.models.social import Relationship, RelationshipEvent
from app.persistence.models.world import Effect, Entity, EntityAttribute, EntitySkill, ItemInstance

__all__ = [
    "AiRequest", "Base", "Campaign", "CampaignIntro", "CanonFact", "Definition", "DiceRollRecord", "Disguise", "Effect",
    "Entity", "EntityAttribute", "EntitySkill", "Event", "ItemInstance", "Knowledge", "Message", "NpcMemory", "Quest", "Relationship", "RelationshipEvent", "ScheduledEvent", "Summary", "Turn", "User",
    "FTS_TABLE",
]
