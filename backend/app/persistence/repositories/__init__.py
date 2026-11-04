"""Repositórios: a única forma de ler e gravar dados no banco.

Regra inviolável: repositórios de dados de jogo exigem o `campaign_id` na criação e
aplicam esse filtro em toda consulta. Não há como consultar "todas as campanhas" por eles.
"""

from app.persistence.repositories.base import CampaignMismatchError
from app.persistence.repositories.campaign_data import CampaignData
from app.persistence.repositories.campaigns import CampaignRepository
from app.persistence.repositories.users import UserRepository

__all__ = ["CampaignData", "CampaignMismatchError", "CampaignRepository", "UserRepository"]
