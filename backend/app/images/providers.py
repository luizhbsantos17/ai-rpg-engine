"""Provedores de imagem. Padrão: nenhum (IMAGE_PROVIDER=none).

Geradores reais (serviço pago ou modelo local grande, como Stable Diffusion) dependem de autorização do
dono do projeto e ainda não foram escolhidos. O `FakeImageProvider` existe só para os testes.
"""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import Settings


class ImageUnavailableError(Exception):
    pass


@dataclass(frozen=True)
class GeneratedImage:
    content: bytes
    mime_type: str
    provider: str


class ImageProvider(ABC):
    name = "base"
    configured = True
    is_paid = False

    @abstractmethod
    def generate(self, prompt: str) -> GeneratedImage:
        ...


class NoImageProvider(ImageProvider):
    name = "none"
    configured = False

    def generate(self, prompt: str) -> GeneratedImage:
        raise ImageUnavailableError("Geração de imagens desligada (IMAGE_PROVIDER=none). O jogo funciona sem ela.")


# PNG de 1×1 pixel (só para testes)
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


class FakeImageProvider(ImageProvider):
    name = "fake"

    def __init__(self):
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> GeneratedImage:
        self.prompts.append(prompt)
        return GeneratedImage(_TINY_PNG, "image/png", self.name)


def build_image_provider(settings: Settings) -> ImageProvider:
    if settings.image_provider == "fake":
        if settings.app_env != "test":
            raise ImageUnavailableError("IMAGE_PROVIDER=fake só existe para os testes.")
        return FakeImageProvider()
    return NoImageProvider()
