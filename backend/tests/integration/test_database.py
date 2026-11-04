from datetime import UTC, datetime, timedelta, timezone

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.auth.local_user import ensure_local_user
from app.persistence.db import Database
from app.persistence.migrations import alembic_config, upgrade_to_head
from app.persistence.models import Base, Campaign, Event, Message, Turn, User

EXPECTED_TABLES = {
    "users", "campaigns", "campaign_intro", "turns", "messages", "events", "ai_requests",
}
PLATFORM_TABLES = {"users", "campaigns"}


def make_campaign(session, title="Teste"):
    owner = ensure_local_user(session)
    campaign = Campaign(owner_id=owner.id, title=title, rng_seed=42)
    session.add(campaign)
    session.flush()
    return campaign


def test_migration_creates_all_tables(db):
    assert EXPECTED_TABLES <= set(inspect(db.engine).get_table_names())


def test_models_and_migrations_are_in_sync(db):
    """Se falhar: um modelo mudou sem migração. Gere uma com `alembic revision --autogenerate`."""
    with db.engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_downgrade_and_upgrade_again(tmp_path):
    url = "sqlite:///" + (tmp_path / "ida_e_volta.db").as_posix()
    upgrade_to_head(url)
    command.downgrade(alembic_config(url), "base")
    upgrade_to_head(url)
    database = Database(url)
    assert EXPECTED_TABLES <= set(inspect(database.engine).get_table_names())
    database.dispose()


def test_upgrade_is_safe_to_repeat(settings):
    upgrade_to_head(settings.database_url)
    upgrade_to_head(settings.database_url)


def test_sqlite_uses_wal_and_foreign_keys(db):
    with db.engine.connect() as connection:
        assert connection.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_every_game_table_has_required_campaign_id():
    """Regra inviolável: toda tabela de jogo tem campaign_id obrigatório ligado a campaigns."""
    for table in Base.metadata.sorted_tables:
        if table.name in PLATFORM_TABLES:
            continue
        column = table.columns.get("campaign_id")
        assert column is not None, f"{table.name} não tem campaign_id"
        assert not column.nullable, f"{table.name}.campaign_id aceita nulo"
        assert {fk.column.table.name for fk in column.foreign_keys} == {"campaigns"}


def test_transaction_rolls_back_everything_on_error(db):
    with pytest.raises(RuntimeError):
        with db.transaction() as session:
            make_campaign(session, "Não deve existir")
            raise RuntimeError("falha no meio")
    with db.transaction() as session:
        assert session.scalar(select(func.count()).select_from(Campaign)) == 0


def test_dates_are_stored_and_returned_in_utc(db):
    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=-3)))
    with db.transaction() as session:
        user = User(name="Fuso", created_at=moment)
        session.add(user)
    with db.transaction() as session:
        stored = session.get(User, user.id)
        assert stored.created_at == moment
        assert stored.created_at.tzinfo == UTC


def test_dates_without_timezone_are_rejected(db):
    with pytest.raises(Exception, match="fuso horário"):
        with db.transaction() as session:
            session.add(User(name="Sem fuso", created_at=datetime(2026, 1, 1)))


def test_turn_number_is_unique_per_campaign(db):
    with pytest.raises(IntegrityError):
        with db.transaction() as session:
            campaign = make_campaign(session)
            session.add(Turn(id="t1", campaign_id=campaign.id, number=1, player_input="a"))
            session.add(Turn(id="t2", campaign_id=campaign.id, number=1, player_input="b"))


def test_foreign_keys_are_enforced(db):
    with pytest.raises(IntegrityError):
        with db.transaction() as session:
            session.add(Turn(id="t1", campaign_id="campanha-inexistente", number=1, player_input="a"))


def test_deleting_campaign_removes_only_its_data(db):
    with db.transaction() as session:
        keep = make_campaign(session, "Fica")
        drop = make_campaign(session, "Sai")
        for campaign in (keep, drop):
            turn_id = f"turn-{campaign.title}"
            session.add(Turn(id=turn_id, campaign_id=campaign.id, number=1, player_input="oi"))
            session.flush()
            session.add(Message(campaign_id=campaign.id, turn_id=turn_id, seq=1, role="player", content="oi"))
            session.add(Event(campaign_id=campaign.id, turn_id=turn_id, type="t", source="system"))
    with db.transaction() as session:
        session.delete(session.get(Campaign, drop.id))
    with db.transaction() as session:
        for model in (Turn, Message, Event):
            rows = session.scalars(select(model)).all()
            assert [row.campaign_id for row in rows] == [keep.id]
