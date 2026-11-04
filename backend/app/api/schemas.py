"""Formato esperado dos dados enviados pelo frontend (validados com Pydantic)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateCampaignRequest(StrictModel):
    title: ShortText
    premise: Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)] | None = None
    genre_tags: list[Tag] = Field(default_factory=list, max_length=12)


class GenerateCampaignRequest(StrictModel):
    genres: list[Tag] = Field(default_factory=list, max_length=8)
    themes: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""
    draft_id: str | None = Field(default=None, max_length=36)  # gerar de novo este rascunho
    keep: list[Literal["title", "premise", "genre_tags"]] = Field(default_factory=list)


class UpdateDraftRequest(StrictModel):
    title: ShortText | None = None
    premise: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)] | None = None
    genre_tags: list[Tag] | None = Field(default=None, max_length=12)


class DeleteCampaignRequest(StrictModel):
    confirm_title: str


class PlayTurnRequest(StrictModel):
    turn_id: str = Field(min_length=1, max_length=36)
    input: str = Field(max_length=4000)
