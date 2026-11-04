"""Snapshot automático a cada N turnos concluídos (DATABASE.md), mantendo só os mais recentes.

Snapshots manuais e os de segurança (antes de comandos destrutivos ou de excluir) nunca são apagados.
"""

from __future__ import annotations

import logging

from app.config import Settings
from app.persistence.db import Database
from app.persistence.repositories import CampaignData
from app.persistence.snapshots import AUTO_LABEL_PREFIX, export_campaign, prune_automatic, write_snapshot
from app.services.background import run_in_background

logger = logging.getLogger(__name__)

KEEP_AUTOMATIC = 5


class AutoBackupService:
    def __init__(self, db: Database, settings: Settings):
        self.db = db
        self.settings = settings

    def schedule(self, campaign_id: str) -> None:
        """Chamado ao fim de cada turno: a cópia de uma campanha grande leva ~1 s, então não segura o jogador."""
        run_in_background(self.settings, lambda: self.after_turn(campaign_id), "snapshot-automatico",
                          f"Falha no snapshot automático da campanha {campaign_id}.")

    def after_turn(self, campaign_id: str) -> str | None:
        every = self.settings.auto_snapshot_every
        if every <= 0:
            return None
        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            completed = data.turns.count_completed()
            if completed == 0 or completed % every != 0:
                return None
            snapshot = export_campaign(session, campaign_id)
        snapshot_id = write_snapshot(self.settings.data_dir, snapshot, f"{AUTO_LABEL_PREFIX}-turno-{completed}")
        prune_automatic(self.settings.data_dir, campaign_id, KEEP_AUTOMATIC)
        return snapshot_id
