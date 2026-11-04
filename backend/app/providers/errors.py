"""Erros dos provedores de IA, com mensagens que podem ser mostradas ao jogador."""

from __future__ import annotations


class ProviderError(Exception):
    """Falha ao usar um provedor de IA. `retryable`: tentar de novo pode funcionar."""

    retryable = False

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ProviderUnavailableError(ProviderError):
    """Não foi possível conectar (programa desligado, endereço errado, sem internet)."""

    retryable = True


class ProviderTimeoutError(ProviderError):
    retryable = True


class ModelNotFoundError(ProviderError):
    """O modelo pedido não existe ou não está instalado."""


class ProviderResponseError(ProviderError):
    """O provedor respondeu com erro ou com algo que não dá para entender."""
