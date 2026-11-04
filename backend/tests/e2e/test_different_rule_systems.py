"""Critério da Etapa 4 (SPEC Parte 23): campanhas com sistemas de regras significativamente diferentes.

Campanha A — fantasia "clássica": atributos inteiros, vida como recurso, magia com custo e recarga,
morte permanente. Campanha B — mundo conceitual: Rank nominal (F..SSS), "Destino" em texto livre,
"Existência" decimal astronômica, testes com fórmula que lê o Rank, reencarnação.
As duas rodam lado a lado no mesmo banco, sem uma afetar a outra.
"""

from app.auth.local_user import ensure_local_user
from app.engine.operations import OperationContext, apply_operations
from app.persistence.repositories import CampaignData, CampaignRepository

CLASSIC = [
    {"op": "definition.create", "kind": "attribute", "key": "forca", "data": {"name": "Força", "value_type": "integer", "min": 0}},
    {"op": "definition.create", "kind": "attribute", "key": "vida", "data": {"name": "Vida", "value_type": "integer", "resource": True}},
    {"op": "definition.create", "kind": "attribute", "key": "mana", "data": {"name": "Mana", "value_type": "integer", "resource": True}},
    {"op": "definition.create", "kind": "skill", "key": "bola_de_fogo",
     "data": {"name": "Bola de Fogo", "costs": [{"resource": "mana", "amount": 5}], "cooldown": "10m"}},
    {"op": "definition.create", "kind": "death_rule", "key": "morte",
     "data": {"name": "Morte", "mode": "permanent", "vital_resource": "vida"}},
    {"op": "entity.create", "kind": "character", "name": "Aria", "is_player": True,
     "attributes": {"forca": 8, "vida": 20, "mana": 12}},
    {"op": "entity.create", "ref": "orc", "kind": "creature", "name": "Orc", "attributes": {"forca": 10, "vida": 6}},
    {"op": "skill.grant", "entity": "player", "key": "bola_de_fogo"},
    {"op": "skill.use", "entity": "player", "key": "bola_de_fogo", "target": "orc"},
    {"op": "attribute.modify", "entity": "orc", "key": "vida", "delta": "-forca"},  # fórmula com a força do orc
    {"op": "skill.use", "entity": "player", "key": "bola_de_fogo"},  # em recarga
]

CONCEPTUAL = [
    {"op": "definition.create", "kind": "attribute", "key": "rank",
     "data": {"name": "Rank", "value_type": "nominal", "scale": ["F", "E", "D", "C", "B", "A", "S", "SS", "SSS"]}},
    {"op": "definition.create", "kind": "attribute", "key": "destino", "data": {"name": "Destino", "value_type": "conceptual"}},
    {"op": "definition.create", "kind": "attribute", "key": "existencia",
     "data": {"name": "Existência", "value_type": "decimal", "resource": True}},
    {"op": "definition.create", "kind": "death_rule", "key": "ciclo",
     "data": {"name": "Ciclo", "mode": "reincarnation", "vital_resource": "existencia"}},
    {"op": "entity.create", "kind": "character", "name": "Sem-Nome", "is_player": True,
     "attributes": {"rank": "F", "destino": "quebrar a roda do tempo", "existencia": "1e50"}},
    {"op": "entity.create", "ref": "deus", "kind": "deity", "name": "Deus Esquecido",
     "attributes": {"rank": "SSS", "existencia": "9.99e99"}},
    {"op": "check.request", "actor": "player", "target": "deus", "label": "Encarar o deus", "dice": "1d1",
     "modifier": 0, "difficulty": "1000 if target.rank == 'SSS' else 5"},
    {"op": "attribute.set", "entity": "player", "key": "rank", "value": "S", "reason": "despertar"},
    {"op": "attribute.set", "entity": "player", "key": "rank", "value": "Z"},  # fora da escala
    {"op": "attribute.modify", "entity": "player", "key": "existencia", "delta": "-2e50"},  # aniquilação
]


def run(db, title, seed, operations):
    with db.transaction() as session:
        campaign_id = CampaignRepository(session, ensure_local_user(session).id).create(title, rng_seed=seed).id
    with db.transaction() as session:
        outcomes = apply_operations(OperationContext(CampaignData(session, campaign_id), "ai", seed), operations)
    return campaign_id, outcomes


def test_two_campaigns_with_very_different_rules(db):
    classic_id, classic = run(db, "Clássica", 1, CLASSIC)
    conceptual_id, conceptual = run(db, "Conceitual", 2, CONCEPTUAL)

    assert [o.status for o in classic] == ["applied"] * 10 + ["rejected"]
    assert classic[9].result["death"]["mode"] == "permanent"  # 6 - 10 = 0: o orc morreu de vez
    assert [o.status for o in conceptual] == ["applied"] * 8 + ["rejected", "applied"]
    assert conceptual[6].result["success"] is False and conceptual[6].result["difficulty"] == "1000"
    assert conceptual[9].result["death"]["mode"] == "reincarnation"

    with db.transaction() as session:
        a = CampaignData(session, classic_id)
        b = CampaignData(session, conceptual_id)
        aria = a.entities.player()
        sem_nome = b.entities.player()
        assert {x.definition_key: x.value for x in a.attributes.for_entity(aria.id)} == {"forca": "8", "mana": "7", "vida": "20"}
        assert {x.definition_key: x.value for x in b.attributes.for_entity(sem_nome.id)}["rank"] == "S"
        assert b.attributes.get_for(sem_nome.id, "destino").value == "quebrar a roda do tempo"
        assert sem_nome.status == "dead" and sem_nome.data["reincarnation_pending"] is True
        # Cada campanha só enxerga as próprias regras.
        assert {d.key for d in a.definitions.list_current()} == {"forca", "vida", "mana", "bola_de_fogo", "morte"}
        assert {d.key for d in b.definitions.list_current()} == {"rank", "destino", "existencia", "ciclo"}
        assert a.definitions.current("attribute", "rank") is None
        assert b.definitions.current("skill", "bola_de_fogo") is None
