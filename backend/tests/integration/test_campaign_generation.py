"""Geração aleatória de campanhas (SPEC 3.1–3.3; Parte 22 caso 21)."""

import json
import uuid

from app.ai.prompts.generator import INGREDIENTS, pick_ingredients
from app.persistence.repositories import CampaignData, CampaignRepository
from app.providers import ProviderUnavailableError


def concept(title, premise="Você acorda num mundo estranho e precisa decidir em quem confiar.", tags=("fantasia",),
            secrets=("O mentor é o vilão.", "A cidade é uma ilusão.")):
    return json.dumps({"title": title, "genre_tags": list(tags), "premise": premise, "secrets": list(secrets)})


def test_ingredients_are_engine_rolled_and_reproducible():
    assert pick_ingredients(123) == pick_ingredients(123)
    picked = pick_ingredients(123)
    assert set(picked) == set(INGREDIENTS) and all(picked[k] in INGREDIENTS[k] for k in picked)
    assert len({tuple(pick_ingredients(s).values()) for s in range(30)}) > 20  # varia de verdade


def test_generate_creates_a_draft_without_leaking_secrets(client, fake_ai):
    fake_ai.queue(concept("A Cidade de Vidro"))
    response = client.post("/api/campaigns/generate", json={"genres": ["mistério"], "themes": "nada de dragões"})
    assert response.status_code == 201
    campaign = response.get_json()["campaign"]
    assert campaign["status"] == "draft" and campaign["title"] == "A Cidade de Vidro"
    assert campaign["secrets_count"] == 2
    everything = json.dumps(response.get_json()) + json.dumps(client.get(f"/api/campaigns/{campaign['id']}").get_json())
    everything += json.dumps(client.get("/api/campaigns").get_json())
    assert "vilão" not in everything and "ilusão" not in everything and "inspiracao" not in everything

    prompt = fake_ai.calls[0].messages[1].content
    assert "Gêneros desejados pelo jogador: mistério" in prompt and "nada de dragões" in prompt
    assert "Ingredientes sugeridos" in prompt


def test_regenerate_keeps_chosen_fields(client, fake_ai, services):
    fake_ai.queue(concept("Título Bom", premise="Premissa original que o jogador adorou muito mesmo."))
    draft = client.post("/api/campaigns/generate", json={}).get_json()["campaign"]
    # A IA "esquece" de manter, mas o motor garante o que o jogador pediu.
    fake_ai.queue(concept("Outro Título", premise="Uma premissa completamente diferente e nova aqui.", tags=("sci-fi",)))
    again = client.post("/api/campaigns/generate", json={"draft_id": draft["id"], "keep": ["premise"]}).get_json()["campaign"]
    assert again["id"] == draft["id"]
    assert again["premise"] == "Premissa original que o jogador adorou muito mesmo."
    assert again["title"] == "Outro Título" and again["genre_tags"] == ["sci-fi"]
    assert "MANTENHA exatamente" in fake_ai.calls[1].messages[1].content
    with services.db.transaction() as session:
        campaign = CampaignRepository(session, services.local_user_id).get(draft["id"])
        assert campaign.intro.version == 2
        assert [e.type for e in CampaignData(session, draft["id"]).events.list_ordered()].count("campaign.generated") == 2


def test_customize_then_start_then_cannot_regenerate(client, fake_ai):
    fake_ai.queue(concept("Rascunho"))
    draft = client.post("/api/campaigns/generate", json={}).get_json()["campaign"]
    turn = client.post(f"/api/campaigns/{draft['id']}/turns", json={"turn_id": str(uuid.uuid4()), "input": "oi"})
    assert turn.status_code == 409  # rascunho não se joga

    edited = client.patch(f"/api/campaigns/{draft['id']}", json={"title": "Meu Título", "genre_tags": ["horror"]})
    assert edited.get_json()["campaign"]["title"] == "Meu Título"
    started = client.post(f"/api/campaigns/{draft['id']}/start").get_json()["campaign"]
    assert started["status"] == "active"
    assert client.post("/api/campaigns/generate", json={"draft_id": draft["id"]}).status_code == 409
    assert client.patch(f"/api/campaigns/{draft['id']}", json={"title": "x"}).status_code == 409


def test_generation_failures_are_clear(client, fake_ai):
    fake_ai.queue(ProviderUnavailableError("Ollama desligado."))
    response = client.post("/api/campaigns/generate", json={})
    assert response.status_code == 503 and "Ollama desligado" in response.get_json()["error"]["message"]
    fake_ai.queue("isto não é json", "{}")
    response = client.post("/api/campaigns/generate", json={})
    assert response.status_code == 503 and "Tente de novo" in response.get_json()["error"]["message"]
    assert client.get("/api/campaigns").get_json()["campaigns"] == []  # nada pela metade


def test_secrets_reach_the_storyteller_but_not_generation_metadata(client, fake_ai):
    fake_ai.queue(concept("Com Segredos"))
    draft = client.post("/api/campaigns/generate", json={}).get_json()["campaign"]
    client.post(f"/api/campaigns/{draft['id']}/start")
    fake_ai.queue("Começa a história.")
    client.post(f"/api/campaigns/{draft['id']}/turns",
                json={"turn_id": str(uuid.uuid4()), "input": "Começo."}).get_data()
    narrator_system = fake_ai.calls[-1].messages[0].content
    assert "O mentor é o vilão." in narrator_system and "NUNCA revele" in narrator_system
    assert "inspiracao" not in narrator_system and "semente" not in narrator_system
