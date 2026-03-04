# OpenClaw Mission Control — Coolify Fork

[![CI](https://github.com/abhi1693/openclaw-mission-control/actions/workflows/ci.yml/badge.svg)](https://github.com/abhi1693/openclaw-mission-control/actions/workflows/ci.yml)
[![Coolify Ready](https://img.shields.io/badge/Coolify-Ready-blue?style=flat)](https://coolify.io)
[![Join Slack](https://img.shields.io/badge/Join-Slack-active?style=flat&color=blue&link=https%3A%2F%2Fjoin.slack.com%2Ft%2Foc-mission-control%2Fshared_invite%2Fzt-3qpcm57xh-AI9C~smc3MDBVzEhvwf7gg)](https://join.slack.com/t/oc-mission-control/shared_invite/zt-3qpcm57xh-AI9C~smc3MDBVzEhvwf7gg)

> **🚀 Coolify-Optimized Fork** — Deploy OpenClaw Mission Control on Coolify in 5 minutes with zero Docker knowledge required.

---

## 🎯 What is This Fork?

This is a **Coolify-optimized fork** of the original [OpenClaw Mission Control](https://github.com/abhi1693/openclaw-mission-control) project.

### Original vs This Fork

| Feature | Original Repo | This Fork (Coolify) |
|---------|---------------|---------------------|
| **Deployment** | Docker Compose CLI | Coolify UI (no CLI needed) |
| **Target User** | DevOps engineers | Anyone (no Docker knowledge) |
| **Setup Time** | 30-60 minutes | 5 minutes |
| **SSL/TLS** | Manual (Certbot, etc.) | Automatic (Let's Encrypt) |
| **Database** | Self-managed PostgreSQL | Coolify-managed PostgreSQL |
| **Reverse Proxy** | Manual (Traefik, Nginx) | Coolify Traefik (auto-configured) |
| **Environment Variables** | `.env` file editing | Coolify UI form |
| **Updates** | Manual `git pull` + rebuild | Coolify auto-deploy on push |
| **Monitoring** | Manual setup | Built-in Coolify dashboards |
| **Backups** | Manual scripts | Coolify automated backups |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Coolify Platform                           │
│  (Self-hosted PaaS on your VPS: Hetzner, DigitalOcean, AWS...) │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Mission Control Stack                        │ │
│  │                                                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │   Frontend   │  │   Backend    │  │    Worker    │   │ │
│  │  │   Next.js    │  │   FastAPI    │  │   RQ Queue   │   │ │
│  │  │   :3000      │  │   :8000      │  │              │   │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘   │ │
│  │         │                  │                              │ │
│  │         └────────┬─────────┘                              │ │
│  │                  │                                        │ │
│  │         ┌────────▼─────────┐                              │ │
│  │         │     Caddy Proxy   │                              │ │
│  │         │   (Path routing)  │                              │ │
│  │         └────────┬─────────┘                              │ │
│  └──────────────────┼────────────────────────────────────────┘ │
│                     │                                          │
│         ┌───────────▼───────────┐                              │
│         │   Coolify Traefik     │                              │
│         │   (TLS termination)   │                              │
│         └───────────┬───────────┘                              │
│                     │                                          │
└─────────────────────┼──────────────────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │   Your Domain (HTTPS)   │
         │  mission-control.you.com│
         └─────────────────────────┘
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- A **Coolify instance** (self-hosted on any VPS)
  - Install: `curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash`
- A **domain name** with DNS pointing to your Coolify server
- An **OpenClaw Gateway** already deployed (native Coolify service)

### Step 1: Add as Docker Compose Resource

1. In Coolify UI, go to your project
2. Click **"+ Add Resource"** → **"Docker Compose"**
3. Paste this repository URL or upload `docker-compose.yml`

### Step 2: Configure Environment Variables

In Coolify → Environment Variables tab, set:

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Database password (strong random) | `openssl rand -hex 32` |
| `LOCAL_AUTH_TOKEN` | Auth token (≥50 characters) | `openssl rand -hex 32` |
| `OPENCLAW_GATEWAY_URL` | OpenClaw Gateway internal URL | `http://openclaw-<uuid>:18789` |
| `OPENCLAW_TOKEN` | Gateway token from OpenClaw env vars | From OpenClaw service |
| `CORS_ORIGINS` | Your public domain | `https://mission-control.you.com` |
| `NEXT_PUBLIC_API_URL` | Your public domain (same as CORS) | `https://mission-control.you.com` |
| `NEXT_PUBLIC_AUTH_MODE` | Auth mode: `local` or `clerk` | `local` |

### Step 3: Deploy

1. Click **"Deploy"** in Coolify UI
2. Wait for all services to turn green (healthy)
3. Open your domain: `https://mission-control.you.com`

### Step 4: Connect to OpenClaw Gateway

1. In Mission Control UI → Settings → Gateways
2. Add your OpenClaw Gateway URL and token
3. Test connection
4. Start provisioning agents!

---

## 🔧 Configuration Reference

### Required Variables

```bash
# Database
POSTGRES_PASSWORD=<strong-random-password>

# Authentication
AUTH_MODE=local
LOCAL_AUTH_TOKEN=<openssl-rand-hex-32>  # Must be ≥50 characters

# OpenClaw Gateway (CRITICAL)
OPENCLAW_GATEWAY_URL=http://openclaw-<container-uuid>:18789
OPENCLAW_TOKEN=<gateway-token-from-env-vars>

# Frontend (must match your Coolify FQDN)
CORS_ORIGINS=https://mission-control.you.com
NEXT_PUBLIC_API_URL=https://mission-control.you.com
NEXT_PUBLIC_AUTH_MODE=local
```

### Optional Variables

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text
REQUEST_LOG_SLOW_MS=1000

# Queue / Worker
RQ_QUEUE_NAME=default
RQ_DISPATCH_THROTTLE_SECONDS=2.0
RQ_DISPATCH_MAX_RETRIES=3

# Database migration (default: true)
DB_AUTO_MIGRATE=true
```

---

## 🔗 Finding Your OpenClaw Gateway URL

This is the **most common issue**. Here's how to find the correct URL:

### Method 1: Coolify UI

1. Go to your **OpenClaw service** in Coolify
2. Click on the service → **"Container"** tab
3. Copy the **Container Name** (e.g., `openclaw-l4gc8o4k4s4scw488g0wcw4g`)
4. Use: `http://<container-name>:18789`

### Method 2: Docker CLI

```bash
# SSH to your Coolify server
ssh root@your-server.com

# List OpenClaw containers
docker ps --format "table {{.Names}}\t{{.Status}}" | grep openclaw

# Use the container name in the URL
# Example: http://openclaw-l4gc8o4k4s4scw488g0wcw4g:18789
```

### Method 3: Find Gateway Token

1. In Coolify → OpenClaw service → **Environment Variables**
2. Look for `OPENCLAW_GATEWAY_TOKEN` or `SERVICE_PASSWORD_64_GATEWAYTOKEN`
3. Copy the value → Paste in Mission Control `OPENCLAW_TOKEN`

---

## 🆚 Differences from Upstream

This fork maintains **100% compatibility** with the upstream while adding Coolify-specific optimizations:

### What Changed

| File | Change | Reason |
|------|--------|--------|
| `docker-compose.yml` | Removed hardcoded domains, added Coolify FQDN support | Coolify auto-injects `SERVICE_FQDN_*` variables |
| `.env.example` | Generic placeholders instead of Moiria domains | Make repo reusable by anyone |
| `README.md` | Complete rewrite with Coolify focus | Help non-Docker users deploy |
| `proxy/Caddyfile` | Path-based routing for Coolify Traefik | Single entry point for HTTPS |
| `backend/Dockerfile` | Optimized for Coolify build context | Faster builds on Coolify |
| `frontend/Dockerfile` | Build args for Coolify env vars | NEXT_PUBLIC_* vars at build time |

### What Stayed the Same

- ✅ **All backend code** — Identical to upstream
- ✅ **All frontend code** — Identical to upstream
- ✅ **Database schema** — Fully compatible
- ✅ **API endpoints** — 100% compatible
- ✅ **Agent provisioning** — Same workflow
- ✅ **Authentication** — Same auth modes (local/clerk)

### Why Fork Instead of PR?

- Coolify-specific deployment workflow
- Different networking model (Coolify networks vs Docker networks)
- Environment variable injection via Coolify UI (not `.env` files)
- Traefik + Caddy double-proxy architecture (Coolify requirement)

---

## 🛠️ Troubleshooting

### "Cannot connect to OpenClaw Gateway"

**Most common issue.** Check:

1. **Network connectivity** — Mission Control must be on the same Docker network as OpenClaw
   ```bash
   # In Coolify → Mission Control → Networks
   # Connect to OpenClaw's Docker network
   ```

2. **Correct container name** — Use the full container name with UUID
   ```bash
   # Wrong: http://openclaw:18789
   # Right: http://openclaw-l4gc8o4k4s4scw488g0wcw4g:18789
   ```

3. **Gateway token** — Must match exactly from OpenClaw env vars

### "CORS error" in browser console

Set `CORS_ORIGINS` to your **exact** Coolify FQDN:
```bash
CORS_ORIGINS=https://mission-control.you.com
```

### "LOCAL_AUTH_TOKEN must be at least 50 characters"

Generate a proper token:
```bash
openssl rand -hex 32
# Output: 64 characters (safe)
```

### Frontend can't reach backend

Check `NEXT_PUBLIC_API_URL` — must be your **public domain**, not internal URL:
```bash
# Wrong: http://backend:8000
# Right: https://mission-control.you.com
```

---

## 📚 Documentation

- **Original Upstream Docs:** [github.com/abhi1693/openclaw-mission-control](https://github.com/abhi1693/openclaw-mission-control)
- **Coolify Docs:** [coolify.io/docs](https://coolify.io/docs)
- **OpenClaw Docs:** [openclaw.ai/docs](https://openclaw.ai/docs)

### This Repo

- `docs/` — Contributor and operations docs
- `backend/` — FastAPI backend code
- `frontend/` — Next.js frontend code
- `proxy/` — Caddy reverse proxy configuration

---

## 🤝 Contributing

This fork welcomes contributions! Please:

1. **Sync with upstream** regularly to stay compatible
2. **Test on Coolify** before submitting PRs
3. **Document Coolify-specific** changes clearly
4. **Keep generic defaults** in `.env.example`

### Reporting Issues

- **Coolify deployment issues** → Open issue on this fork
- **Backend/Frontend bugs** → Open issue on upstream repo
- **OpenClaw Gateway issues** → Open issue on OpenClaw repo

---

## 📄 License

Same as upstream: **MIT License**

See [LICENSE](./LICENSE) for details.

---

## 🙏 Credits

- **Original Project:** [OpenClaw Mission Control](https://github.com/abhi1693/openclaw-mission-control) by @abhi1693
- **Coolify Platform:** [Coolify](https://coolify.io) by @coollabsio
- **OpenClaw:** [OpenClaw](https://openclaw.ai) by @openclaw

This fork exists to make OpenClaw Mission Control accessible to everyone, not just Docker experts.

---

**Ready to deploy?** → Follow the [Quick Start](#-quick-start-5-minutes) above!
