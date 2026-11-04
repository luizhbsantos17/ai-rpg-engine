"""Turno com o motor ligado (D-013): preparação → intérprete → motor → narrador. FakeProvider roteirizado."""

import json
import uuid

import pytest

from app import create_app
from app.ai.orchestrator.events import MechanicsApplied, NarrationDelta, TurnCompleted, TurnFailed
from app.persistence.repositories import CampaignData
from app.providers import ProviderUnavailableError

SETUP = json.dumps({
    "attributes": [
        {"name": "Vida", "value_type": "integer", "resource": True, "initial_value": 20},
        {"name": "Força", "value_type": "integer", "initial_value": 5},
    ],
    "protagonist": {"name": "Kael", "description": "aprendiz de cartógrafo"},
    "starting_location": "Vila Costeira",
})


def interpretation(*operations, intent="agir"):
    return json.dumps({"intent": intent, "operations": list(operations)})


@pytest.fixture
def app_with_mechanics(mechanics_settings):
    application = create_app(mechanics_settings)
    yield application
    application.extensions["rpg_engine"].db.dispose()


@pytest.fixture
def services(app_with_mechanics):
    return app_with_mechanics.extensions["rpg_engine"]


@pytest.fixture
def fake_ai(services):
    return services.provider


@pytest.fixture
def campaign(services):
    return services.campaigns.create(services.local_user_id, "Mapas Perdidos", "Os mapas sumiram.", ["mistério"])


def play(services, campaign_id, text, turn_id=None):
    turn_id = turn_id or str(uuid.uuid4())
    prepared = services.turns.prepare(services.local_user_id, campaign_id, turn_id, text)
    return turn_id, list(services.turns.run(prepared))


def state(services, campaign_id):
    with services.db.transaction() as session:
        data = CampaignData(session, campaign_id)
        player = data.entities.player()
        return {
            "player": player.name if player else None,
            "attributes": {a.definition_key: a.value for a in data.attributes.for_entity(player.id)} if player else {},
            "messages": [(m.role, m.content) for m in data.messages.list_ordered()],
            "dice_rolls": data.dice_rolls.count(),
            "requests": [(r.role, r.error is None) for r in reversed(data.ai_requests.latest(50))],
            "turns": [(t.number, t.status) for t in data.turns.list_ordered()],
        }


def test_first_turn_prepares_campaign_applies_operations_and_narrates_with_facts(services, fake_ai, campaign):
    fake_ai.queue(
        SETUP,
        interpretation(
            {"op": "attribute.modify", "entity": "player", "key": "vida", "delta": -3, "reason": "tropeçou"},
            intent="sair de casa",
        ),
        "Kael tropeça na soleira e sente o joelho arder.",
    )
    _, events = play(services, campaign["id"], "Saio de casa correndo.")

    mechanics = [e for e in events if isinstance(e, MechanicsApplied)]
    assert len(mechanics) == 1 and mechanics[0].intent == "sair de casa"
    notices = [m["content"] for m in mechanics[0].messages]
    assert "[SISTEMA] Personagem criado: Kael." in notices
    assert "[SISTEMA] Vida: 20 → 17 / 20" in notices
    assert isinstance(events[-1], TurnCompleted)

    narrator_call = fake_ai.calls[2].messages
    assert "motor de regras resolve testes" in narrator_call[0].content
    assert "RESULTADOS DO MOTOR" in narrator_call[-1].content
    assert "Vida de Kael: 20 → 17" in narrator_call[-1].content

    s = state(services, campaign["id"])
    assert s["player"] == "Kael" and s["attributes"] == {"vida": "17", "forca": "5"}
    assert [role for role, _ in s["messages"]] == ["player", "system", "system", "narration"]
    assert s["requests"] == [("setup", True), ("interpreter", True), ("narrator", True)]


def test_checks_are_rolled_by_engine_and_consequences_follow_the_result(services, fake_ai, campaign):
    fake_ai.queue(SETUP, interpretation(), "Começo.")
    play(services, campaign["id"], "Começo.")
    fake_ai.queue(
        interpretation(
            {"op": "check.request", "ref": "salto", "actor": "player", "label": "Saltar o muro",
             "modifier": "forca", "difficulty": 15},
            {"op": "attribute.modify", "entity": "player", "key": "vida", "delta": -5,
             "when": {"check": "salto", "success": False}, "reason": "caiu"},
        ),
        "Narração do salto.",
    )
    _, events = play(services, campaign["id"], "Salto o muro.")
    notices = [m["content"] for e in events if isinstance(e, MechanicsApplied) for m in e.messages]
    check_notice = next(n for n in notices if n.startswith("[TESTE] Saltar o muro"))
    succeeded = "→ sucesso" in check_notice or "→ sucesso crítico" in check_notice
    s = state(services, campaign["id"])
    assert s["dice_rolls"] == 1
    assert s["attributes"]["vida"] == ("20" if succeeded else "15")
    facts = fake_ai.calls[-1].messages[-1].content
    assert "Teste 'Saltar o muro'" in facts and ("SUCESSO" in facts or "FALHA" in facts)


