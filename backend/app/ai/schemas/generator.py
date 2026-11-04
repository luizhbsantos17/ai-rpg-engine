"""Resposta da IA geradora de campanhas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CampaignConcept(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=200)
    genre_tags: list[str] = Field(default_factory=list, max_length=8)
    premise: str = Field(min_length=10, max_length=4000)
    secrets: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("genre_tags", "secrets")
    @classmethod
    def _clean(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            value = str(value).strip()
            if value and value not in cleaned:
                cleaned.append(value[:300])
        return cleaned

    @field_validator("title", "premise")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()
