"""Mede o desempenho com uma campanha grande (Etapa 7.4). Usa a IA falsa: mede só o motor e o banco.

Uso (na pasta backend):  .venv/Scripts/python.exe scripts/benchmark_large_campaign.py [npcs] [turnos]
Cria tudo numa pasta temporária em .tmp/ (no projeto); não toca no banco real do jogo.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import event  # noqa: E402

from app import create_app  # noqa: E402
from app.ai.context.game_state import build_game_state  # noqa: E402
from app.ai.orchestrator.simulation import WorldSimulation  # noqa: E402
from app.config import PROJECT_ROOT, load_settings  # noqa: E402
from app.engine.operations.context import OperationContext  # noqa: E402
from app.engine.operations.pipeline import apply_operations  # noqa: E402
from app.persistence.repositories import CampaignData  # noqa: E402
from app.persistence.snapshots import export_campaign  # noqa: E402

BATCH = 50
PLACES = 20
NPCS_AT_PLAYER_LOCATION = 40


class QueryCounter:
    def __init__(self, engine):
        self.count = 0
        event.listen(engine, "before_cursor_execute", self._on_query)

    def _on_query(self, *_args):
        self.count += 1


results: list[tuple[str, float, int]] = []


@contextmanager
def measure(name: str, counter: QueryCounter):
    before, started = counter.count, time.perf_counter()
    yield
    results.append((name, (time.perf_counter() - started) * 1000, counter.count - before))


def apply_in_batches(services, campaign_id: str, operations: list[dict]) -> None:
    for start in range(0, len(operations), BATCH):
        with services.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            ctx = OperationContext(data, source="system", campaign_seed=data.campaign().rng_seed,
                                   world_time=data.campaign().world_clock)
            outcomes = apply_operations(ctx, operations[start:start + BATCH])
            rejected = [o for o in outcomes if o.status == "rejected"]
            if rejected:
                raise SystemExit(f"Operação recusada ao montar a campanha: {rejected[0].op}: {rejected[0].reason}")


def populate(services, campaign_id: str, npcs: int) -> None:
    definitions = [{"op": "definition.create", "kind": "attribute", "key": key, "data": {"name": key}}
                   for key in ("forca", "destreza", "mente", "presenca")]
    definitions.append({"op": "definition.create", "kind": "attribute", "key": "vida",
                        "data": {"name": "Vida", "resource": True}})
    definitions.append({"op": "definition.create", "kind": "item", "key": "moeda", "data": {"name": "Moeda"}})
    places = [{"op": "entity.create", "ref": f"lugar_{n}", "kind": "location", "name": f"Lugar {n}"}
              for n in range(PLACES)]
    apply_in_batches(services, campaign_id, definitions + places)

    with services.db.transaction() as session:
        data = CampaignData(session, campaign_id)
        place_ids = [e.id for e in data.entities.list() if e.kind == "location"]
    player = [{"op": "entity.create", "kind": "character", "name": "Heroína", "is_player": True,
               "location": place_ids[0], "attributes": {"forca": 5, "vida": {"value": 10, "max": 10}}}]
    apply_in_batches(services, campaign_id, player)

    operations = []
    for n in range(npcs):
        place = place_ids[0] if n < NPCS_AT_PLAYER_LOCATION else place_ids[n % PLACES]
        operations.append({"op": "entity.create", "ref": f"npc_{n}", "kind": "character", "name": f"NPC {n}",
                           "location": place, "sim_tier": 1 if n % 10 == 0 else 2,
                           "data": {"personality": "desconfiado e curioso", "goal": "sobreviver ao inverno"},
                           "attributes": {"forca": n % 7, "vida": {"value": 8, "max": 8}}})
    apply_in_batches(services, campaign_id, operations)

    with services.db.transaction() as session:
        data = CampaignData(session, campaign_id)
        npc_ids = [e.id for e in data.entities.list() if e.kind == "character" and not e.is_player]
    social = []
    for n, npc_id in enumerate(npc_ids):
        social.append({"op": "relationship.change", "source": npc_id, "target": "player",
                       "changes": {"confianca": n % 5}, "cause": "encontro na estrada"})
        social.append({"op": "knowledge.record", "observer": npc_id, "subject": "player", "field": "nome",
                       "value": "Heroína", "source": "ouviu"})
        social.append({"op": "memory.record", "entity": npc_id, "content": f"Viu a Heroína no dia {n}.",
                       "importance": 1 + n % 5})
        social.append({"op": "item.create", "key": "moeda", "quantity": 1 + n % 20, "owner": npc_id})
    social += [{"op": "canon.assert", "key": f"fato_{n}", "subject": "mundo", "statement": f"Fato do mundo número {n}."}
               for n in range(150)]
    social += [{"op": "quest.create", "key": f"missao_{n}", "title": f"Missão {n}",
                "objectives": ["ir", "voltar"]} for n in range(30)]
    apply_in_batches(services, campaign_id, social)


def play_turns(services, campaign_id: str, turns: int) -> None:
    for n in range(turns):
        services.provider.queue(json.dumps({"intent": "agir", "operations": []}),
                                f"Narração do turno {n}. " + "O vento sopra sobre a vila. " * 20)
        prepared = services.turns.prepare(services.local_user_id, campaign_id, str(uuid.uuid4()),
                                          f"Ação {n}: converso com os moradores.")
        list(services.turns.run(prepared))


def main() -> None:
    npcs = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    turns = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    work_dir = PROJECT_ROOT / ".tmp"  # fora do disco C:
    work_dir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work_dir, prefix="benchmark-", ignore_cleanup_errors=True) as tmp:
        settings = load_settings(environ={
            "APP_ENV": "test", "DATA_DIR": tmp, "AI_PROVIDER": "fake", "AI_MODEL": "fake-model",
            "AI_MECHANICS": "true", "AI_SIMULATION_MINUTES": "0", "AI_SUMMARY_EVERY": "0",
            "AUTO_SNAPSHOT_EVERY": "10000",  # conta os turnos, mas nunca grava
        }, env_file=None)
        services = create_app(settings).extensions["rpg_engine"]
        counter = QueryCounter(services.db.engine)
        campaign_id = services.campaigns.create(services.local_user_id, "Grande", "Teste de desempenho", [])["id"]
        started = time.perf_counter()
        populate(services, campaign_id, npcs)
        print(f"Campanha montada em {time.perf_counter() - started:.1f} s")
        started = time.perf_counter()
        play_turns(services, campaign_id, turns)
        print(f"{turns} turnos jogados em {time.perf_counter() - started:.1f} s")

        with services.db.transaction() as session:
            data = CampaignData(session, campaign_id)
            print(f"Eventos: {len(data.events.list_ordered())}, mensagens: {len(data.messages.list_ordered())}")
            with measure("estado do jogo para a IA (build_game_state)", counter):
                state = build_game_state(data)
            print(f"Estado do jogo: {len(state.text)} caracteres (~{len(state.text) // 4} tokens)")
            with measure("NPCs para a simulação do mundo", counter):
                WorldSimulation._relevant_npcs(data)
            with measure("exportar snapshot", counter):
                export_campaign(session, campaign_id)

        owner = services.local_user_id
        with measure("histórico completo (abrir a campanha)", counter):
            services.campaigns.history(owner, campaign_id)
        with measure("ficha", counter):
            services.sheets.sheet(owner, campaign_id)
        with measure("personagens conhecidos", counter):
            services.known.known(owner, campaign_id)
        with measure("mapa, diário e laços", counter):
            services.journal.journal(owner, campaign_id)
        with measure("cópia automática (conta turnos)", counter):
            services.auto_backup.after_turn(campaign_id)
        with measure("um turno completo (IA falsa)", counter):
            play_turns(services, campaign_id, 1)

        print(f"\n{'tempo (ms)':>11} {'consultas':>10}  o quê")
        for name, ms, queries in results:
            print(f"{ms:11.1f} {queries:10d}  {name}")
        services.db.dispose()


if __name__ == "__main__":
    main()
