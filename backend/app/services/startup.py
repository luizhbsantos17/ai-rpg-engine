"""Preparação feita uma vez quando o backend inicia."""

from __future__ import annotations

import logging

from flask import Flask, current_app

from app.admin.interpreter import AdminInterpreter
from app.admin.sessions import AdminSessions
from app.ai.orchestrator.turns import TurnOrchestrator
from app.auth.local_user import ensure_local_user
from app.config import Settings
from app.persistence.db import Database
from app.persistence.migrations import upgrade_to_head
from app.persistence.repositories.narrative import fail_interrupted_turns
from app.providers import AIProvider
from app.providers.registry import build_provider
from app.services.auto_backup import AutoBackupService
from app.services.campaign_settings import CampaignSettingsService
from app.services.campaigns import CampaignService
from app.services.generation import CampaignGenerationService
from app.images.providers import build_image_provider
from app.services.images import ImageService
from app.services.journal import JournalService
from app.services.known import KnownCharactersService
from app.services.sheet import CharacterSheetService
from app.services.summaries import SummaryService

logger = logging.getLogger(__name__)

EXTENSION_KEY = "rpg_engine"
INTERRUPTED_ON_SHUTDOWN = "O programa foi fechado durante esta jogada. Tente de novo."


class Services:
    """Objetos compartilhados pela aplicação inteira (guardados em `flask_app.extensions`)."""

    def __init__(self, settings: Settings, db: Database, provider: AIProvider, local_user_id: str):
        self.settings = settings
        self.db = db
        self.provider = provider
        self.local_user_id = local_user_id
        self.campaigns = CampaignService(db, settings.data_dir)
        self.sheets = CharacterSheetService(db)
        self.known = KnownCharactersService(db)
        self.journal = JournalService(db)
        self.campaign_settings = CampaignSettingsService(db, provider, settings)
        self.admin_sessions = AdminSessions(settings.admin_password)
        self.admin = AdminInterpreter(db, self.admin_sessions, settings.data_dir)
        self.images = ImageService(db, build_image_provider(settings), settings.data_dir)
        self.summaries = SummaryService(db, provider, settings)
        self.generation = CampaignGenerationService(db, provider, settings)
        self.auto_backup = AutoBackupService(db, settings)
        self.turns = TurnOrchestrator(db, provider, settings, on_turn_completed=self._after_turn)

    def _after_turn(self, campaign_id: str) -> None:
        """Tarefas depois de cada turno concluído: cópia automática e resumo da história."""
        try:
            self.auto_backup.after_turn(campaign_id)
        except Exception:  # falha na cópia (ex.: disco cheio) não impede o resumo nem estraga o turno
            logger.exception("Falha no snapshot automático da campanha %s", campaign_id)
        self.summaries.schedule(campaign_id)


def initialize_services(flask_app: Flask, settings: Settings) -> Services:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    upgrade_to_head(settings.database_url)

    db = Database(settings.database_url)
    with db.transaction() as session:
        local_user_id = ensure_local_user(session).id
        interrupted = fail_interrupted_turns(session, INTERRUPTED_ON_SHUTDOWN)
    if interrupted:
        logger.warning("%d jogada(s) interrompida(s) na última execução marcada(s) como falha.", interrupted)

    services = Services(settings, db, build_provider(settings), local_user_id)
    flask_app.extensions[EXTENSION_KEY] = services
    return services


def get_services() -> Services:
    return current_app.extensions[EXTENSION_KEY]
