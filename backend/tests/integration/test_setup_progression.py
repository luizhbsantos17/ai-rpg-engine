"""Preparação da campanha com ficha completa: progressão, energia, habilidades e itens iniciais (SPEC 5).

Usa o motor de verdade (operações validadas); o JSON da IA é escrito à mão aqui.
"""

from app.ai.prompts.narrator import CampaignBrief
from app.ai.prompts.setup import build_setup_messages
from app.ai.schemas.setup import CampaignSetup
from app.auth.local_user import ensure_local_user
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData, CampaignRepository
from app.services.sheet import CharacterSheetService

SETUP = {
    "attributes": [
        {"name": "Vida", "resource": True, "initial_value": 30},
        {"name": "Mana", "resource": True, "initial_value": 12},
        {"name": "Força", "initial_value": 4},
        {"name": "Agilidade", "initial_value": 6},
        {"name": "Sorte", "initial_value": 3},
        {"name": "Nível", "initial_value": 1},
        {"name": "Experiência", "initial_value": 0},
    ],
    "protagonist": {"name": "Lia", "description": "aprendiz de maga", "character_class": "maga", "race": "humana"},
    "starting_location": "Torre do Sábio",
    "starting_skills": [{"name": "Faísca", "description": "pequena chama", "category": "magia", "level": 1},
                        {"name": "Faísca", "level": 3}],  # repetida: fica só a primeira
    "starting_items": [
        {"name": "Cajado de Carvalho", "slot": "mão", "bonus": {"Força": 1, "Inexistente": 5}, "equipped": True},
        {"name": "Túnica", "slot": "corpo", "equipped": False},
        {"name": "Moedas de Cobre", "quantity": 15},
    ],
}


def test_setup_builds_a_full_sheet(db):
    with db.transaction() as session:
        owner_id = ensure_local_user(session).id
        campaign_id = CampaignRepository(session, owner_id).create("Torre", rng_seed=3).id
    operations = CampaignSetup.model_validate(SETUP).to_operations()
    with db.transaction() as session:
        outcomes = apply_operations(OperationContext(CampaignData(session, campaign_id), "ai", 3), operations)
    assert all(o.status == "applied" for o in outcomes), [(o.op, o.reason) for o in outcomes if o.status != "applied"]

    sheet = CharacterSheetService(db).sheet(owner_id, campaign_id)["character"]
    names = {a["name"] for a in sheet["attributes"]}
    assert {"Vida", "Mana", "Nível", "Experiência", "Sorte"} <= names
    assert [(s["name"], s["level"]) for s in sheet["skills"]] == [("Faísca", 1)]
    items = {i["name"]: i for i in sheet["items"]}
    assert items["Cajado de Carvalho"]["equipped_slot"] == "mao"
    assert items["Cajado de Carvalho"]["bonus"] == {"forca": 1}  # atributo inexistente é ignorado
    assert items["Túnica"]["equipped_slot"] is None
    assert items["Moedas de Cobre"]["quantity"] == 15


def test_setup_prompt_asks_for_progression_and_says_if_there_is_a_status_window():
    brief = CampaignBrief(title="Torre", genre_tags=["fantasia"], player_visible={"premise": "Uma aprendiz."})
    game_like = build_setup_messages(brief, system_window=True)
    assert "Nível" in game_like[0].content and "starting_items" in game_like[0].content
    assert "Janela de status: SIM" in game_like[1].content
    assert "Janela de status: NÃO" in build_setup_messages(brief, system_window=False)[1].content
