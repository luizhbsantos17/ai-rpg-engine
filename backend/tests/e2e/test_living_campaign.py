"""Campanha simulada da Etapa 3 (critério da Parte 23: continuidade narrativa e acontecimentos persistentes).

Fluxo: gerar campanha → começar → turnos com motor (preparação, NPC, relação, missão, fato canônico,
agendamento, passagem de tempo) → fechar o programa → reabrir → tudo persiste e chega à IA.
Usa FakeProvider roteirizado: verifica a lógica interna, não a qualidade de uma IA real.
"""

import json
import uuid

from app import create_app
from app.persistence.repositories import CampaignData
from tests.conftest import make_settings

CONCEPT = json.dumps({"title": "O Farol Silencioso", "genre_tags": ["mistério"],
                      "premise": "Você chega a uma vila onde o farol apagou e ninguém fala sobre isso.",
                      "secrets": ["O faroleiro está vivo e escondido."]})
SETUP = json.dumps({
    "attributes": [{"name": "Vida", "resource": True, "initial_value": 20}, {"name": "Astúcia", "initial_value": 6}],
    "protagonist": {"name": "Nara"},
    "starting_location": "Vila de Breu",
    "world_facts": ["O farol guia os mortos para o mar.", "Quem morre aqui volta como névoa por três dias."],
})


def ops(*operations, intent="agir"):
    return json.dumps({"intent": intent, "operations": list(operations)})


def play(client, campaign_id, text):
    response = client.post(f"/api/campaigns/{campaign_id}/turns", json={"turn_id": str(uuid.uuid4()), "input": text})
    body = response.get_data(as_text=True)
    assert "event: done" in body, body[-500:]
    return body


def test_living_campaign_persists_across_restart(tmp_path, migrated_db_template):
    settings = make_settings(tmp_path, migrated_db_template, AI_MECHANICS="true", AI_SUMMARY_EVERY="0")

    app1 = create_app(settings)
    fake1 = app1.extensions["rpg_engine"].provider
    client1 = app1.test_client()
    fake1.queue(CONCEPT)
    campaign_id = client1.post("/api/campaigns/generate", json={}).get_json()["campaign"]["id"]
    client1.post(f"/api/campaigns/{campaign_id}/start")

    fake1.queue(SETUP, ops(
        {"op": "entity.create", "ref": "ilda", "kind": "character", "name": "Ilda", "location": "e1",
         "data": {"personality": "desconfiada", "goal": "proteger o neto"}},
        {"op": "quest.create", "key": "farol", "title": "Reacender o farol", "kind": "main", "giver": "ilda",
         "objectives": ["Descobrir por que apagou", "Subir ao farol"]},
    ), "Nara chega à vila; uma velha, Ilda, observa da janela.")
    play(client1, campaign_id, "Chego à vila e procuro alguém.")

    fake1.queue(ops(
        {"op": "relationship.change", "source": "e2", "target": "player", "changes": {"confianca": 20},
         "cause": "Nara devolveu a lanterna perdida do neto"},
        {"op": "canon.assert", "key": "faroleiro", "subject": "farol", "statement": "O faroleiro sumiu há sete noites.",
         "status": "rumor"},
        {"op": "event.schedule", "after": "1d", "summary": "A névoa invade a vila.",
         "operations": [{"op": "attribute.modify", "entity": "player", "key": "vida", "delta": -2}]},
        {"op": "quest.update", "key": "farol", "complete_objectives": [1]},
    ), "Ilda conta que o faroleiro sumiu.")
    play(client1, campaign_id, "Devolvo a lanterna do neto de Ilda e pergunto sobre o farol.")
    before = client1.get(f"/api/campaigns/{campaign_id}/history").get_json()
    sheet_before = client1.get(f"/api/campaigns/{campaign_id}/sheet").get_json()
    app1.extensions["rpg_engine"].db.dispose()  # "fecha o programa"

    app2 = create_app(settings)  # "abre de novo"
    fake2 = app2.extensions["rpg_engine"].provider
    client2 = app2.test_client()
    assert client2.get(f"/api/campaigns/{campaign_id}/history").get_json() == before
    assert client2.get(f"/api/campaigns/{campaign_id}/sheet").get_json() == sheet_before
    assert sheet_before["world_time"] == "dia 1, 00:00"  # fechar não avançou o tempo

    fake2.queue(ops({"op": "time.advance", "duration": "1d", "reason": "Nara dorme na estalagem"}),
                "Ao amanhecer, a névoa cobre tudo.")
    play(client2, campaign_id, "Durmo na estalagem até o dia seguinte.")

    interpreter_state = fake2.calls[0].messages[1].content
    assert "Ilda" in interpreter_state and "confianca=20" in interpreter_state
    assert "[rumor] faroleiro: O faroleiro sumiu há sete noites." in interpreter_state
    assert "farol: Reacender o farol — 1. [x] Descobrir por que apagou; 2. [ ] Subir ao farol" in interpreter_state
    narrator = fake2.calls[1].messages
    assert "O farol guia os mortos para o mar." in narrator[0].content  # fato inicial do universo
    assert "O faroleiro está vivo e escondido." in narrator[0].content  # segredo do mestre
    facts = narrator[-1].content
    assert "Enquanto o tempo passava (dia 2, 00:00): A névoa invade a vila." in facts
    assert "Ilda: personalidade: desconfiada; quer: proteger o neto; lembra:" in facts

    sheet = client2.get(f"/api/campaigns/{campaign_id}/sheet").get_json()
    assert sheet["world_time"] == "dia 2, 00:00"
    assert {a["key"]: a["value"] for a in sheet["character"]["attributes"]}["vida"] == "18"
    assert [q["title"] for q in sheet["quests"]] == ["Reacender o farol"]
    with app2.extensions["rpg_engine"].db.transaction() as session:
        data = CampaignData(session, campaign_id)
        ilda = next(e for e in data.entities.list() if e.name == "Ilda")
        assert len(data.memories.recall(ilda.id, 10)) == 3  # viu os três turnos
    app2.extensions["rpg_engine"].db.dispose()
