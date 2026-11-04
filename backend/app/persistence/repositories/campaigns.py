"""Repositório de campanhas, sempre limitado ao dono (permissões, SPEC 18.4)."""

from __future__ import annotations

import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import Campaign, CampaignIntro
from app.persistence.types import utc_now

RNG_SEED_BITS = 63  # cabe em um inteiro de 64 bits com sinal (SQLite e PostgreSQL)


class CampaignRepository:
    def __init__(self, session: Session, owner_id: str):
        if not owner_id:
            raise ValueError("owner_id é obrigatório para acessar campanhas.")
        self.session = session
        self.owner_id = owner_id

    def _select(self):
        return select(Campaign).where(Campaign.owner_id == self.owner_id)

    def create(
        self,
        title: str,
        genre_tags: list[str] | None = None,
        player_visible: dict[str, Any] | None = None,
        gm_secret: dict[str, Any] | None = None,
        rng_seed: int | None = None,
    ) -> Campaign:
        campaign = Campaign(
            owner_id=self.owner_id,
            title=title,
            genre_tags=list(genre_tags or []),
            rng_seed=rng_seed if rng_seed is not None else secrets.randbits(RNG_SEED_BITS),
        )
        campaign.intro = CampaignIntro(player_visible=dict(player_visible or {}), gm_secret=dict(gm_secret or {}))
        self.session.add(campaign)
        self.session.flush()
        return campaign

    def get(self, campaign_id: str) -> Campaign | None:
        return self.session.scalars(self._select().where(Campaign.id == campaign_id)).first()

    def list_recent(self) -> list[Campaign]:
        return list(self.session.scalars(self._select().order_by(Campaign.updated_at.desc())))

    def touch(self, campaign: Campaign) -> None:
        """Marca a campanha como modificada agora (ordena a lista por 'jogada por último')."""
        campaign.updated_at = utc_now()
        self.session.flush()

    def delete(self, campaign: Campaign) -> None:
        if campaign.owner_id != self.owner_id:
            raise PermissionError("Campanha de outro usuário.")
        self.session.delete(campaign)
        self.session.flush()
