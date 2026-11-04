"""Casos de uso de campanhas: criar, listar, abrir, histórico e excluir."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.persistence.db import Database
from app.persistence.models import Event
from app.persistence.repositories import CampaignData, CampaignRepository
from app.persistence.snapshots import SnapshotError, export_campaign, restore_campaign, work_dir_for, write_snapshot
from app.services.errors import InvalidInputError, NotFoundError
from app.services.serializers import campaign_to_dict, message_to_dict, turn_to_dict


class CampaignService:
    def __init__(self, db: Database, data_dir: Path | None = None):
        self.db = db
        self.data_dir = data_dir  # onde ficam as cópias de segurança (data/backups)

    def export(self, owner_id: str, campaign_id: str) -> dict[str, Any]:
        """Arquivo com a campanha inteira (para guardar, mover de computador ou restaurar)."""
        with self.db.transaction() as session:
            self._require(CampaignRepository(session, owner_id), campaign_id)
            return export_campaign(session, campaign_id)

    def import_(self, owner_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
        try:
            with self.db.transaction() as session:
                campaign_id = restore_campaign(session, snapshot, owner_id, replace_existing=False,
                                               work_dir=work_dir_for(self.data_dir))
        except SnapshotError as exc:
            raise InvalidInputError(str(exc)) from None
        except (KeyError, TypeError, ValueError):
            raise InvalidInputError("Arquivo de campanha inválido ou incompleto.") from None
        with self.db.transaction() as session:
            return campaign_to_dict(self._require(CampaignRepository(session, owner_id), campaign_id))

    def list(self, owner_id: str) -> list[dict[str, Any]]:
        with self.db.transaction() as session:
            return [campaign_to_dict(c) for c in CampaignRepository(session, owner_id).list_recent()]

    def create(self, owner_id: str, title: str, premise: str | None, genre_tags: list[str]) -> dict[str, Any]:
        player_visible = {"premise": premise} if premise else {}
        with self.db.transaction() as session:
            campaign = CampaignRepository(session, owner_id).create(title, genre_tags, player_visible)
            CampaignData(session, campaign.id).events.record(
                "campaign.created", Event.SOURCE_SYSTEM, {"title": title, "rng_seed": campaign.rng_seed}
            )
            return campaign_to_dict(campaign)

    def get(self, owner_id: str, campaign_id: str) -> dict[str, Any]:
        with self.db.transaction() as session:
            return campaign_to_dict(self._require(CampaignRepository(session, owner_id), campaign_id))

    def history(self, owner_id: str, campaign_id: str, after_seq: int = 0) -> dict[str, Any]:
        """Tudo o que o chat precisa para retomar a campanha exatamente de onde parou."""
        with self.db.transaction() as session:
            campaign = self._require(CampaignRepository(session, owner_id), campaign_id)
            data = CampaignData(session, campaign.id)
            return {
                "campaign": campaign_to_dict(campaign),
                "turns": [turn_to_dict(t) for t in data.turns.list_ordered()],
                "messages": [message_to_dict(m) for m in data.messages.list_ordered(after_seq=after_seq)],
            }

    def delete(self, owner_id: str, campaign_id: str, confirm_title: str | None) -> None:
        """Exclusão definitiva. Exige digitar o título exato como confirmação."""
        with self.db.transaction() as session:
            campaigns = CampaignRepository(session, owner_id)
            campaign = self._require(campaigns, campaign_id)
            if (confirm_title or "").strip() != campaign.title:
                raise InvalidInputError("Para excluir, confirme digitando o título exato da campanha.")
            if self.data_dir is not None:  # cópia de segurança antes de apagar (pode ser importada depois)
                write_snapshot(self.data_dir, export_campaign(session, campaign.id), "antes-de-excluir")
            CampaignData(session, campaign.id).memory_search.delete_campaign()  # índice FTS não tem cascata
            campaigns.delete(campaign)

    @staticmethod
    def _require(campaigns: CampaignRepository, campaign_id: str):
        campaign = campaigns.get(campaign_id)
        if campaign is None:
            raise NotFoundError("Campanha não encontrada.")
        return campaign
