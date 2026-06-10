# Jobs

These modules are written to be callable from Windmill flows.

Planned flows:

- `daily_ingest_results`
- `hourly_ingest_odds`
- `daily_retrain_model`
- `post_match_update`
- `simulate_tournament`
- `generate_ai_previews`
- `monitor_model_drift`

Each job should return structured JSON so Windmill can store logs, drive alerts, and pass state between steps.

## Immediate Windmill Schedule

Use these as the first production schedules:

- `ingest_live_fixtures`: every 5 minutes during match windows, every 30 minutes otherwise.
- `predict`: after every successful fixture ingest.
- `generate_match_preview`: nightly and six hours before kickoff.

Required variables:

- `LIVE_FIXTURE_PROVIDER=openfootball` for no-key reference data.
- `LIVE_FIXTURE_PROVIDER=football-data` plus `FOOTBALL_DATA_API_TOKEN` for keyed live score updates.
- `DATABASE_URL` to upsert into Postgres.
- `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` for AI preview jobs.
