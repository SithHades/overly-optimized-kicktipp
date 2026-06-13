from datetime import UTC, datetime, time

from worldcup_api.services import scheduled_ingest
from worldcup_api.services.scheduled_ingest import seconds_until_next_run, start_scheduled_ingest


def test_seconds_until_next_run_uses_today_when_time_is_future() -> None:
    now = datetime(2026, 6, 13, 5, 30, tzinfo=UTC)

    assert seconds_until_next_run(now, time(6, 0, tzinfo=UTC)) == 30 * 60


def test_seconds_until_next_run_uses_tomorrow_when_time_passed() -> None:
    now = datetime(2026, 6, 13, 6, 30, tzinfo=UTC)

    assert seconds_until_next_run(now, time(6, 0, tzinfo=UTC)) == 23.5 * 60 * 60


def test_scheduled_ingest_does_not_start_without_database(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SCHEDULED_INGEST_ENABLED", "true")

    assert start_scheduled_ingest() is None


def test_scheduled_ingest_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setenv("SCHEDULED_INGEST_ENABLED", "false")
    monkeypatch.setattr(scheduled_ingest.asyncio, "create_task", lambda _: (_ for _ in ()).throw(AssertionError()))

    assert start_scheduled_ingest() is None
