from abc import ABC, abstractmethod
from datetime import UTC, datetime
from hashlib import sha1

import httpx

from worldcup_model.data.live.schemas import FixtureStatus, LiveFixture, LiveIngestResult
from worldcup_model.data.live.timeparse import parse_openfootball_datetime


class LiveFixtureProvider(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> LiveIngestResult:
        raise NotImplementedError


class OpenFootballWorldCupProvider(LiveFixtureProvider):
    name = "openfootball-worldcup-json"

    def __init__(
        self,
        url: str = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    def fetch(self) -> LiveIngestResult:
        response = httpx.get(self.url, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        fixtures = [self._fixture_from_match(payload["name"], item) for item in payload.get("matches", [])]
        return LiveIngestResult(
            provider=self.name,
            fetched_at=datetime.now(UTC),
            fixtures=fixtures,
            warnings=[],
        )

    def _fixture_from_match(self, tournament: str, item: dict) -> LiveFixture:
        source_match_id = str(
            item.get("num")
            or sha1(
                "|".join(
                    [
                        item.get("date", ""),
                        item.get("time", ""),
                        item.get("team1", ""),
                        item.get("team2", ""),
                        item.get("round", ""),
                    ]
                ).encode()
            ).hexdigest()[:16]
        )
        score = item.get("score") or {}
        return LiveFixture(
            source=self.name,
            source_match_id=source_match_id,
            date=parse_openfootball_datetime(item["date"], item.get("time")),
            tournament=tournament,
            stage=item.get("round", "Unknown"),
            group_name=item.get("group"),
            home_team=item.get("team1", "TBD"),
            away_team=item.get("team2", "TBD"),
            neutral=True,
            venue=item.get("ground"),
            city=item.get("ground"),
            home_score=score.get("ft", [None, None])[0] if isinstance(score.get("ft"), list) else None,
            away_score=score.get("ft", [None, None])[1] if isinstance(score.get("ft"), list) else None,
            status=FixtureStatus.finished if score else FixtureStatus.scheduled,
            raw=item,
        )


class FootballDataWorldCupProvider(LiveFixtureProvider):
    name = "football-data-org"

    def __init__(
        self,
        api_token: str,
        base_url: str = "https://api.football-data.org/v4",
        competition_code: str = "WC",
        timeout_seconds: float = 20.0,
    ) -> None:
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self.competition_code = competition_code
        self.timeout_seconds = timeout_seconds

    def fetch(self) -> LiveIngestResult:
        response = httpx.get(
            f"{self.base_url}/competitions/{self.competition_code}/matches",
            headers={"X-Auth-Token": self.api_token},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        fixtures = [self._fixture_from_match(item) for item in payload.get("matches", [])]
        return LiveIngestResult(
            provider=self.name,
            fetched_at=datetime.now(UTC),
            fixtures=fixtures,
            warnings=[],
        )

    def _fixture_from_match(self, item: dict) -> LiveFixture:
        status = _football_data_status(item.get("status"))
        full_time = (item.get("score") or {}).get("fullTime") or {}
        home_team = item.get("homeTeam") or {}
        away_team = item.get("awayTeam") or {}
        competition = item.get("competition") or {}
        return LiveFixture(
            source=self.name,
            source_match_id=str(item["id"]),
            date=datetime.fromisoformat(item["utcDate"].replace("Z", "+00:00")).astimezone(UTC),
            tournament=competition.get("name") or "World Cup 2026",
            stage=item.get("stage") or item.get("matchday") or "Unknown",
            group_name=item.get("group"),
            home_team=home_team.get("name") or home_team.get("shortName") or "TBD",
            away_team=away_team.get("name") or away_team.get("shortName") or "TBD",
            neutral=True,
            venue=item.get("venue"),
            home_score=full_time.get("home"),
            away_score=full_time.get("away"),
            status=status,
            raw=item,
        )


def _football_data_status(value: str | None) -> FixtureStatus:
    match value:
        case "SCHEDULED" | "TIMED":
            return FixtureStatus.scheduled
        case "IN_PLAY" | "PAUSED":
            return FixtureStatus.live
        case "FINISHED":
            return FixtureStatus.finished
        case "POSTPONED":
            return FixtureStatus.postponed
        case _:
            return FixtureStatus.unknown
