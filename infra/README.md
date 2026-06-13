# Infra

Local stack:

- `postgres`: prediction warehouse and model metadata
- `redis`: job state/cache placeholder
- `api`: FastAPI service
- `web`: Next.js app

Run:

```bash
docker compose --project-directory . -f infra/docker-compose.yml -f infra/docker-compose.local.yml up --build
```

Production target:

- Deploy through Coolify.
- Use `infra/docker-compose.yml` as the Compose file path.
- Keep Postgres volume backups enabled.
- Postgres, Redis, API, and web are internal-only in the production compose file. Assign domains to `web` on container port `3000` and `api` on container port `8000` in Coolify.
- Keep host port mappings in `infra/docker-compose.local.yml` for local development only.
- If you use existing Coolify Postgres/Redis services instead of the bundled ones, remove or disable the `postgres`/`redis` services and set `DATABASE_URL` / `REDIS_URL` on `api`.
- If you keep the bundled services, set strong `POSTGRES_PASSWORD` and keep the `postgres-data` volume backed up.
- Set `NEXT_PUBLIC_API_BASE_URL` to the public API URL if the frontend starts calling the API from the browser.
- Set `CORS_ALLOW_ORIGINS` to the public frontend origin when API calls run from the browser.
- Set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` on the API service for AI previews. These must be runtime environment variables, not only build arguments. `OPENROUTER_USE_WEB_SEARCH=true` is the default so the preview can use current context for future fixtures. Web-search previews can take around two minutes, so keep `OPENROUTER_TIMEOUT_SECONDS` near the default `180`.
- Set `FOOTBALL_DATA_API_TOKEN` and `INGEST_ADMIN_TOKEN` to random/secret values, then trigger live fixture ingest with:

```bash
curl -X POST "$API_URL/api/admin/ingest-fixtures" -H "X-Admin-Token: $INGEST_ADMIN_TOKEN"
```

You can also open `/admin/ingest` in the deployed web app, paste the same token, and run the ingest from the UI.
The first successful ingest creates the `pre_tournament` Tipps if they do not exist yet, then writes the latest `current` Tipps on every later ingest.
- The API also runs the same fixture ingest once per day by default when `DATABASE_URL` and the selected provider credentials are configured.
  - `SCHEDULED_INGEST_ENABLED=true` enables it; set this to `false` to disable API-side scheduling.
  - `SCHEDULED_INGEST_UTC_HOUR=6` and `SCHEDULED_INGEST_UTC_MINUTE=0` control the daily run time.
  - `SCHEDULED_INGEST_ON_STARTUP=false` avoids a write-heavy ingest on every deploy; set it to `true` only if you want an immediate run after container start.
  - `SCHEDULED_INGEST_PROVIDER` can override `LIVE_FIXTURE_PROVIDER` for scheduled runs.

- Add Caddy or Traefik routing once domains are assigned.
- Add Windmill as a sibling stack or use an existing Windmill instance with job scripts from `ml/worldcup_model/jobs`.
