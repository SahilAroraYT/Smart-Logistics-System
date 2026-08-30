# Smart Logistics System

An AI-powered delivery optimization platform. It predicts delivery failures, auto-assigns deliveries to agents, and generates optimized delivery routes with a live map, alerts, and audit logging.

Built as a full-stack web app: a **Next.js** frontend, a **Python (FastAPI)** backend, and a **PostgreSQL** database (Supabase).

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Getting Started (Local)](#getting-started-local)
  - [1. Backend](#1-backend)
  - [2. Frontend](#2-frontend)
  - [3. Seed the database](#3-seed-the-database)
- [Demo Users](#demo-users)
- [Environment Variables](#environment-variables)
- [Deployment (Vercel + Render + Supabase)](#deployment-vercel--render--supabase)
- [API Overview](#api-overview)
- [Project Structure](#project-structure)
- [Reporting / Docs](#reporting--docs)

---

## Features

- **Delivery failure prediction** — an XGBoost model scores each delivery as LOW / MEDIUM / HIGH risk with an explanation of contributing factors.
- **Auto & manual agent assignment** — assign delivery agents to orders, with load-aware availability.
- **Route generation** — nearest-neighbor ordering plus OSRM driving routes, rendered on a Leaflet map.
- **Clustering** — group nearby deliveries into assignment sessions.
- **Live dashboard** — KPIs, delivery status, risk distribution, and charts for admins and managers.
- **Agent app** — delivery agents see their assigned routes and can mark deliveries completed or failed; failed deliveries trigger rerouting.
- **Warehouse management** — add/update/delete warehouses and agents.
- **Alerts** — high-risk deliveries generate alerts that can be acknowledged.
- **Audit logging** — records login and key actions (timestamps in IST).
- **JWT authentication** — role-based access (admin, operations manager, delivery supervisor, delivery agent).

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Leaflet (maps), Recharts |
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| **ML** | XGBoost, scikit-learn, pandas, numpy, joblib |
| **Database** | PostgreSQL (Supabase) / SQLite (local dev) |
| **Routing** | OSRM (public API) |
| **Deployment** | Vercel (frontend), Render (backend), Supabase (Postgres) |

---

## Architecture

```
┌────────────────┐   HTTP    ┌─────────────────┐   SQL    ┌─────────────┐
│  Next.js       │ ─────────►│  FastAPI (Python)│ ───────► │  PostgreSQL  │
│  (Vercel)      │           │  (Render)       │          │  (Supabase)  │
└────────────────┘           └─────────────────┘          └─────────────┘
```

- The **frontend** calls the backend REST API using `NEXT_PUBLIC_API_URL`.
- The **backend** loads an XGBoost model for risk prediction and talks to OSRM for routing.
- The **database** stores users, agents, deliveries, routes, alerts, warehouse, assignments, and audit logs.

---

## Prerequisites

- **Python 3.13** and `pip`
- **Node.js 18+** and `npm`
- A database (PostgreSQL/Supabase, or SQLite for quick local dev)
- (Optional) Git

---

## Getting Started (Local)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create your environment file
cp .env.example .env
# Edit backend/.env and set a DATABASE_URL, JWT_SECRET_KEY, etc.

# Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

> **Note on the database for local dev:** if you do not set `DATABASE_URL`, the app falls back to a local SQLite file (`backend/smart_logistics.db`), which requires no setup.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. Seed the database

Populate demo users, warehouses, agents, and ~500 deliveries:

```bash
cd backend
.venv/bin/python scripts/seed.py
```

> The seed script creates the schema (`create_all`) and imports from `data/logistics_dataset_v3.csv`. For **production**, seed **once** against your deployed database as described in [DEPLOY.md](DEPLOY.md).

---

## Demo Users

| Role | Email | Password |
|---|---|---|
| Admin | `admin@logistics.com` | `admin123` |
| Delivery Agent | `agent1@logistics.com` | `agent123` |

---

## Environment Variables

**Backend** (`backend/.env` — see [backend/.env.example](backend/.env.example)):

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLAlchemy database URL. For Supabase **must** be the Transaction pooler URL (port `6543`). |
| `JWT_SECRET_KEY` | Secret used to sign JWT tokens. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. |
| `JWT_ALGORITHM` | JWT signing algorithm (default `HS256`). |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (default `1440`). |
| `DEBUG` | Enable/disable debug mode (`false` in production). |
| `DEMO_MODE` | Bypasses auth for local testing only. |
| `CORS_ORIGINS` | Comma-separated allowed browser origins, e.g. `http://localhost:3000,https://app.vercel.app`. |
| `OSRM_BASE_URL` | OSRM routing endpoint. |
| `ML_ASSET_BASE_URL` | Base URL for the gitignored ML model files (used for deployment). |

**Frontend** (`frontend/.env.local`):

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the backend API, e.g. `http://localhost:8000/api`. |

---

## Deployment (Vercel + Render + Supabase)

This app deploys as three pieces. The full step-by-step runbook is in **[DEPLOY.md](DEPLOY.md)**. Summary:

1. **Database → Supabase**: use the **Transaction pooler** connection string (`.pooler.supabase.com:6543`) — the direct `:5432` host is IPv6-only and fails from Render.
2. **Backend → Render**: deploy via the included [`render.yaml`](render.yaml) blueprint (free tier). Set `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, and `ML_ASSET_BASE_URL`.
3. **Frontend → Vercel**: import the repo with root directory `frontend` and set `NEXT_PUBLIC_API_URL` to your Render URL.
4. **Seed once**: run `scripts/seed.py` against the production database.

> **ML model files are gitignored.** The XGBoost model, label encoders, and training CSV are not in git. On a deploy host, provide them via `ML_ASSET_BASE_URL` (or upload them) — see `backend/scripts/fetch_ml_assets.sh` and [DEPLOY.md](DEPLOY.md).

---

## API Overview

All routes are prefixed with `/api` and protected by JWT auth (except login/register).

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Log in, returns a JWT |
| `POST` | `/api/auth/register` | Register a user |
| `GET` | `/api/auth/me` | Current user |
| `GET` | `/api/deliveries` | List deliveries (paginated, filter by status/risk) |
| `POST` | `/api/deliveries/predict` | Predict delivery risk |
| `POST` | `/api/deliveries/manual` | Add a manual delivery |
| `GET` | `/api/agents` | List agents |
| `POST` | `/api/agents/auto-assign` | Auto-assign deliveries to agents |
| `POST` | `/api/agents/{id}/offline` | Set an agent offline (redistributes deliveries) |
| `GET` | `/api/routes` | List routes |
| `POST` | `/api/routes/generate` | Generate routes |
| `GET` | `/api/warehouses` | List warehouses |
| `GET` | `/api/alerts` | List alerts |
| `POST` | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |
| `GET` | `/api/audit` | List audit logs |
| `GET` | `/api/assignments` | List assignment sessions |
| `POST` | `/api/assignments` | Create an assignment session |
| `GET` | `/api/agent/me` | Agent self info |
| `GET` | `/api/agent/dashboard` | Agent dashboard data |
| `POST` | `/api/agent/deliveries/{id}/complete` | Mark delivery completed |
| `POST` | `/api/agent/deliveries/{id}/fail` | Mark delivery failed (triggers reroute) |

Full interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI).

---

## Project Structure

```
├── backend/                  # Python FastAPI backend
│   ├── app/                  # Application code
│   │   ├── main.py           # FastAPI entry point
│   │   ├── config.py         # Settings (env-driven)
│   │   ├── database.py       # SQLAlchemy engine/session
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routers/          # API route handlers
│   │   ├── services/         # Business logic (ML, routing, assignment...)
│   │   ├── middleware/       # CORS, etc.
│   │   └── dependencies/     # Auth dependencies
│   ├── alembic/              # Database migrations
│   ├── scripts/              # Seed + ML asset fetch scripts
│   ├── data/                 # Training data (CSV, gitignored)
│   ├── models/               # Trained ML models (pickle, gitignored)
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # Next.js frontend
│   ├── app/                  # App Router pages
│   │   ├── (auth)/           # login, register
│   │   ├── (dashboard)/      # dashboard, deliveries, agents, routes, map, ...
│   │   └── agent/            # agent dashboard
│   ├── components/           # React components
│   ├── lib/                  # API client, auth, utilities
│   └── package.json
├── render.yaml               # Render Blueprint for the backend
├── DEPLOY.md                 # Deployment runbook (Vercel + Render + Supabase)
└── RUN.md                    # Quick start cheat sheet
```

---

## Reporting / Docs

Academic project reports are included at the repo root (`PROJECT_DOCUMENTATION.md`, `report-synopsis.tex`, `report-mid-term.tex`).

---

## License

This project is for educational/academic purposes. See the repo for license details (if any).
