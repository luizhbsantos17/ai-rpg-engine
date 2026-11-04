import pytest

from app.engine.dice import DiceSyntaxError, derive_seed, new_seed, parse_dice, roll, roll_uniform


def test_same_seed_same_result():
    a = roll("4d6kh3+2", seed=12345)
    b = roll("4d6kh3+2", seed=12345)
    assert a == b


def test_different_seeds_vary():
    totals = {roll("3d20", seed=s).total for s in range(50)}
    assert len(totals) > 10


@pytest.mark.parametrize("expression", ["1d20", "d20", "3d6+2", "2d20kh1", "2d20kl1-1", "1d4+1d6+3", " 2D8 + 1 "])
def test_results_stay_within_bounds(expression):
    terms = parse_dice(expression)
    minimum = sum(t.sign * (t.keep_count or t.count) if hasattr(t, "faces") else t.sign * t.value for t in terms)
    maximum = sum(
        t.sign * (t.keep_count or t.count) * t.faces if hasattr(t, "faces") else t.sign * t.value for t in terms
    )
    low, high = min(minimum, maximum), max(minimum, maximum)
    for seed in range(200):
        assert low <= roll(expression, seed).total <= high


def test_keep_highest_and_lowest():
    for seed in range(100):
        advantage = roll("2d20kh1", seed).terms[0]
        disadvantage = roll("2d20kl1", seed).terms[0]
        assert advantage.kept == [max(advantage.rolls)]
        assert disadvantage.kept == [min(disadvantage.rolls)]


def test_details_are_recorded_for_audit():
    result = roll("2d6+3", seed=7).to_dict()
    assert result["seed"] == 7 and result["expression"] == "2d6+3"
    dice, constant = result["terms"]
    assert len(dice["rolls"]) == 2 and dice["notation"] == "+2d6"
    assert constant == {"notation": "+3", "rolls": [], "kept": [], "subtotal": 3}
    assert result["total"] == dice["subtotal"] + 3


def test_negative_terms():
    result = roll("10-1d4", seed=1)
    assert 6 <= result.total <= 9


@pytest.mark.parametrize(
    "bad",
    ["", "abc", "2d", "d0", "0d6", "1001d6", "1d1000001", "2d20kh3", "2d6 3", "1d6++2", "1d6*2", "x" * 300],
)
def test_invalid_expressions(bad):
    with pytest.raises(DiceSyntaxError):
        roll(bad, seed=1)


def test_derived_seeds_are_deterministic_and_distinct():
    assert derive_seed(99, "turno-1", 0) == derive_seed(99, "turno-1", 0)
    assert derive_seed(99, "turno-1", 0) != derive_seed(99, "turno-1", 1)
    assert derive_seed(99, "turno-1", 0) != derive_seed(100, "turno-1", 0)
    assert 0 <= derive_seed(99, "x") < 2**63


def test_new_seed_range():
    assert all(0 <= new_seed() < 2**63 for _ in range(20))


def test_roll_uniform():
    assert roll_uniform(5, 1, 100) == roll_uniform(5, 1, 100)
    assert all(1 <= roll_uniform(s, 1, 3) <= 3 for s in range(50))
    with pytest.raises(ValueError):
        roll_uniform(1, 5, 1)