def test_invalid_interpreter_json_does_not_stop_the_story(services, fake_ai, campaign):
    fake_ai.queue(SETUP, "isto não é json", '{"sem": "intent válido", "operations": "não é lista"}', "A história segue.")
    _, events = play(services, campaign["id"], "Faço algo estranho.")
    assert isinstance(events[-1], TurnCompleted)
    s = state(services, campaign["id"])
    assert s["requests"] == [("setup", True), ("interpreter", False), ("interpreter", False), ("narrator", True)]
    assert s["turns"] == [(1, "completed")]


def test_retry_after_narration_failure_does_not_apply_operations_twice(services, fake_ai, campaign):
    fake_ai.queue(
        SETUP,
        interpretation({"op": "attribute.modify", "entity": "player", "key": "vida", "delta": -4}),
        ProviderUnavailableError("caiu antes de narrar"),
    )
    turn_id, events = play(services, campaign["id"], "Luto.")
    assert isinstance(events[-1], TurnFailed)
    assert state(services, campaign["id"])["attributes"]["vida"] == "16"

    calls_before = len(fake_ai.calls)
    fake_ai.queue("Agora a narração saiu.")
    _, retry = play(services, campaign["id"], "Luto.", turn_id=turn_id)
    assert isinstance(retry[-1], TurnCompleted)
    assert len(fake_ai.calls) == calls_before + 1  # só o narrador; intérprete não roda de novo
    s = state(services, campaign["id"])
    assert s["attributes"]["vida"] == "16"  # dano aplicado UMA vez
    assert "Vida de Kael: 20 → 16" in fake_ai.calls[-1].messages[-1].content  # fatos guardados reaproveitados


def test_npc_changes_reach_narrator_but_not_player_notices(services, fake_ai, campaign):
    fake_ai.queue(SETUP, interpretation(
        {"op": "entity.create", "ref": "lobo", "kind": "creature", "name": "Lobo Cinzento",
         "attributes": {"vida": 12, "forca": 4}},
        {"op": "attribute.modify", "entity": "lobo", "key": "vida", "delta": -2},
    ), "Um lobo surge.")
    _, events = play(services, campaign["id"], "Olho a floresta.")
    notices = [m["content"] for e in events if isinstance(e, MechanicsApplied) for m in e.messages]
    assert not any("Lobo" in n for n in notices)  # status de NPC é oculto para o jogador
    facts = fake_ai.calls[-1].messages[-1].content
    assert "Surgiu Lobo Cinzento" in facts and "Vida de Lobo Cinzento: 12 → 10" in facts


def test_rejected_operations_are_told_to_narrator_as_not_happened(services, fake_ai, campaign):
    fake_ai.queue(SETUP, interpretation(
        {"op": "skill.grant", "entity": "player", "key": "voo_divino"},
    ), "Nada de especial acontece.")
    play(services, campaign["id"], "Tento voar.")
    facts = fake_ai.calls[-1].messages[-1].content
    assert "não aconteceu" in facts and "voo_divino" in facts


def test_replay_of_completed_turn_resends_notices_without_calling_ai(services, fake_ai, campaign):
    fake_ai.queue(SETUP, interpretation(), "Começo.")
    turn_id, _ = play(services, campaign["id"], "Começo.")
    calls = len(fake_ai.calls)
    _, again = play(services, campaign["id"], "Começo.", turn_id=turn_id)
    assert len(fake_ai.calls) == calls
    replayed = [m["content"] for e in again if isinstance(e, MechanicsApplied) for m in e.messages]
    assert replayed == ["[SISTEMA] Personagem criado: Kael."]
    assert "".join(e.text for e in again if isinstance(e, NarrationDelta)) == "Começo."


def test_sse_stream_contains_mechanics_event(app_with_mechanics, fake_ai, campaign):
    fake_ai.queue(SETUP, interpretation(), "Começo.")
    response = app_with_mechanics.test_client().post(
        f"/api/campaigns/{campaign['id']}/turns", json={"turn_id": str(uuid.uuid4()), "input": "Começo."}
    )
    names = [block.split("\n", 1)[0] for block in response.get_data(as_text=True).strip().split("\n\n")]
    assert names[:2] == ["event: turn", "event: mechanics"] and names[-1] == "event: done"
