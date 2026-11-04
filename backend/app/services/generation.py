"""Geração aleatória de campanhas (SPEC 3.1–3.3): gerar, gerar de novo mantendo partes, ajustar, começar.

A campanha gerada nasce como RASCUNHO no banco: os segredos do mestre ficam no servidor
(`campaign_intro.gm_secret`) e nunca vão para o navegador. Só a introdução visível é devolvida.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.ai.prompts.generator import build_generator_messages, pick_ingredients
from app.ai.schemas.generator import CampaignConcept
from app.ai.structured import request_structured
from app.config import Settings
from app.engine.dice import new_seed
from app.persistence.db import Database
from app.persistence.models import Event
from app.persistence.repositories import CampaignData, CampaignRepository
from app.providers import AIProvider, ProviderError
from app.providers.registry import generation_options, resolve_model
from app.services.errors import ConflictError, NotFoundError, UnavailableError
from app.services.serializers import campaign_to_dict

STATUS_DRAFT = "draft"
STATUS_ACTIVE = "active"
KEEPABLE = ("title", "premise", "genre_tags")
GENERATOR_TEMPERATURE = 1.0  # criatividade alta: o padrão é ser bem aleatório (SPEC 3.1)
GENERATOR_MAX_TOKENS = 900
GENERATOR_ROLE = "generator"


class CampaignGenerationService:
    def __init__(self, db: Database, provider: AIProvider, settings: Settings):
        self.db = db
        self.provider = provider
        self.settings = settings

    def generate(self, owner_id: str, genres: list[str], themes: str, draft_id: str | None = None,
                 keep: list[str] | None = None) -> dict[str, Any]:
        kept = self._kept_values(owner_id, draft_id, keep or []) if draft_id else {}
        seed = new_seed()
        ingredients = pick_ingredients(seed)
        messages = build_generator_messages(ingredients, genres, themes, kept)
        model = self._model()
        options = replace(generation_options(self.settings, model), temperature=GENERATOR_TEMPERATURE,
                          max_output_tokens=GENERATOR_MAX_TOKENS)
        try:
            result = request_structured(self.provider, messages, options, CampaignConcept, self.settings.ai_json_attempts)
        except ProviderError as exc:
            raise UnavailableError(exc.message) from None
        if not result.ok:
            raise UnavailableError("A IA não conseguiu gerar uma campanha válida. Tente de novo.")

        concept = result.value.model_copy(update=kept)  # o que o jogador quis manter prevalece
        secrets = {f"segredo_{n}": text for n, text in enumerate(concept.secrets, start=1)}
        secrets["inspiracao"] = ingredients
        secrets["semente_inspiracao"] = seed
        with self.db.transaction() as session:
            campaigns = CampaignRepository(session, owner_id)
            if draft_id:
                campaign = self._draft(campaigns, draft_id)
                campaign.title, campaign.genre_tags = concept.title, list(concept.genre_tags)
                campaign.intro.player_visible = {"premise": concept.premise}
                campaign.intro.gm_secret = secrets
                campaign.intro.version += 1
            else:
                campaign = campaigns.create(concept.title, concept.genre_tags, {"premise": concept.premise}, secrets)
                campaign.status = STATUS_DRAFT
            session.flush()
            data = CampaignData(session, campaign.id)
            data.events.record("campaign.generated", Event.SOURCE_AI,
                               {"ingredients": ingredients, "seed": seed, "kept": sorted(kept)})
            for attempt in result.attempts:
                data.ai_requests.record(role=GENERATOR_ROLE, provider=attempt.result.provider,
                                        model=attempt.result.model, tokens_in=attempt.result.tokens_in,
                                        tokens_out=attempt.result.tokens_out, duration_ms=attempt.result.duration_ms,
                                        error=attempt.error, request_messages=[m.to_dict() for m in messages])
            return {**campaign_to_dict(campaign), "secrets_count": len(concept.secrets)}

    def update_draft(self, owner_id: str, campaign_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        with self.db.transaction() as session:
            campaign = self._draft(CampaignRepository(session, owner_id), campaign_id)
            if "title" in changes:
                campaign.title = changes["title"]
            if "genre_tags" in changes:
                campaign.genre_tags = list(changes["genre_tags"])
            if "premise" in changes:
                campaign.intro.player_visible = {**campaign.intro.player_visible, "premise": changes["premise"]}
            session.flush()
            return campaign_to_dict(campaign)

    def start(self, owner_id: str, campaign_id: str) -> dict[str, Any]:
        with self.db.transaction() as session:
            campaign = self._draft(CampaignRepository(session, owner_id), campaign_id)
            campaign.status = STATUS_ACTIVE
            CampaignData(session, campaign.id).events.record("campaign.started", Event.SOURCE_SYSTEM, {})
            session.flush()
            return campaign_to_dict(campaign)

    def _kept_values(self, owner_id: str, draft_id: str, keep: list[str]) -> dict[str, Any]:
        with self.db.transaction() as session:
            campaign = self._draft(CampaignRepository(session, owner_id), draft_id)
            current = {"title": campaign.title, "genre_tags": list(campaign.genre_tags),
                       "premise": campaign.intro.player_visible.get("premise", "")}
        return {field: current[field] for field in keep if field in KEEPABLE and current[field]}

    @staticmethod
    def _draft(campaigns: CampaignRepository, campaign_id: str):
        campaign = campaigns.get(campaign_id)
        if campaign is None:
            raise NotFoundError("Campanha não encontrada.")
        if campaign.status != STATUS_DRAFT:
            raise ConflictError("Esta campanha já começou; não dá para gerar de novo.")
        return campaign

    def _model(self) -> str:
        try:
            return resolve_model(self.provider, self.settings.ai_model)
        except ProviderError as exc:
            raise UnavailableError(exc.message) from None
