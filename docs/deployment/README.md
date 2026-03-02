# Deploying Mission Control on Coolify

This guide covers deploying Mission Control on a Coolify instance alongside an
existing OpenClaw service.

## Prerequisites

- A running Coolify instance (v4.x)
- A server connected to Coolify with Docker and Traefik
- An OpenClaw service already deployed on the same server
- A domain name pointed to the server (e.g. `mission-control.moiria.com`)

## Architecture Overview

Mission Control deploys as a **Docker Compose** resource with six services:

| Service | Role |
|---------|------|
| `proxy` | Caddy reverse proxy — single entry point, receives the FQDN |
| `db` | PostgreSQL 16 database |
| `redis` | Redis 7 for background queue |
| `backend` | FastAPI API server |
| `worker` | Background queue worker (lifecycle + webhooks) |
| `frontend` | Next.js web UI |

Caddy routes traffic internally:

- `/api/*`, `/health`, `/healthz`, `/readyz` → backend on port 8000
- Everything else → frontend on port 3000

## Step 1: Prepare OpenClaw Gateway

Mission Control communicates with OpenClaw via its gateway port (18789).
By default, the gateway only listens on localhost inside the container.

1. In Coolify, go to your **OpenClaw service** → **Environment Variables**
2. Add or change: `OPENCLAW_GATEWAY_BIND=network`
3. **Restart** the OpenClaw service
4. Note the **container name** (e.g. `openclaw-l4gc8o4k4s4scw488g0wcw4g`)
5. Note the **gateway token** (the value of `SERVICE_PASSWORD_64_GATEWAYTOKEN`)

## Step 2: Create the Mission Control Resource

1. In Coolify, go to your project → environment → **Add New Resource**
2. Select **Docker Compose**
3. Connect your GitHub repository (`lesmoires/openclaw-mission-control`)
4. Set the branch to `main` (or your deployment branch)
5. Set **Docker Compose Location** to `/docker-compose.yml`
6. Set **Base Directory** to `/`

## Step 3: Configure Environment Variables

In the Coolify UI, add these environment variables:

### Required

| Variable | Value | Notes |
|----------|-------|-------|
| `POSTGRES_PASSWORD` | Strong random password | Use Coolify's generate button |
| `AUTH_MODE` | `local` | Or `clerk` for Clerk auth |
| `LOCAL_AUTH_TOKEN` | Min 50 chars | `openssl rand -hex 32` |
| `CORS_ORIGINS` | `https://mission-control.moiria.com` | Your domain |
| `NEXT_PUBLIC_API_URL` | `https://mission-control.moiria.com` | Same domain, no `/api` suffix |
| `NEXT_PUBLIC_AUTH_MODE` | `local` | Must match `AUTH_MODE` |
| `OPENCLAW_GATEWAY_URL` | `http://openclaw-<container-name>:18789` | From Step 1 |
| `OPENCLAW_TOKEN` | Gateway token from Step 1 | |

### Optional

| Variable | Default | Notes |
|----------|---------|-------|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `text` | `text` or `json` |
| `RQ_DISPATCH_THROTTLE_SECONDS` | `2.0` | Queue processing interval |
| `RQ_DISPATCH_MAX_RETRIES` | `3` | Max retry attempts |

## Step 4: Assign the Domain

1. In the Coolify resource settings, find the **Domains** section
2. Assign your FQDN (e.g. `https://mission-control.moiria.com`) to the
   **proxy** service on port **80**
3. Coolify will auto-configure Traefik TLS termination

## Step 5: Connect Docker Networks

Mission Control needs to reach the OpenClaw container. In Coolify:

1. Go to Mission Control resource → **Settings** or **Networks**
2. Connect to the OpenClaw service's Docker network
   (the network name matches the OpenClaw service UUID)

## Step 6: Deploy

Click **Deploy** in Coolify. The first build takes several minutes as it:

1. Builds the backend Docker image (Python deps + app)
2. Builds the frontend Docker image (Node deps + Next.js build)
3. Pulls PostgreSQL, Redis, and Caddy images
4. Starts all containers
5. Backend auto-runs database migrations on first start

## Verifying the Deployment

After deployment completes:

- **Health check**: `curl https://mission-control.moiria.com/healthz`
  should return `{"ok": true}`
- **Frontend**: Visit `https://mission-control.moiria.com` in a browser
- **API docs**: Visit `https://mission-control.moiria.com/docs`

## Troubleshooting

### Build fails with "Dockerfile not found"

Ensure the **Docker Compose Location** is set to `/docker-compose.yml`
(not `/docker-compose.yaml` or another path).

### Frontend shows "NEXT_PUBLIC_API_URL is not set"

`NEXT_PUBLIC_API_URL` is baked at build time. If you added it after the
first build, trigger a **full rebuild** (not just restart).

### Backend can't reach OpenClaw gateway

1. Verify `OPENCLAW_GATEWAY_BIND=network` is set on the OpenClaw service
2. Verify the Docker networks are connected (Step 5)
3. Verify the container name in `OPENCLAW_GATEWAY_URL` is correct

### Database migration errors

Check backend logs in Coolify. The `DB_AUTO_MIGRATE=true` setting runs
Alembic migrations on startup. If migrations fail, the backend will not
start and the health check will fail.

## Updating

Push changes to the configured branch. If Coolify webhooks are set up,
it will auto-deploy. Otherwise, click **Deploy** manually.

**Important**: Changes to `NEXT_PUBLIC_*` variables require a full rebuild
since they are baked into the Next.js bundle at build time.
