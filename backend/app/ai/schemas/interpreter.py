"""Resposta da IA intérprete.

`operations` fica como lista de objetos livres de propósito: cada operação é validada
SOZINHA pelo pipeline do motor. Uma operação malformada é recusada sem invalidar as outras.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InterpreterOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intent: str = Field(default="", max_length=500, description="O que o jogador tenta fazer, em poucas palavras.")
    operations: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
