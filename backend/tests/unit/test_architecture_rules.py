"""Testes "guardiões" das regras invioláveis do CLAUDE.md, verificadas no código-fonte."""

import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[2] / "app"


def python_files(*exclude_dirs: str):
    excluded = [APP_DIR / d for d in exclude_dirs]
    for path in APP_DIR.rglob("*.py"):
        if not any(path.is_relative_to(e) for e in excluded):
            yield path


def test_only_persistence_layer_queries_the_database():
    """Todo acesso a dados passa pelos repositórios (app/persistence)."""
    forbidden = re.compile(r"\bselect\(|\.query\(|session\.execute\(|session\.get\(|session\.scalars?\(")
    offenders = [
        f"{path.relative_to(APP_DIR)}:{n}"
        for path in python_files("persistence")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if forbidden.search(line)
    ]
    assert offenders == [], f"Consulta ao banco fora dos repositórios: {offenders}"


def test_no_eval_or_exec_anywhere():
    """Fórmulas da IA usam o avaliador seguro; eval/exec são proibidos."""
    forbidden = re.compile(r"(?<![\w.])(eval|exec)\(")
    offenders = [
        f"{path.relative_to(APP_DIR)}:{n}"
        for path in python_files()
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if forbidden.search(line)
    ]
    assert offenders == []


def test_python_random_module_only_in_dice_engine():
    """Aleatoriedade só pelo motor (engine/dice), com seed registrada."""
    forbidden = re.compile(r"^\s*(import random\b|from random import)")
    offenders = [
        str(path.relative_to(APP_DIR))
        for path in python_files("engine/dice")
        if any(forbidden.search(line) for line in path.read_text(encoding="utf-8").splitlines())
    ]
    assert offenders == []
