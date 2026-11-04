"""Snapshot automático a cada N turnos concluídos (DATABASE.md), mantendo só os mais recentes.

Snapshots manuais e os de segurança (antes de comandos destrutivos ou de excluir) nunca são apagados.
"""

from __future__ import annotations

import logging

from app.config import Settings
from app.persistence.db import Database
from app.persistence.models import Turn
from app.persistence.repositories import CampaignData
from app.persistence.snapshots import AUTO_LABEL_PREFIX, export_campaign, prune_automatic, write_snapshot

logger = logging.getLogger(__name__)

KEEP_AUTOMATIC = 5


class AutoBackupService:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings

    def after_turn(self, campaign_id: str) -> str | None:
        every = self.settings.auto_snapshot_every
        if every <= 0:
            return None
        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            completed = sum(1 for t in data.turns.list_ordered() if t.status == Turn.STATUS_COMPLETED)
            if completed == 0 or completed % every != 0:
                return None
            snapshot = export_campaign(session, campaign_id)
        snapshot_id = write_snapshot(self.settings.data_dir, snapshot, f"{AUTO_LABEL_PREFIX}-turno-{completed}")
        prune_automatic(self.settings.data_dir, campaign_id, KEEP_AUTOMATIC)
        return snapshot_id
