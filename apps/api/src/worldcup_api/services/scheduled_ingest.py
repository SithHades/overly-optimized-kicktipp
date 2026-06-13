import asyncio
import logging
import os
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from worldcup_api.services.live_ingest import run_fixture_ingest

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScheduledIngestConfig:
    enabled: bool
    run_at_utc: time
    run_on_startup: bool
    provider: str | None


def scheduled_ingest_config() -> ScheduledIngestConfig:
    return ScheduledIngestConfig(
        enabled=_env_bool("SCHEDULED_INGEST_ENABLED", default=True),
        run_at_utc=time(
            hour=_env_int("SCHEDULED_INGEST_UTC_HOUR", default=6, minimum=0, maximum=23),
            minute=_env_int("SCHEDULED_INGEST_UTC_MINUTE", default=0, minimum=0, maximum=59),
            tzinfo=UTC,
        ),
        run_on_startup=_env_bool("SCHEDULED_INGEST_ON_STARTUP", default=False),
        provider=os.environ.get("SCHEDULED_INGEST_PROVIDER"),
    )


def start_scheduled_ingest() -> asyncio.Task[None] | None:
    config = scheduled_ingest_config()
    if not config.enabled:
        LOGGER.info("Scheduled fixture ingest is disabled.")
        return None

    if not os.environ.get("DATABASE_URL"):
        LOGGER.warning("Scheduled fixture ingest is disabled because DATABASE_URL is not configured.")
        return None

    provider = config.provider or os.environ.get("LIVE_FIXTURE_PROVIDER", "football-data")
    if provider == "football-data" and not os.environ.get("FOOTBALL_DATA_API_TOKEN"):
        LOGGER.warning("Scheduled fixture ingest is disabled because FOOTBALL_DATA_API_TOKEN is not configured.")
        return None

    task = asyncio.create_task(_scheduled_ingest_loop(config))
    LOGGER.info(
        "Scheduled fixture ingest enabled at %s UTC using provider %s.",
        config.run_at_utc.strftime("%H:%M"),
        provider,
    )
    return task


async def stop_scheduled_ingest(task: asyncio.Task[None] | None) -> None:
    if task is None:
        return

    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def _scheduled_ingest_loop(config: ScheduledIngestConfig) -> None:
    if config.run_on_startup:
        await _run_scheduled_ingest(config)

    while True:
        delay_seconds = seconds_until_next_run(datetime.now(UTC), config.run_at_utc)
        await asyncio.sleep(delay_seconds)
        await _run_scheduled_ingest(config)


async def _run_scheduled_ingest(config: ScheduledIngestConfig) -> None:
    provider = config.provider or os.environ.get("LIVE_FIXTURE_PROVIDER", "football-data")
    try:
        result = await asyncio.to_thread(run_fixture_ingest, provider)
    except Exception:
        LOGGER.exception("Scheduled fixture ingest failed.")
        return

    LOGGER.info(
        "Scheduled fixture ingest finished: provider=%s fixtures=%s upserts=%s tournament_tips=%s warnings=%s",
        result.provider,
        result.fixture_count,
        result.postgres_upserts,
        result.tournament_tip_count,
        result.warnings,
    )


def seconds_until_next_run(now: datetime, run_at_utc: time) -> float:
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    now = now.astimezone(UTC)
    target = datetime.combine(now.date(), run_at_utc, tzinfo=UTC)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    parsed = int(value)
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed
