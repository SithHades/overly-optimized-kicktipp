# WorldCupQuant Build Plan

## Product North Star

Build a prediction terminal for football tournaments whose primary advantage is Tipp-Spiel expected-points optimization. The model predicts distributions; the product converts those distributions into picks that match the user's scoring rules and leaderboard situation.

## Guiding Rules

- Deterministic math owns probabilities, scoring, calibration, and backtests.
- LLMs enrich, explain, audit, and summarize; they do not compute final probabilities.
- Every model must beat or explain failure against an Elo baseline.
- Exact-score argmax is not the Tipp recommendation unless it also maximizes expected score.
- All validation is time-split, never random-split.

## Milestone 1: Baseline Machine

Goal: a local prediction loop with sample fixtures.

Deliverables:

- Historical match ingestion contract.
- Team normalization tables and alias handling.
- Elo model skeleton.
- Poisson score-distribution model.
- Tipp-Spiel optimizer.
- `GET /api/matches/{id}/prediction`.
- Simple dashboard table with model probability and best Tipp.

Acceptance:

- API returns 1X2 probabilities, top scorelines, and recommended Tipp.
- Optimizer can be unit-tested independently from API and frontend.
- Frontend renders without needing Postgres or external APIs.

Current production-readiness status:

- Live fixture ingestion is provider-based.
- `openfootball` is the no-key fixture/reference provider.
- `football-data` is the keyed live-score provider hook.
- Ingest writes a local backend snapshot, frontend export, and optional Postgres upserts.
- API prediction reads the live snapshot before falling back to sample fixtures.
- OpenRouter structured-output preview jobs are scaffolded with web search enabled.

## Milestone 2: Tournament Simulator

Goal: simulate 2026 group and knockout paths.

Deliverables:

- Group stage simulation.
- FIFA 2026 advancement logic: top two plus eight best third-placed teams.
- Knockout simulation including penalties placeholder.
- Team-stage probability JSON.
- Bracket UI with probability overlays.

Acceptance:

- Simulation output includes group winner, advance, R32, R16, QF, SF, final, and winner probabilities.
- Most likely paths are materialized per team.

## Milestone 3: Data and Odds

Goal: make predictions market-aware and auditable.

Deliverables:

- Historical dataset ingestion.
- Live fixture ingestion adapters.
- Odds snapshot table and ingestion.
- Vig removal and implied-probability conversion.
- Champion/challenger model promotion checks.

Acceptance:

- Prediction payload distinguishes model, market, and blended probabilities.
- Model-market disagreements are queryable.

## Milestone 4: AI Layer

Goal: structured narrative and monitoring without polluting math.

Deliverables:

- OpenRouter structured-output client.
- Data quality auditor.
- Team scouting summarizer.
- Match preview writer.
- Post-match autopsy writer.

Acceptance:

- All LLM outputs are parsed through Pydantic models.
- Failed validation retries or stores a typed failure state.
- Source URLs are retained for scouting/news data.

## Milestone 5: Monitoring and Operations

Goal: run continuously during the tournament.

Deliverables:

- Windmill flows for ingest, retrain, simulate, previews, and drift checks.
- Model dashboard with log loss, Brier score, calibration, feature drift.
- Uptime and stale-data alerts.
- Telegram or Slack summary job.

Acceptance:

- Daily model health report is generated.
- New results trigger prediction and simulation refresh.
- Bad challenger models are retained but not promoted.

## Loop Protocol

Each implementation loop should:

1. Pick the next unchecked acceptance criterion.
2. Make the smallest coherent code change.
3. Add or update a focused test.
4. Run the relevant local check.
5. Record the result in this plan or a follow-up issue.

## Near-Term Backlog

- Replace baseline team-prior lambdas with historical ingestion from `martj42/international_results`.
- Add the preferred paid live-score provider key and run live ingest every 5-15 minutes.
- Add odds provider ingestion and market implied-probability conversion.
- Add persistent database models and Alembic migrations.
- Add a true Elo update pass with tournament importance weights.
- Add score-distribution calibration.
- Add group table simulator with deterministic tie-break helpers.
- Add `/leaderboard-optimizer` with custom scoring input.
- Add odds ingestion and vig removal.
- Add OpenRouter preview agent with strict JSON schema.
