"""Imagens de entidades (retratos, criaturas, locais...), opcionais (SPEC 13).

- Sem provedor configurado, responde "desligado" e o resto do jogo não muda.
- O pedido (prompt) usa só o que é visível da entidade: nome, tipo, descrição e gêneros da campanha.
- Mesmo pedido na mesma campanha devolve a imagem já gerada (sem custo repetido).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from app.images.providers import ImageProvider, ImageUnavailableError
from app.persistence.db import Database
from app.persistence.models import GeneratedImageRecord
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.errors import NotFoundError, UnavailableError

EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


class ImageService:
    def __init__(self, db: Database, provider: ImageProvider, data_dir: Path):
        self.db = db
        self.provider = provider
        self.data_dir = data_dir

    def status(self) -> dict[str, Any]:
        return {"enabled": self.provider.configured, "provider": self.provider.name, "paid": self.provider.is_paid}

    def generate_for_entity(self, owner_id: str, campaign_id: str, entity_id: str) -> dict[str, Any]:
        with self.db.transaction() as session:
            campaign = CampaignRepository(session, owner_id).get(campaign_id)
            if campaign is None:
                raise NotFoundError("Campanha não encontrada.")
            data = CampaignData(session, campaign_id)
            entity = data.entities.get(entity_id)
            if entity is None:
                raise NotFoundError("Entidade não encontrada nesta campanha.")
            prompt = build_prompt(entity.name, entity.kind, str(entity.data.get("description", "")),
                                  list(campaign.genre_tags))
            prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            existing = data.images.by_hash(prompt_hash)
            if existing is not None:
                return {**_to_dict(existing), "reused": True}
        try:
            image = self.provider.generate(prompt)  # fora de transação (pode demorar)
        except ImageUnavailableError as exc:
            raise UnavailableError(str(exc)) from None
        with self.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            record = data.images.add(GeneratedImageRecord(
                entity_id=entity_id, prompt=prompt, prompt_hash=prompt_hash,
                file_name="pendente", mime_type=image.mime_type, provider=image.provider,
            ))
            record.file_name = f"{record.id}.{EXTENSIONS.get(image.mime_type, 'bin')}"
            folder = self.data_dir / "images" / campaign_id
            folder.mkdir(parents=True, exist_ok=True)
            (folder / record.file_name).write_bytes(image.content)
            session.flush()
            return {**_to_dict(record), "reused": False}

    def file_for(self, owner_id: str, campaign_id: str, image_id: str) -> tuple[Path, str]:
        with self.db.transaction() as session:
            if CampaignRepository(session, owner_id).get(campaign_id) is None:
                raise NotFoundError("Campanha não encontrada.")
            record = CampaignData(session, campaign_id).images.get(image_id)
            if record is None:
                raise NotFoundError("Imagem não encontrada.")
            return self.data_dir / "images" / campaign_id / record.file_name, record.mime_type


def build_prompt(name: str, kind: str, description: str, genres: list[str]) -> str:
    style = f"estilo de ilustração de light novel, {', '.join(genres)}" if genres else "estilo de ilustração de light novel"
    detail = f": {description[:400]}" if description else ""
    return f"{kind} chamado {name}{detail}. {style}."


def _to_dict(record: GeneratedImageRecord) -> dict[str, Any]:
    return {"id": record.id, "entity_id": record.entity_id, "provider": record.provider,
            "url": f"/api/campaigns/{record.campaign_id}/images/{record.id}"}
