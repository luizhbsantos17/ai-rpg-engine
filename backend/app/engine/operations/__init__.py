"""Operações primitivas: o ÚNICO caminho para alterar o estado do jogo (D-004).

A IA (ou o administrador) propõe operações; o pipeline valida, aplica em transação e
registra cada uma no log de eventos. Operações inválidas são recusadas com o motivo.
"""

from app.engine.operations.context import OperationContext
from app.engine.operations.errors import OperationRejected
from app.engine.operations.pipeline import OperationOutcome, apply_operations

__all__ = ["OperationContext", "OperationOutcome", "OperationRejected", "apply_operations"]
