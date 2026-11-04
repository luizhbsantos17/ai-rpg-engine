"""API HTTP de campanhas e turnos (com FakeProvider)."""

import json
import uuid

from app.providers import ProviderUnavailableError


def parse_sse(body: str):
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def create(client, **body):
    payload = {"title": "Ecos de Aurora", "premise": "Você acorda num templo.", "genre_tags": ["isekai"], **body}
    return client.post("/api/campaigns", json=payload)


def play(client, campaign_id, text, turn_id=None):
    turn_id = turn_id or str(uuid.uuid4())
    response = client.post(f"/api/campaigns/{campaign_id}/turns", json={"turn_id": turn_id, "input": text})
    return turn_id, response


def test_create_list_and_get_campaign(client):
    response = create(client)
    assert response.status_code == 201
    campaign = response.get_json()["campaign"]
    assert campaign["title"] == "Ecos de Aurora"
    assert campaign["premise"] == "Você acorda num templo."
    assert campaign["genre_tags"] == ["isekai"]

    listed = client.get("/api/campaigns").get_json()["campaigns"]
    assert [c["id"] for c in listed] == [campaign["id"]]
    assert client.get(f"/api/campaigns/{campaign['id']}").get_json()["campaign"]["id"] == campaign["id"]


def test_campaign_response_never_contains_gm_secrets(client):
    campaign = create(client).get_json()["campaign"]
    assert "gm_secret" not in json.dumps(campaign)


def test_create_campaign_validation(client):
    response = client.post("/api/campaigns", json={"title": "   "})
    assert response.status_code == 400
    assert response.get_json()["error"]["details"][0]["field"] == "title"
    assert client.post("/api/campaigns", json={"title": "x", "hack": 1}).status_code == 400
    assert client.post("/api/campaigns", data="não é json").status_code == 400


def test_unknown_campaign_is_404(client):
    assert client.get(f"/api/campaigns/{uuid.uuid4()}").status_code == 404
    _, response = play(client, str(uuid.uuid4()), "oi")
    assert response.status_code == 404


def test_play_turn_streams_sse_and_history_is_saved(client, fake_ai):
    campaign_id = create(client).get_json()["campaign"]["id"]
    fake_ai.queue("O sino do templo toca três vezes.")
    turn_id, response = play(client, campaign_id, "Levanto e olho ao redor.")

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    events = parse_sse(response.get_data(as_text=True))
    names = [name for name, _ in events]
    assert names[0] == "turn" and names[-1] == "done" and "delta" in names
    assert "".join(d["text"] for n, d in events if n == "delta") == "O sino do templo toca três vezes."
    assert events[0][1]["turn"]["id"] == turn_id

    history = client.get(f"/api/campaigns/{campaign_id}/history").get_json()
    assert [(m["role"], m["content"]) for m in history["messages"]] == [
        ("player", "Levanto e olho ao redor."), ("narration", "O sino do templo toca três vezes."),
    ]
    assert history["turns"][0]["status"] == "completed"
    after = client.get(f"/api/campaigns/{campaign_id}/history?after_seq=1").get_json()
    assert [m["seq"] for m in after["messages"]] == [2]


def test_ai_failure_arrives_as_error_event(client, fake_ai):
    campaign_id = create(client).get_json()["campaign"]["id"]
    fake_ai.queue(ProviderUnavailableError("Não foi possível conectar ao Ollama."))
    _, response = play(client, campaign_id, "Grito.")
    events = parse_sse(response.get_data(as_text=True))
    assert events[-1][0] == "error"
    assert events[-1][1]["retryable"] is True
    assert "Ollama" in events[-1][1]["message"]


def test_turn_request_validation(client):
    campaign_id = create(client).get_json()["campaign"]["id"]
    _, response = play(client, campaign_id, "")
    assert response.status_code == 400
    response = client.post(f"/api/campaigns/{campaign_id}/turns", json={"turn_id": "x", "input": "oi"})
    assert response.status_code == 400


def test_delete_requires_exact_title(client, fake_ai):
    campaign_id = create(client).get_json()["campaign"]["id"]
    fake_ai.queue("narração")
    play(client, campaign_id, "ação")

    wrong = client.delete(f"/api/campaigns/{campaign_id}", json={"confirm_title": "outro"})
    assert wrong.status_code == 400
    assert client.get(f"/api/campaigns/{campaign_id}").status_code == 200

    right = client.delete(f"/api/campaigns/{campaign_id}", json={"confirm_title": "Ecos de Aurora"})
    assert right.status_code == 204
    assert client.get(f"/api/campaigns/{campaign_id}").status_code == 404
    assert client.get("/api/campaigns").get_json()["campaigns"] == []
