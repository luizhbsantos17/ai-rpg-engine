"""Imagens opcionais (SPEC 13): o jogo funciona sem; com provedor, associa à entidade e não repete."""

import pytest

from app import create_app
from app.config import ConfigError, load_settings
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData
from tests.conftest import make_settings


def setup_entity(app_, client):
    campaign_id = client.post("/api/campaigns", json={"title": "Img", "genre_tags": ["fantasia"]}).get_json()["campaign"]["id"]
    with app_.extensions["rpg_engine"].db.transaction() as session:
        outcome = apply_operations(OperationContext(CampaignData(session, campaign_id), "system", 1), [
            {"op": "entity.create", "kind": "creature", "name": "Grifo", "data": {"description": "asas douradas"}},
        ])[0]
    return campaign_id, outcome.result["entity_id"]


def test_without_provider_the_feature_is_off_and_nothing_breaks(client, flask_app):
    assert client.get("/api/images/status").get_json() == {"enabled": False, "provider": "none", "paid": False}
    campaign_id, entity_id = setup_entity(flask_app, client)
    response = client.post(f"/api/campaigns/{campaign_id}/images", json={"entity_id": entity_id})
    assert response.status_code == 503 and "desligada" in response.get_json()["error"]["message"]


@pytest.fixture
def app_with_images(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template, IMAGE_PROVIDER="fake"))
    yield application
    application.extensions["rpg_engine"].db.dispose()


def test_image_is_linked_to_entity_and_not_generated_twice(app_with_images):
    client = app_with_images.test_client()
    campaign_id, entity_id = setup_entity(app_with_images, client)
    first = client.post(f"/api/campaigns/{campaign_id}/images", json={"entity_id": entity_id}).get_json()
    second = client.post(f"/api/campaigns/{campaign_id}/images", json={"entity_id": entity_id}).get_json()
    assert first["reused"] is False and second["reused"] is True and first["id"] == second["id"]
    provider = app_with_images.extensions["rpg_engine"].images.provider
    assert len(provider.prompts) == 1  # só uma geração
    assert "Grifo" in provider.prompts[0] and "asas douradas" in provider.prompts[0] and "fantasia" in provider.prompts[0]

    picture = client.get(first["url"])
    assert picture.status_code == 200 and picture.mimetype == "image/png" and picture.data.startswith(b"\x89PNG")
    other = client.post("/api/campaigns", json={"title": "Outra"}).get_json()["campaign"]["id"]
    assert client.get(f"/api/campaigns/{other}/images/{first['id']}").status_code == 404  # isolamento


def test_image_provider_configuration_is_validated():
    with pytest.raises(ConfigError, match="IMAGE_PROVIDER"):
        load_settings(environ={"IMAGE_PROVIDER": "pago-qualquer"}, env_file=None)
    with pytest.raises(ConfigError, match="testes"):
        load_settings(environ={"IMAGE_PROVIDER": "fake"}, env_file=None)
