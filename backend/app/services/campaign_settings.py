"""Configurações da campanha durante o jogo (SPEC 19 e 14).

- Experiência: muda como o jogo é apresentado/executado (modelo, criatividade, motor, simulação, avisos).
  Vazio = usa o padrão do programa (`.env`).
- Conteúdo: maturidade por categoria (0 evitar · 1 leve · 2 moderado · 3 intenso), sempre com as regras
  de segurança fixas da SPEC 14. O provedor pode limitar o que é possível (D-007).
- Regras e narrativa NÃO mudam aqui: são definições e fatos do mundo, versionados pelo motor
  (`definition.amend`, `canon.amend`). Esta tela só os lista.
Cada mudança grava uma versão nova (o histórico fica) e um evento `settings.changed`.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config import Settings
from app.persistence.db import Database
from app.persistence.models import CampaignSetting, Event
from app.persistence.repositories import CampaignData, CampaignRepository
from app.providers import AIProvider
from app.services.errors import NotFoundError

SIMULATION_MINUTES = {"off": 0, "low": 1440, "normal": 360, "high": 120}
LEVEL_NAMES = {0: "evitar", 1: "leve", 2: "moderado", 3: "intenso"}
CONTENT_CATEGORIES = {
    "violencia": "Violência", "horror": "Horror", "linguagem": "Linguagem pesada",
    "psicologico": "Temas psicológicos", "romance": "Romance", "intimidade": "Intimidade",
    "sexual": "Conteúdo sexual adulto", "perturbador": "Temas perturbadores", "manipulacao": "Manipulação",
    "abuso_de_poder": "Abuso de poder", "conflito_moral": "Conflitos morais", "trauma": "Situações traumáticas",
}
SAFETY_RULES = ("Conteúdo sexual explícito só entre personagens adultos. Violência sexual pode existir como tema "
                "narrativo, com consequências, mas nunca erotizada.")


class ExperienceSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ai_model: str | None = Field(default=None, max_length=200)
    creativity: float | None = Field(default=None, ge=0, le=2)
    mechanics: bool | None = None
    simulation: Literal["off", "low", "normal", "high"] | None = None
    summary_every: int | None = Field(default=None, ge=0, le=100)
    show_dice: bool = True  # mostrar os avisos [TESTE] com os números
    system_window: bool = True  # mostrar avisos de "sistema" (nem todo mundo tem janela de status, SPEC 12.2)


class ContentSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intensity: int = Field(default=2, ge=0, le=3)
    categories: dict[Literal[tuple(CONTENT_CATEGORIES)], int] = Field(default_factory=dict)  # type: ignore[valid-type]

    def level(self, category: str) -> int:
        return min(3, max(0, self.categories.get(category, self.intensity)))


def load_experience(data: CampaignData) -> ExperienceSettings:
    record = data.settings.current(CampaignSetting.KIND_EXPERIENCE)
    return ExperienceSettings.model_validate(record.data) if record else ExperienceSettings()


def load_content(data: CampaignData) -> ContentSettings:
    record = data.settings.current(CampaignSetting.KIND_CONTENT)
    return ContentSettings.model_validate(record.data) if record else ContentSettings()


def effective_settings(base: Settings, experience: ExperienceSettings) -> Settings:
    """Configuração do programa com as escolhas da campanha por cima."""
    changes: dict[str, Any] = {}
    if experience.ai_model:
        changes["ai_model"] = experience.ai_model
    if experience.creativity is not None:
        changes["ai_temperature"] = experience.creativity
    if experience.mechanics is not None:
        changes["ai_mechanics"] = experience.mechanics
    if experience.simulation is not None:
        changes["ai_simulation_minutes"] = SIMULATION_MINUTES[experience.simulation]
    if experience.summary_every is not None:
        changes["ai_summary_every"] = experience.summary_every
    return replace(base, **changes) if changes else base


def content_guidelines(content: ContentSettings) -> str:
    """Texto para os prompts da IA: limites desta campanha + regras fixas de segurança."""
    levels = "; ".join(f"{name}: {LEVEL_NAMES[content.level(key)]}" for key, name in CONTENT_CATEGORIES.items())
    return f"Limites de conteúdo desta campanha (respeite): {levels}. Sempre: {SAFETY_RULES}"


class CampaignSettingsService:
    def __init__(self, db: Database, provider: AIProvider, settings: Settings):
        self.db = db
        self.provider = provider
        self.settings = settings

    def get(self, owner_id: str, campaign_id: str) -> dict[str, Any]:
        with self.db.transaction() as session:
            data = self._data(session, owner_id, campaign_id)
            return self._view(data)

    def update(self, owner_id: str, campaign_id: str, experience: dict | None, content: dict | None) -> dict[str, Any]:
        new_experience = ExperienceSettings.model_validate(experience) if experience is not None else None
        new_content = ContentSettings.model_validate(content) if content is not None else None
        with self.db.transaction() as session:
            data = self._data(session, owner_id, campaign_id)
            old_experience = load_experience(data)
            warnings = []
            if new_experience is not None:
                warnings += self._experience_warnings(old_experience, new_experience)
                data.settings.save(CampaignSetting.KIND_EXPERIENCE, new_experience.model_dump())
            if new_content is not None:
                if new_content.level("sexual") > 0 and self.provider.content_note:
                    warnings.append(self.provider.content_note)
                data.settings.save(CampaignSetting.KIND_CONTENT, new_content.model_dump())
            data.events.record("settings.changed", Event.SOURCE_SYSTEM, {
                "experience": new_experience.model_dump() if new_experience else None,
                "content": new_content.model_dump() if new_content else None,
            }, None, data.campaign().world_clock)
            return {**self._view(data), "warnings": warnings}

    @staticmethod
    def _experience_warnings(old: ExperienceSettings, new: ExperienceSettings) -> list[str]:
        warnings = []
        if old.mechanics is not False and new.mechanics is False:
            warnings.append("Sem o motor de regras, a ficha, os testes e as missões deixam de ser atualizados "
                            "pela IA a partir de agora. Nada do que já aconteceu é desfeito.")
        if old.mechanics is False and new.mechanics is not False:
            warnings.append("O motor de regras volta a valer a partir da próxima jogada; o passado não é recalculado.")
        if new.simulation == "off" and old.simulation != "off":
            warnings.append("Com a simulação desligada, personagens longe do protagonista não agem quando o tempo passa.")
        return warnings

    def _view(self, data: CampaignData) -> dict[str, Any]:
        experience = load_experience(data)
        content = load_content(data)
        return {
            "experience": experience.model_dump(),
            "content": content.model_dump(),
            "defaults": {"ai_model": self.settings.ai_model, "creativity": self.settings.ai_temperature,
                         "mechanics": self.settings.ai_mechanics, "summary_every": self.settings.ai_summary_every},
            "content_categories": CONTENT_CATEGORIES,
            "provider": {"name": self.provider.name, "content_note": self.provider.content_note},
            "rules": [{"kind": d.kind, "key": d.key, "name": d.data.get("name", d.key), "version": d.version}
                      for d in data.definitions.list_current()],
            "versions": {"experience": len(data.settings.history(CampaignSetting.KIND_EXPERIENCE)),
                         "content": len(data.settings.history(CampaignSetting.KIND_CONTENT))},
        }

    @staticmethod
    def _data(session, owner_id: str, campaign_id: str) -> CampaignData:
        if CampaignRepository(session, owner_id).get(campaign_id) is None:
            raise NotFoundError("Campanha não encontrada.")
        return CampaignData(session, campaign_id)
