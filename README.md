# WorldCupQuant

Bloomberg Terminal-style football prediction workspace for World Cup simulations and Tipp-Spiel optimization.

The project is intentionally scaffolded around the real killer feature: choose picks that maximize expected points under a custom scoring system, rather than simply choosing the most likely scoreline.

## Stack

- Frontend: Next.js 15, Tailwind, shadcn-style local components, Recharts-ready structure
- API: FastAPI, Pydantic, SQLModel-ready layout
- ML: Python package for ingestion, Elo, Poisson score distributions, simulations, evaluation, and AI enrichment
- Jobs: Windmill-oriented scripts under `ml/worldcup_model/jobs`
- Data: Postgres, optional TimescaleDB for odds snapshots, Redis for job state/cache
- Deployment: Docker Compose, Caddy/Traefik-ready services
- AI: OpenRouter-compatible client skeleton with structured-output validation

## Repository Layout

```text
apps/
  web/        Next.js dashboard
  api/        FastAPI service
ml/
  worldcup_model/
    data/        ingestion, normalization, feature builders
    models/      Elo, Poisson, ensemble, calibration
    simulation/  group, knockout, tournament simulation
    evaluation/  metrics and backtests
    ai/          OpenRouter structured-output agents
    jobs/        Windmill-callable entrypoints
packages/
  shared-types/  generated/shared TypeScript contracts placeholder
infra/
  docker-compose.yml
  Dockerfile.api
  Dockerfile.web
data/
  sample/      tiny sample fixtures for local development
docs/
  plan.md      executable build plan and acceptance criteria
```

## Quickstart

Install dependencies, then run the API and web app:

```bash
pnpm install
uv sync --project apps/api
uv sync --project ml
pnpm dev
uv run --project apps/api uvicorn worldcup_api.main:app --reload --host 0.0.0.0 --port 8000
```

Or run the service stack:

```bash
docker compose -f infra/docker-compose.yml up --build
```

## Live Data

The app is wired for provider-based live ingestion.

No-key fixture/reference feed:

```bash
uv run --project ml python -m worldcup_model.jobs.ingest_live_fixtures
```

Keyed live provider:

```bash
LIVE_FIXTURE_PROVIDER=football-data FOOTBALL_DATA_API_TOKEN=... \
  uv run --project ml python -m worldcup_model.jobs.ingest_live_fixtures
```

The ingest job writes:

- `data/processed/live_fixtures.json` for backend/API reads
- `apps/web/public/live-fixtures.json` for the frontend live fixture feed
- Postgres `teams` and `matches` upserts when `DATABASE_URL` is set

AI match previews are OpenRouter-ready:

```bash
OPENROUTER_API_KEY=... \
  uv run --project ml python -m worldcup_model.jobs.generate_match_preview Germany Japan
```

## First Useful Loop

1. Ingest historical international results.
2. Normalize team IDs and aliases.
3. Train Elo baseline.
4. Fit Poisson goal model.
5. Produce per-match score distributions.
6. Optimize picks under Tipp-Spiel scoring rules.
7. Expose predictions through FastAPI.
8. Show match table and prediction detail in Next.js.

The detailed plan is in [docs/plan.md](docs/plan.md).
