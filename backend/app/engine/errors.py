"""Erros do motor de RPG."""


class OperationRejected(Exception):
    """Operação recusada pela validação (o motivo vai para o log e para a IA corrigir)."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason
