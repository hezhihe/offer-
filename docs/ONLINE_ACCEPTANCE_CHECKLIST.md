# Offer Compass Online Acceptance Checklist

Last updated: 2026-06-03

Use this checklist before marking the online MVP as deliverable.

## Acceptance Run - 2026-06-03

Environment tested:

- Frontend: `https://bejewelled-lamington-a93247.netlify.app`
- Backend: `https://offer-compass-api-production.up.railway.app`
- Test account: `19906030001`

Results:

- PASS: Railway `/api/jobs` returned `200`.
- PASS: Railway `/docs` returned the FastAPI docs page.
- PASS: Local frontend production build passed with `npm run build`.
- PENDING REDEPLOY: Netlify config has been corrected to proxy `/api/*` to Railway. Redeploy Netlify before retesting `https://bejewelled-lamington-a93247.netlify.app/api/jobs`.
- PENDING REDEPLOY: Railway needs the latest backend code before retesting `stats/mine`.
- BLOCKED: `public.job_browse_history` is missing in Supabase, so job browse persistence returns `success=false`. Execute `backend/database/update_job_status_tracking.sql` in Supabase SQL Editor, then redeploy/retest.
- WATCH: Previous interview answer scoring returned `0` for a reasonable test answer. The endpoint works, but scoring quality should be reviewed before demo.
- WATCH: PowerShell displayed Chinese API content as mojibake. Browser rendering still needs visual confirmation.

## Deployment Source Of Truth

- [x] Backend production platform is Railway.
- [x] Frontend production platform is Netlify.
- [x] `frontend/netlify.toml` proxies `/api/*` to the Railway backend.
- [x] `frontend/.env.production` sets `VITE_API_BASE_URL=/api`.
- [x] No production frontend setting points to Render, `localhost`, or `127.0.0.1`.

## Railway Backend

- [x] Railway service deploys from `backend/railway.toml`.
- [x] Start command uses Railway `$PORT`.
- [x] `/api/jobs` returns a successful response.
- [ ] `/docs` loads only if public API docs are acceptable for the demo.
- [ ] `CORS_ORIGINS` includes the exact Netlify production origin.
- [ ] Railway environment variables are set: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `API_SECRET_KEY`, `DEEPSEEK_API_KEY`, `DEEPSEEK_API_URL`.
- [ ] No API key or service role key appears in GitHub, Netlify frontend env, browser console, or network response.

## Netlify Frontend

- [x] Netlify base directory is `frontend`.
- [x] Build command is `npm run build`.
- [x] Publish directory is `dist`.
- [ ] Netlify build logs show `VITE_API_BASE_URL=/api`.
- [ ] Refreshing nested routes does not 404 because SPA fallback is enabled.
- [ ] Browser network requests go to `https://<netlify-site>/api/...`, not directly to Render or local addresses.

## Core User Flows

- [ ] Register a new account with phone and password.
- [ ] Log in with that account.
- [ ] Refresh the page and stay authenticated.
- [ ] Visit Home and load tips or fallback content.
- [ ] Visit Calendar and load job data.
- [ ] Submit resume analysis with pasted text.
- [ ] Upload a PDF or Word resume and receive analysis.
- [ ] Start a mock interview.
- [ ] Submit at least one interview answer and receive feedback.
- [ ] Complete interview and save history.
- [ ] Open Profile and view resume/interview history.
- [ ] Upload avatar and confirm it persists after refresh.

## Production Quality Checks

- [x] Frontend build passes locally with `npm run build`.
- [ ] No browser console errors during the core flows.
- [ ] No failed CORS preflight requests.
- [ ] API timeout behavior is acceptable for AI calls.
- [ ] Railway logs do not show missing env variables.
- [ ] Supabase tables contain expected new records after resume and interview tests.
- [ ] Supabase table `public.job_browse_history` exists and accepts upsert from the Railway backend.
- [ ] Mobile viewport can complete login, resume analysis, interview, calendar, and profile flows.

## Release Decision

Release is acceptable only when all blocking items are checked:

- [ ] One production backend only: Railway.
- [ ] One frontend API path only: `/api`.
- [ ] Authentication works online.
- [ ] Resume and interview data persists to Supabase.
- [ ] Job browse history table exists and browse persistence works.
- [ ] No secrets are exposed.
