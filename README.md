# Kort

## Stack

- **Backend**: Django + Django REST Framework, Postgres. One app (`core`): `POST /api/links/` creates a short link (anonymous, rate-limited, expiring after 1 day to 1 year, guarded by Cloudflare Turnstile and Google Safe Browsing), `GET /<code>` redirects to it, `GET /api/health/` for monitoring.
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
5. Cron `purge_expired_links` and `check_links` (re-checks active links against Safe Browsing) daily, via `docker compose -f docker-compose.prod.yml exec -T web python manage.py <command>`.
6. Point Netdata's alerts somewhere: append `SEND_DISCORD`, `DISCORD_WEBHOOK_URL` and `SEND_EMAIL="NO"` (the box has no MTA, so mail fails silently) to `/etc/netdata/health_alarm_notify.conf`, then `sudo -u netdata /usr/libexec/netdata/plugins.d/alarm-notify.sh test sysadmin` to check delivery. `/etc/netdata/health.d/disks.conf` is a copy of the stock file warning at 80% instead of 90%: `/` is shared with the other apps on the VPS, so filling it takes them down too.
7. Add a Cloudflare rate limiting rule on `POST /api/links/`, scoped by `http.host`. It blocks bursts at the edge before they cost a Turnstile or Safe Browsing call; the per-IP hourly limit in `config/settings.py` is a separate, slower guard.

`WEB_CONCURRENCY` sets the gunicorn worker count (default 2, on a 2-vCPU box shared with other apps). Each worker runs 4 threads, because link creation blocks on two outbound HTTP calls.

To take down an abusive link: `python manage.py disable_link <code>` (same `exec` prefix).
