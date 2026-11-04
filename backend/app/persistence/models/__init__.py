"""Modelos do banco. Importar este pacote registra todas as tabelas em `Base.metadata`."""

from app.persistence.models.audit import AiRequest
from app.persistence.models.base import Base
from app.persistence.models.narrative import Event, Message, Turn
from app.persistence.models.platform import Campaign, CampaignIntro, User

__all__ = ["AiRequest", "Base", "Campaign", "CampaignIntro", "Event", "Message", "Turn", "User"]
