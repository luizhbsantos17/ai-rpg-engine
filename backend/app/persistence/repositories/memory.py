"""Resumos e busca por texto no passado da campanha (memória narrativa e histórica)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.persistence.models import FTS_TABLE, Summary
from app.persistence.repositories.base import CampaignScopedRepository

MIN_WORD = 4
MAX_TERMS = 8
# Palavras comuns que não ajudam a achar nada.
STOPWORDS = frozenset("""
para pelo pela pelos pelas como mais muito muita esse essa isso este esta isto aquele aquela aquilo
qual quais quando onde quem porque então também ainda depois antes sobre entre até cada mesmo
mesma tudo todos todas nada algo alguém minha meus minhas seus suas dele dela deles delas
você vocês estou está estão estava tenho tinha fazer faço vou vamos olho pego digo pergunto
""".split())


@dataclass(frozen=True)
class MemoryHit:
    kind: str  # "narration" | "summary"
    turn_number: int
    snippet: str


class SummaryRepository(CampaignScopedRepository[Summary]):
    model = Summary

    def latest(self, limit: int) -> list[Summary]:
        query = self._select().order_by(Summary.to_turn.desc()).limit(limit)
        return list(reversed(list(self.session.scalars(query))))

    def last_covered_turn(self) -> int:
        latest = self.latest(1)
        return latest[0].to_turn if latest else 0


class MemorySearchRepository:
    """Índice FTS5 (busca por palavras) restrito à campanha. Específico do SQLite (D-033)."""

    def __init__(self, session: Session, campaign_id: str):
        if not campaign_id:
            raise ValueError("campaign_id é obrigatório para acessar dados de jogo.")
        self.session = session
        self.campaign_id = campaign_id

    def index(self, kind: str, ref_id: str, turn_number: int, content: str) -> None:
        self.session.execute(
            text(f"INSERT INTO {FTS_TABLE} (campaign_id, kind, ref_id, turn_number, content) "
                 "VALUES (:campaign_id, :kind, :ref_id, :turn_number, :content)"),
            {"campaign_id": self.campaign_id, "kind": kind, "ref_id": ref_id,
             "turn_number": turn_number, "content": content},
        )

    def search(self, query_text: str, limit: int = 4, before_turn: int | None = None) -> list[MemoryHit]:
        terms = search_terms(query_text)
        if not terms:
            return []
        match = " OR ".join(f'"{t}"' for t in terms)
        sql = (f"SELECT kind, turn_number, snippet({FTS_TABLE}, 4, '', '', ' … ', 24) "
               f"FROM {FTS_TABLE} WHERE {FTS_TABLE} MATCH :match AND campaign_id = :campaign_id")
        params = {"match": match, "campaign_id": self.campaign_id, "limit": limit}
        if before_turn is not None:
            sql += " AND turn_number < :before_turn"
            params["before_turn"] = before_turn
        rows = self.session.execute(text(sql + " ORDER BY rank LIMIT :limit"), params)
        return [MemoryHit(kind, int(turn), snippet) for kind, turn, snippet in rows]

    def delete_campaign(self) -> None:
        self.session.execute(text(f"DELETE FROM {FTS_TABLE} WHERE campaign_id = :c"), {"c": self.campaign_id})


def search_terms(query_text: str) -> list[str]:
    words = re.findall(r"[\wÀ-ÿ]+", query_text.lower())
    terms: list[str] = []
    for word in words:
        if len(word) >= MIN_WORD and word not in STOPWORDS and word not in terms:
            terms.append(word.replace('"', ""))
    return terms[:MAX_TERMS]
