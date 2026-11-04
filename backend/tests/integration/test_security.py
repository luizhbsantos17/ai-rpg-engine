"""Verificações de segurança da Etapa 7 (SPEC 20)."""

import json
import uuid

import pytest

from app import MAX_REQUEST_BYTES
from app.admin.sessions import MAX_FAILED_LOGINS, AdminAccessError, AdminSessions


def test_oversized_requests_are_refused_with_json_error(client):
    big = "x" * (MAX_REQUEST_BYTES + 1)
    response = client.post("/api/campaigns/import", data=big, content_type="application/json")
    assert response.status_code == 413
    assert response.get_json()["error"]["code"] == 413


def test_admin_password_guessing_is_slowed_down():
    now = [0.0]
    sessions = AdminSessions("certa", clock=lambda: now[0])
    for _ in range(MAX_FAILED_LOGINS):
        with pytest.raises(AdminAccessError, match="incorreta"):
            sessions.login("errada")
    with pytest.raises(AdminAccessError, match="Espere"):
        sessions.login("certa")  # bloqueado mesmo com a senha certa
    now[0] += 61
    assert sessions.login("certa")


@pytest.mark.parametrize("query", ['"); DROP TABLE campaigns; --', "* OR 1", "NEAR(a b)", "\u0000 aaa", "' OR ''='"])
def test_memory_search_input_cannot_break_the_query(client, fake_ai, query):
    campaign_id = client.post("/api/campaigns", json={"title": "Busca"}).get_json()["campaign"]["id"]
    fake_ai.queue("Narração.")
    for text in (query, "Ajo normalmente."):
        response = client.post(f"/api/campaigns/{campaign_id}/turns", json={"turn_id": str(uuid.uuid4()), "input": text})
        assert response.status_code in (200, 400)
        response.get_data()
    assert client.get("/api/campaigns").status_code == 200


def test_errors_never_expose_secrets_or_stack_traces(client, flask_app):
    @flask_app.get("/api/_explode")
    def explode():
        raise RuntimeError(flask_app.config["SECRET_KEY"])

    body = client.get("/api/_explode").get_data(as_text=True)
    assert flask_app.config["SECRET_KEY"] not in body and "Traceback" not in body


def test_api_responses_never_include_gm_secrets(client, fake_ai):
    fake_ai.queue(json.dumps({"title": "T", "genre_tags": [], "premise": "Uma premissa longa o bastante.",
                              "secrets": ["SEGREDO-ABSOLUTO"]}))
    draft = client.post("/api/campaigns/generate", json={}).get_json()["campaign"]
    client.post(f"/api/campaigns/{draft['id']}/start")
    for url in ("/api/campaigns", f"/api/campaigns/{draft['id']}", f"/api/campaigns/{draft['id']}/history",
                f"/api/campaigns/{draft['id']}/sheet", f"/api/campaigns/{draft['id']}/known",
                f"/api/campaigns/{draft['id']}/journal", f"/api/campaigns/{draft['id']}/settings"):
        assert "SEGREDO-ABSOLUTO" not in client.get(url).get_data(as_text=True), url
