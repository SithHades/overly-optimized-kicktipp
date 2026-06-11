from sqlalchemy import create_engine, text

from worldcup_model.data.live.schemas import LiveFixture


def upsert_fixtures(database_url: str, fixtures: list[LiveFixture]) -> int:
    engine = create_engine(database_url)
    upserted = 0
    with engine.begin() as connection:
        _ensure_live_schema(connection)
        for fixture in fixtures:
            home_team_id = _upsert_team(connection, fixture.home_team)
            away_team_id = _upsert_team(connection, fixture.away_team)
            connection.execute(
                text(
                    """
                    INSERT INTO matches (
                      source, source_match_id, date, tournament, stage, group_name,
                      home_team_id, away_team_id, neutral, venue, city, country,
                      home_score, away_score, status
                    )
                    VALUES (
                      :source, :source_match_id, :date, :tournament, :stage, :group_name,
                      :home_team_id, :away_team_id, :neutral, :venue, :city, :country,
                      :home_score, :away_score, :status
                    )
                    ON CONFLICT (source, source_match_id)
                    DO UPDATE SET
                      date = excluded.date,
                      tournament = excluded.tournament,
                      stage = excluded.stage,
                      group_name = excluded.group_name,
                      home_team_id = excluded.home_team_id,
                      away_team_id = excluded.away_team_id,
                      neutral = excluded.neutral,
                      venue = excluded.venue,
                      city = excluded.city,
                      country = excluded.country,
                      home_score = excluded.home_score,
                      away_score = excluded.away_score,
                      status = excluded.status
                    """
                ),
                {
                    "source": fixture.source,
                    "source_match_id": fixture.source_match_id,
                    "date": fixture.date,
                    "tournament": fixture.tournament,
                    "stage": fixture.stage,
                    "group_name": fixture.group_name,
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id,
                    "neutral": fixture.neutral,
                    "venue": fixture.venue,
                    "city": fixture.city,
                    "country": fixture.country,
                    "home_score": fixture.home_score,
                    "away_score": fixture.away_score,
                    "status": fixture.status.value,
                },
            )
            upserted += 1
    return upserted


def _upsert_team(connection, team_name: str) -> int:
    result = connection.execute(
        text(
            """
            INSERT INTO teams (name)
            VALUES (:name)
            ON CONFLICT (name) DO UPDATE SET name = excluded.name
            RETURNING id
            """
        ),
        {"name": team_name},
    )
    return int(result.scalar_one())


def _ensure_live_schema(connection) -> None:
    for statement in [
        "CREATE EXTENSION IF NOT EXISTS pgcrypto",
        """
        CREATE TABLE IF NOT EXISTS teams (
          id serial PRIMARY KEY,
          fifa_code text,
          name text NOT NULL UNIQUE,
          aliases text[] DEFAULT '{}',
          confederation text,
          current_fifa_rank integer,
          current_elo double precision
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS matches (
          id serial PRIMARY KEY,
          source text,
          source_match_id text,
          date timestamptz,
          tournament text,
          stage text,
          group_name text,
          home_team_id integer REFERENCES teams(id),
          away_team_id integer REFERENCES teams(id),
          neutral boolean DEFAULT true,
          venue text,
          city text,
          country text,
          home_score integer,
          away_score integer,
          status text NOT NULL DEFAULT 'scheduled',
          UNIQUE (source, source_match_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date)",
        """
        CREATE TABLE IF NOT EXISTS model_runs (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          created_at timestamptz NOT NULL DEFAULT now(),
          git_sha text,
          train_data_until date,
          model_type text NOT NULL,
          metrics jsonb NOT NULL DEFAULT '{}',
          artifact_path text,
          is_active boolean NOT NULL DEFAULT false
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tournament_tips (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          phase text NOT NULL,
          question_key text NOT NULL,
          question_label text NOT NULL,
          answer jsonb NOT NULL,
          confidence double precision NOT NULL DEFAULT 0,
          generated_at timestamptz NOT NULL DEFAULT now(),
          model_version text NOT NULL DEFAULT 'historical-world-cup-elo-v1',
          source_state jsonb NOT NULL DEFAULT '{}',
          UNIQUE (phase, question_key)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_tournament_tips_phase ON tournament_tips(phase, generated_at DESC)",
    ]:
        connection.execute(text(statement))
