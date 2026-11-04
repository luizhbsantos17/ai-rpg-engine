"""Relógio do mundo, acontecimentos agendados e efeitos com duração (SPEC 10.2, 10.3; Parte 22 casos 14 e 24)."""

import pytest

from app.ai.context.game_state import build_game_state
from app.auth.local_user import ensure_local_user
from app.engine.errors import OperationRejected
from app.engine.notifications import describe_for_narrator, player_notices
from app.engine.operations import OperationContext, OperationOutcome, apply_operations
from app.engine.time import format_world_time, parse_duration
from app.persistence.repositories import CampaignData, CampaignRepository

WORLD = [
    {"op": "definition.create", "kind": "attribute", "key": "vida", "data": {"name": "Vida", "value_type": "integer", "resource": True}},
    {"op": "definition.create", "kind": "effect", "key": "veneno", "data": {"name": "Envenenado"}},
    {"op": "entity.create", "ref": "vila", "kind": "location", "name": "Vila"},
    {"op": "entity.create", "kind": "character", "name": "Kael", "is_player": True, "location": "vila", "attributes": {"vida": 20}},
]


@pytest.fixture
def run(db):
    with db.transaction() as session:
        campaign_id = CampaignRepository(session, ensure_local_user(session).id).create("Tempo", rng_seed=9).id

    def _run(operations):
        with db.transaction() as session:
            ctx = OperationContext(CampaignData(session, campaign_id), source="ai", campaign_seed=9)
            return apply_operations(ctx, operations)

    def _read(fn):
        with db.transaction() as session:
            return fn(CampaignData(session, campaign_id))

    _run.read = _read
    assert all(o.status == "applied" for o in _run(WORLD))
    return _run


@pytest.mark.parametrize("raw,minutes", [(90, 90), ("90", 90), ("30m", 30), ("4h", 240), ("2d", 2880), ("1d12h", 2160), ("1s", 10080)])
def test_durations(raw, minutes):
    assert parse_duration(raw) == minutes


@pytest.mark.parametrize("raw", [0, "-1h", "abc", "2x", "1h abc", True])
def test_invalid_durations(raw):
    with pytest.raises(OperationRejected):
        parse_duration(raw)


def test_world_time_format():
    assert format_world_time(0) == "dia 1, 00:00"
    assert format_world_time(1440 + 6 * 60 + 5) == "dia 2, 06:05"


def test_time_only_advances_by_operation(run):
    assert run.read(lambda d: d.campaign().world_clock) == 0
    outcome = run([{"op": "time.advance", "duration": "8h", "reason": "dormiu"}])[0]
    assert outcome.status == "applied"
    assert outcome.result["to_text"] == "dia 1, 08:00"
    assert run.read(lambda d: d.campaign().world_clock) == 480
    assert "Tempo do mundo: dia 1, 08:00." in run.read(lambda d: build_game_state(d).text)


def test_scheduled_events_trigger_in_order_when_time_passes(run):
    outcomes = run([
        {"op": "event.schedule", "after": "2d", "summary": "A caravana chega à vila.",
         "operations": [{"op": "entity.create", "kind": "character", "name": "Mercador"}]},
        {"op": "event.schedule", "after": "1d", "summary": "Começa a chover."},
        {"op": "event.schedule", "after": "1h", "summary": "inválido", "operations": [{"op": "time.advance", "duration": "1h"}]},
        {"op": "event.schedule", "after": "1h", "summary": "malformado", "operations": [{"op": "nada"}]},
    ])
    assert [o.status for o in outcomes] == ["applied", "applied", "rejected", "rejected"]

    first = run([{"op": "time.advance", "duration": "1d"}])[0].result
    assert [t["summary"] for t in first["triggered"]] == ["Começa a chover."]
    second = run([{"op": "time.advance", "duration": "1d"}])[0].result
    assert [t["summary"] for t in second["triggered"]] == ["A caravana chega à vila."]
    assert second["triggered"][0]["outcomes"][0]["status"] == "applied"
    names = run.read(lambda d: [e.name for e in d.entities.list()])
    assert "Mercador" in names
    # Cada agendamento dispara uma vez só.
    assert run([{"op": "time.advance", "duration": "5d"}])[0].result["triggered"] == []


def test_scheduled_operations_keep_references_from_their_batch(run):
    outcomes = run([
        {"op": "entity.create", "ref": "lobo", "kind": "creature", "name": "Lobo", "attributes": {"vida": 8}},
        {"op": "event.schedule", "after": "1h", "summary": "O lobo morre de fome.",
         "operations": [{"op": "entity.update", "entity": "lobo", "status": "dead"}]},
    ])
    assert [o.status for o in outcomes] == ["applied", "applied"]
    run([{"op": "time.advance", "duration": "2h"}])
    assert run.read(lambda d: {e.name: e.status for e in d.entities.list()})["Lobo"] == "dead"


def test_effects_expire_with_time_and_are_not_duplicated(run):
    outcomes = run([
        {"op": "effect.apply", "target": "player", "key": "veneno", "duration": "2h"},
        {"op": "effect.apply", "target": "player", "key": "veneno", "duration": "3h"},
        {"op": "effect.apply", "target": "player", "key": "efeito_inexistente"},
    ])
    assert [o.status for o in outcomes] == ["applied", "applied", "rejected"]
    assert outcomes[1].result["refreshed"] is True
    player_effects = lambda d: [e.definition_key for e in d.effects.active_for(d.entities.player().id)]  # noqa: E731
    assert run.read(player_effects) == ["veneno"]
    assert run([{"op": "time.advance", "duration": "2h"}])[0].result["expired_effects"] == []
    expired = run([{"op": "time.advance", "duration": "1h"}])[0].result["expired_effects"]
    assert [e["name"] for e in expired] == ["Envenenado"]
    assert run.read(player_effects) == []


def test_notices_and_narrator_lines_for_time(run):
    run([{"op": "event.schedule", "after": "1h", "summary": "Um sino toca ao longe.",
          "operations": [{"op": "attribute.modify", "entity": "player", "key": "vida", "delta": -1}]}])
    outcome = run([{"op": "time.advance", "duration": "2h"}])[0]
    player_id = run.read(lambda d: d.entities.player().id)
    lines = describe_for_narrator([outcome])
    assert lines[0] == "O tempo passou: 2h (agora dia 1, 02:00)."
    assert "Enquanto o tempo passava (dia 1, 01:00): Um sino toca ao longe." in lines
    assert any("Vida de Kael: 20 → 19" in line for line in lines)
    notices = [n.as_message() for n in player_notices([outcome], player_id)]
    assert notices == ["[SISTEMA] Tempo: dia 1, 02:00 (+2h).", "[SISTEMA] Vida: 20 → 19 / 20"]


def test_schedules_are_secret_from_narration(run):
    outcome = run([{"op": "event.schedule", "after": "1d", "summary": "O traidor age."}])[0]
    assert describe_for_narrator([outcome]) == []
    assert isinstance(outcome, OperationOutcome)
