"""Avaliador seguro de fórmulas criadas pela IA ou pelo administrador (ARCHITECTURE §5.3)."""

from app.engine.expressions.evaluator import (
    ExpressionError,
    analyze,
    evaluate,
)

__all__ = ["ExpressionError", "analyze", "evaluate"]
