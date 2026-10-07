# Kort

## Stack

- **Backend**: Django + Django REST Framework, Postgres. One app (`core`): `POST /api/links/` creates a short link (anonymous, rate-limited, valid for 1 year), `GET /<code>` redirects to it, `GET /api/health/` for monitoring.
- **Frontend**: React + TypeScript, built with Vite. Plain CSS, no CSS-in-JS. A repository layer (`src/repositories/`) owns all `fetch()` calls.
- **Deployment**: Docker Compose on a VPS. Django serves the built frontend directly (via WhiteNoise) alongside the API. Cloudflare Tunnel handles HTTPS and routing to the box.

## Running locally

```bash
cp .env.example .env   # fill in real values
docker compose up
```

- Frontend (Vite dev server): [http://localhost:5173](http://localhost:5173)
- Backend directly: [http://localhost:8000](http://localhost:8000)

The dev frontend proxies `/api` to the Django container, so the browser only ever talks to `localhost:5173`.

## Tests

Backend only:

```bash
cd backend
pytest
```

Runs against SQLite (no Postgres needed, see `config/settings.py`'s `DATABASE_URL` fallback). CI runs the same thing on every push to `main` via `.github/workflows/ci.yml`, and only deploys if it passes.

## Deployment

Push to `main`: CI runs the test suite and, on success, SSHs into the VPS to `git pull` and rebuild via `docker-compose.prod.yml`. See `backend/Dockerfile.prod` for the production image (multi-stage: builds the frontend, bakes it into the Django image) and `deploy/backup-db.sh` for the daily Postgres backup (cron'd on the VPS, not run by CI).

First-time VPS setup:

1. Clone the repo on the VPS and create `.env` from `.env.prod.example`. Pick an available `WEB_PORT` and `DB_PORT`.
2. Add a public hostname to the Cloudflare Tunnel pointing at `http://localhost:<WEB_PORT>`.
3. Set the GitHub secrets `VPS_HOST`, `VPS_USER`, `VPS_DEPLOY_KEY`, `VPS_DEPLOY_PATH`.
4. Add the backup crontab line (see `deploy/backup-db.sh`).
