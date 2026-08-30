# Smart Logistics — Deployment Runbook (Vercel + Render + Supabase)

Architecture:

```
Vercel (Next.js frontend)  ──NEXT_PUBLIC_API_URL──►  Render (FastAPI backend)  ──DATABASE_URL──►  Supabase (Postgres)
```

- **Frontend**: Next.js App Router, deployed to **Vercel**.
- **Backend**: Python FastAPI + uvicorn, deployed to **Render** (persistent host; Supabase/Vercel cannot run it).
- **Database**: Supabase **Postgres**. The backend connects via SQLAlchemy (`DATABASE_URL`).

---

## 0. Prerequisites / accounts

- Supabase project (you have one)
- Render account (free tier is fine)
- Vercel account (hobby/free fine)
- Git repo pushed to GitHub (or GitLab) reachable by both Render and Vercel.

---

## 1. Supabase

### 1.1 Get the connection string
Supabase dashboard → Project Settings → **Database** → Connection string → **URI**.

For production/from a server, prefer the **Transaction pooler** (port `6543`) URL:
```
postgresql://postgres.<ref>:<PASSWORD>@aws-0-<region>.pooler.supabase.com:6543/postgres
```
The backend uses the psycopg2 dialect, so use the `postgresql://` (not `postgresql+asyncpg`) form.

### 1.2 No schema work needed
The app creates its own 8 tables. You choose between:

- **(A) Fresh seed (recommended for a demo)** — run `scripts/seed.py` once against Supabase (creates tables via `create_all` + loads demo users/warehouses/agents/500 deliveries). See section 4.
- **(B) Alembic baseline** — `alembic upgrade head` runs the initial migration `4475cb35d367_initial_schema` if you prefer migrations over seeds. (Seed and migration both work; don't run both on an empty DB and then duplicate — run one.)

---

## 2. Backend on Render

### 2.1 Blueprint
A `render.yaml` blueprint is included at the repo root. From a desktop with the Render CLI:

```bash
render blueprint launch
```

Or, in the Render dashboard:
1. **New → Blueprint** → connect your repo → select `render.yaml`.

The blueprint uses `rootDir: backend`, installs `requirements.txt`, runs `scripts/fetch_ml_assets.sh` (preDeploy) to fetch the gitignored ML model, and starts `uvicorn app.main:app`.

### 2.2 Set secrets in the Render dashboard (not in the committed file)
For `render.yaml` the following `envVars` with `sync: false` must be filled manually in the Render Dashboard → Environment:

| Var | Value |
|---|---|
| `DATABASE_URL` | Your Supabase Postgres URI from step 1.1 |
| `JWT_SECRET_KEY` | A long random string. Generate on your machine: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ML_ASSET_BASE_URL` | Base URL hosting the model files (see 2.3) — only needed if they're not in the repo |

The blueprint already sets `DEBUG=false` and `DEMO_MODE=false`.

### 2.3 The ML model is gitignored — you MUST provide it
The model pickles and training CSV are **not** in git (the repo `.gitignore` excludes `*.pkl` and `*.csv`), so a push-to-deploy will NOT include them. Three options:

1. **`ML_ASSET_BASE_URL`** (easiest): put these 3 files somewhere publicly reachable (S3/GCS/any static host) and set the base URL:
   - `models/delivery_failure_model_v2.pkl`
   - `models/label_encoders_v2.pkl`
   - `data/logistics_dataset_v3.csv`
   `scripts/fetch_ml_assets.sh` downloads them into place during `preDeploy`.

2. **Upload manually**: after the service is created, use Render **Console/Shell** to upload the files to `models/` and `data/` inside the backend dir.

3. **Force them into the repo**: remove the `*.pkl` / `*.csv` ignores (not recommended; large binaries bloat the repo and the free tier build).

> Without the model present, the app still starts but `ml_service.load_model()` will fail when prediction is called, and the seed cannot run. The 2 pickle files + CSV must exist.

### 2.4 Health check
The blueprint sets `healthCheckPath: /docs` (FastAPI's interactive docs) so Render marks the service live once it responds.

### 2.5 Free tier behavior
Free Render spins down after ~15 min idle. First request after idle triggers a cold start — with the 9 MB model + ML libs this is **~45–120s**. The Vercel frontend itself stays fast. For a demo this is acceptable; there is no keep-alive on the free plan's 750-hr budget.

---

## 3. Frontend on Vercel

### 3.1 Import
1. Vercel Dashboard → **Add New → Project** → import your repo.
2. **Root Directory**: select `frontend` (the Next.js app lives there). A `frontend/vercel.json` is included; adjust if Vercel autodetects the subfolder.
3. **Framework Preset**: Next.js.
4. Build: `next build` (default). No special config needed.

### 3.2 Environment variable (required)
In Vercel → Project → **Settings → Environment Variables**, add:

| Name | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<your-render-service>.onrender.com/api` |

`frontend/lib/api.ts` reads `process.env.NEXT_PUBLIC_API_URL` (falls back to localhost if unset). It must be set for the dashboard/agent pages to reach the backend.

> `NEXT_PUBLIC_*` vars are inlined at build time — set them in **Production** (and Preview/Development if wanted), then **redeploy**.

### 3.3 Deploy
Push to the connected branch (or click **Deploy**) → Vercel builds the frontend and serves it.

---

## 4. Fresh-seed the database (Supabase)

After the backend is deployed and its `DATABASE_URL` points at Supabase, create the demo data. Run the seed inside the Render service shell, or locally with your venv pointed at Supabase:

```bash
cd backend
.venv/bin/python scripts/seed.py
```

This creates the tables via `Base.metadata.create_all` and inserts:
- 3 staff users, 25 delivery agents
- 5 warehouses (Delhi, Gurgaon, Noida, South Delhi, Ludhiana)
- ~500 deliveries with ML risk scores (reads `data/logistics_dataset_v3.csv`, requires the model)

Demo logins (from `RUN.md`):

| Role | Email | Password |
|---|---|---|
| Admin | admin@logistics.com | admin123 |
| Operations Manager | manager@logistics.com | manager123 |
| Delivery Supervisor | supervisor@logistics.com | supervisor123 |
| Delivery Agent | agent1@logistics.com | agent123 |

---

## 5. Verify

1. **Backend**: open `https://<render-service>.onrender.com/docs` — should render FastAPI docs and report healthy.
2. **Login flow**: open the Vercel URL, log in as `admin@logistics.com` / `admin123` — should hit the backend and load the dashboard KPIs/deliveries.
3. **Prediction**: trigger a delivery risk prediction — confirms the ML model is loaded (fails fast if the model files are missing).
4. **Route on a map**: OpenStreetMap/Leaflet runs in the browser; OSRM routing calls go from the backend to the public OSRM API (free, rate-limited).

---

## 6. Rollback

- **Vercel**: Dashboard → Deployments → click **⋮ → Promote** a previous deployment.
- **Render**: Dashboard → service → top-right **Rollback**.
- **Supabase**: use SQL editor + point-in-time restore for the DB if data changes need undoing.

---

## 7. Before you call it production-ready

- [ ] `JWT_SECRET_KEY` is a real random secret in Render (not the `"change-me"` fallback in `app/config.py`).
- [ ] `DEBUG` and `DEMO_MODE` are `false` in production.
- [ ] OSRM is pointed at a hosted/keyed provider for volume (public demo endpoint is rate-limited).
- [ ] The gitignored ML assets are actually reachable by the backend (section 2.3).
- [ ] Database backup / Point-in-Time (Supabase PITR) verified.
