"""Formato esperado dos dados enviados pelo frontend (validados com Pydantic)."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateCampaignRequest(StrictModel):
    title: ShortText
    premise: Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)] | None = None
    genre_tags: list[Tag] = Field(default_factory=list, max_length=12)


class DeleteCampaignRequest(StrictModel):
    confirm_title: str


class PlayTurnRequest(StrictModel):
    turn_id: str = Field(min_length=1, max_length=36)
    input: str = Field(max_length=4000)
