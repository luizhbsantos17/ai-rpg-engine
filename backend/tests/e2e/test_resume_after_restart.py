"""Fluxo completo da Etapa 1 (SPEC Parte 22, casos 1, 3, 4 e 24; critério da Parte 23).

Cria campanha → joga 3 turnos → "fecha o programa" (descarta a aplicação e as conexões)
→ "abre de novo" (nova aplicação, mesmo arquivo de banco) → histórico idêntico e o jogo continua.
Usa FakeProvider: verifica a lógica interna, não a qualidade de uma IA real.
"""

import json
import uuid

from app import create_app
from app.persistence.repositories import CampaignRepository


def sse_events(response):
    return [
        (dict(line.split(": ", 1) for line in block.splitlines()))
        for block in response.get_data(as_text=True).strip().split("\n\n")
    ]


def play(client, campaign_id, text):
    response = client.post(
        f"/api/campaigns/{campaign_id}/turns", json={"turn_id": str(uuid.uuid4()), "input": text}
    )
    assert response.status_code == 200
    assert sse_events(response)[-1]["event"] == "done"


def start_app(settings, narrations):
    application = create_app(settings)
    application.extensions["rpg_engine"].provider.queue(*narrations)
    return application


def shutdown(application):
    application.extensions["rpg_engine"].db.dispose()


def test_play_close_reopen_and_continue(settings):
    # 1ª execução do programa
    app1 = start_app(settings, ["Narração 1.", "Narração 2.", "Narração 3."])
    client1 = app1.test_client()
    campaign = client1.post("/api/campaigns", json={"title": "Persistente", "premise": "Teste de retomada."})
    campaign_id = campaign.get_json()["campaign"]["id"]
    for n in (1, 2, 3):
        play(client1, campaign_id, f"Ação {n}.")
    before = client1.get(f"/api/campaigns/{campaign_id}/history").get_json()
    database_url = app1.extensions["rpg_engine"].db.url
    shutdown(app1)

    # 2ª execução: tudo de novo a partir do disco
    app2 = start_app(settings, ["Narração 4."])
    client2 = app2.test_client()
    after = client2.get(f"/api/campaigns/{campaign_id}/history").get_json()

    assert json.dumps(after, sort_keys=True) == json.dumps(before, sort_keys=True)
    assert [t["number"] for t in after["turns"]] == [1, 2, 3]
    assert [m["content"] for m in after["messages"]][-2:] == ["Ação 3.", "Narração 3."]
    assert app2.extensions["rpg_engine"].db.url == database_url  # mesmo arquivo de banco

    # Continua do mesmo ponto: a IA recebe a história anterior.
    play(client2, campaign_id, "Ação 4.")
    sent = app2.extensions["rpg_engine"].provider.calls[0].messages
    assert [m.content for m in sent[1:]] == [
        "Ação 1.", "Narração 1.", "Ação 2.", "Narração 2.", "Ação 3.", "Narração 3.", "Ação 4.",
    ]
    final = client2.get(f"/api/campaigns/{campaign_id}/history").get_json()
    assert [t["number"] for t in final["turns"]] == [1, 2, 3, 4]
    shutdown(app2)


def test_reopening_does_not_advance_world_time(settings):
    """SPEC 10.3 / caso 24: fechar e abrir não avança o relógio do mundo."""
    app1 = start_app(settings, ["n"])
    client1 = app1.test_client()
    campaign_id = client1.post("/api/campaigns", json={"title": "Relógio"}).get_json()["campaign"]["id"]
    play(client1, campaign_id, "a")
    services = app1.extensions["rpg_engine"]
    with services.db.transaction() as session:
        clock_before = CampaignRepository(session, services.local_user_id).get(campaign_id).world_clock
    shutdown(app1)

    app2 = start_app(settings, [])
    services2 = app2.extensions["rpg_engine"]
    with services2.db.transaction() as session:
        assert CampaignRepository(session, services2.local_user_id).get(campaign_id).world_clock == clock_before
    shutdown(app2)
