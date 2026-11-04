"""Snapshot automático a cada N turnos, mantendo só os 5 automáticos mais recentes."""

import uuid

from app import create_app
from app.ai.orchestrator.events import TurnCompleted
from app.persistence.snapshots import list_snapshots, write_snapshot, export_campaign
from tests.conftest import make_settings


def test_every_n_turns_with_rotation(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template, AUTO_SNAPSHOT_EVERY="2"))
    services = application.extensions["rpg_engine"]
    campaign = services.campaigns.create(services.local_user_id, "Backup", None, [])
    with services.db.transaction() as session:  # um snapshot manual nunca é apagado pela rotação
        write_snapshot(services.settings.data_dir, export_campaign(session, campaign["id"]), "manual-importante")

    for n in range(1, 15):
        services.provider.queue(f"Narração {n}.")
        prepared = services.turns.prepare(services.local_user_id, campaign["id"], str(uuid.uuid4()), f"Ação {n}.")
        list(services.turns.run(prepared))

    labels = [s["label"] for s in list_snapshots(services.settings.data_dir, campaign["id"])]
    automatic = [label for label in labels if label.startswith("automatico")]
    assert automatic == [f"automatico-turno-{n}" for n in (14, 12, 10, 8, 6)]  # 7 criados, ficam os 5 últimos
    assert "manual-importante" in labels
    services.db.dispose()


def test_backup_failure_keeps_turn_and_summary(tmp_path, migrated_db_template, monkeypatch):
    application = create_app(make_settings(tmp_path, migrated_db_template, AUTO_SNAPSHOT_EVERY="1"))
    services = application.extensions["rpg_engine"]
    campaign = services.campaigns.create(services.local_user_id, "Falha", None, [])
    scheduled = []

    def broken(campaign_id):
        raise OSError("disco cheio")

    monkeypatch.setattr(services.auto_backup, "after_turn", broken)
    monkeypatch.setattr(services.summaries, "schedule", scheduled.append)
    services.provider.queue("Narração.")
    events = list(services.turns.run(services.turns.prepare(services.local_user_id, campaign["id"],
                                                            str(uuid.uuid4()), "Ação.")))
    assert isinstance(events[-1], TurnCompleted)
    assert scheduled == [campaign["id"]]
    services.db.dispose()


def test_disabled_with_zero(tmp_path, migrated_db_template):
    application = create_app(make_settings(tmp_path, migrated_db_template, AUTO_SNAPSHOT_EVERY="0"))
    services = application.extensions["rpg_engine"]
    campaign = services.campaigns.create(services.local_user_id, "Sem", None, [])
    services.provider.queue("n")
    list(services.turns.run(services.turns.prepare(services.local_user_id, campaign["id"], str(uuid.uuid4()), "a")))
    assert list_snapshots(services.settings.data_dir, campaign["id"]) == []
    services.db.dispose()
