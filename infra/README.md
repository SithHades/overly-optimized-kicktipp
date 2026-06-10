# Infra

Local stack:

- `postgres`: prediction warehouse and model metadata
- `redis`: job state/cache placeholder
- `api`: FastAPI service
- `web`: Next.js app

Run:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Production target:

- Deploy through Coolify.
- Keep Postgres volume backups enabled.
- Postgres and Redis are internal-only in this compose file. They do not publish host ports unless you add `ports:` mappings back.
- If you use existing Coolify Postgres/Redis services instead of the bundled ones, remove or disable the `postgres`/`redis` services and set `DATABASE_URL` / `REDIS_URL` on `api`.
- If you keep the bundled services, set strong `POSTGRES_PASSWORD` and keep the `postgres-data` volume backed up.
- Set `NEXT_PUBLIC_API_BASE_URL` to the public API URL if the frontend starts calling the API from the browser.
- Set `CORS_ALLOW_ORIGINS` to the public frontend origin when API calls run from the browser.
- Set `FOOTBALL_DATA_API_TOKEN` and `INGEST_ADMIN_TOKEN` to random/secret values, then trigger live fixture ingest with:

```bash
curl -X POST "$API_URL/api/admin/ingest-fixtures" -H "X-Admin-Token: $INGEST_ADMIN_TOKEN"
```

You can also open `/admin/ingest` in the deployed web app, paste the same token, and run the ingest from the UI.
The first successful ingest creates the `pre_tournament` Tipps if they do not exist yet, then writes the latest `current` Tipps on every later ingest.

- Add Caddy or Traefik routing once domains are assigned.
- Add Windmill as a sibling stack or use an existing Windmill instance with job scripts from `ml/worldcup_model/jobs`.
