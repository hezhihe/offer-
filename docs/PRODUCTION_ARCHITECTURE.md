# Offer Compass Production Architecture

Last updated: 2026-06-03

## Final Deployment Decision

The production backend is Railway.

Reason: during the MVP online phase, Render's free-tier cold start made the system response too slow for demo use, so the backend was moved to Railway.

Evidence in this repository and current online checks:

- `backend/railway.toml` defines the Railway FastAPI deployment command and health check.
- `frontend/netlify.toml` proxies `/api/*` to `https://offer-compass-api-production.up.railway.app/api/:splat`.
- `https://offer-compass-api-production.up.railway.app/api/jobs` returns `200`.
- `https://offer-compass-api-production.up.railway.app/docs` returns the FastAPI docs page.
- The root `render.yaml` is historical / fallback configuration, not the current production source of truth.

Do not run Render and Railway as parallel production backends for the same frontend. That creates split logs, split environment variables, unclear incident ownership, and misleading deploy results.

## Production Topology

```text
Browser
  |
  | https://<netlify-site>/api/*
  v
Netlify frontend
  |
  | redirect proxy
  v
Railway backend
  |
  | supabase-py
  v
Supabase PostgreSQL and Storage

Railway backend
  |
  | requests
  v
DeepSeek API
```

## Frontend

Platform: Netlify

Build settings:

| Setting | Value |
| --- | --- |
| Base directory | `frontend` |
| Build command | `npm run build` |
| Publish directory | `dist` |
| Production API base | `/api` |

Required frontend environment variable:

| Variable | Value |
| --- | --- |
| `VITE_API_BASE_URL` | `/api` |

Reason: the built Vue app should call a same-origin API path. Netlify then forwards that path to the real Railway API. This avoids hardcoding backend domains in Vue bundles and keeps future backend domain changes inside Netlify config.

## Backend

Platform: Railway

Service settings are defined in `backend/railway.toml`:

| Setting | Value |
| --- | --- |
| Builder | `RAILPACK` |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/api/jobs` |
| Restart policy | `on_failure` |

Production backend URL:

```text
https://offer-compass-api-production.up.railway.app
```

Required backend environment variables:

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key, server-side only |
| `API_SECRET_KEY` | JWT signing secret |
| `CORS_ORIGINS` | Netlify frontend origin |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `DEEPSEEK_API_URL` | `https://api.deepseek.com/v1/chat/completions` |

## Rules

- The browser must not call Render in production.
- The browser must not call `127.0.0.1` or `localhost` in production.
- Secrets stay in Railway or Supabase settings, never in frontend env files.
- Frontend code uses `VITE_API_BASE_URL=/api`; Netlify owns the public backend routing.
- If the Railway backend domain changes, update only `frontend/netlify.toml` and the architecture docs.
