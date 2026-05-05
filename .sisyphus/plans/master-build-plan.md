# Master Build Plan — AI-Powered Smart Logistics Delivery Optimization System

> Saved: 2026-05-05 | Status: Planning & Clarification Phase

---

## 1. WHAT I UNDERSTAND

### Current Workspace State
- **`backend/`** — Has `.venv/`, `data/logistics_dataset_v3.csv`, `models/delivery_failure_model_v2.pkl`, `models/label_encoders_v2.pkl`
- **`frontend/`** — Fresh Next.js 16 scaffold (App Router, Tailwind v4, TypeScript). Only default `page.tsx` and `layout.tsx`. No ShadCN, no Recharts, no Leaflet installed yet.
- **No backend code exists yet** — no FastAPI app, no routes, no services, no DB setup.

### Core System — 6 Pillars
1. **ML Risk Prediction** — Load pretrained XGBoost + label encoders, run inference with exact feature engineering matching training pipeline
2. **Intelligent Routing Engine** — Multi-factor cost function (distance + risk + traffic + weather + agent load), NOT shortest path
3. **Dynamic Rerouting** — Real-time trigger-based reroute when conditions change
4. **Alert System** — Threshold-based alert generation, stored in DB, exposed via API
5. **Audit Logging** — Every critical action logged with user_id, action_type, timestamp, metadata
6. **RBAC Auth** — JWT-based, 4 roles (Admin, Ops Manager, Supervisor, Agent), permission-gated APIs

### Tech Stack
- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind v4 + ShadCN UI + Recharts + Leaflet/OpenStreetMap
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy + Pydantic
- **ML**: XGBoost (pretrained, via joblib .pkl) + Pandas/NumPy
- **Routing**: OSRM API for base routes + custom cost-function reordering
- **Local only** — no Docker, no deployment configs

### Dataset Columns (from CSV header)
Numerical: distance_km, package_weight, floor_number, past_success_rate, customer_cancellation_rate, customer_return_rate, agent_daily_load, previous_failed_attempt_same_order
Binary: lift_available (0/1)
Categorical: delivery_zone, time_slot, day_of_week, location_type, building_type, payment_type, package_size, weather, traffic_level
Additional (not model features): order_id, customer_id, warehouse_id, agent_id, customer_lat, customer_lon, warehouse_lat, warehouse_lon, month, is_weekend, is_holiday, order_value, customer_past_orders, phone_reachable, customer_available, preferred_slot_match, otp_required, agent_experience_years, agent_success_rate, delivery_attempts, delivery_success

### Feature Engineering Formulas (strict)
- customer_risk_score = (1 - past_success_rate) * customer_cancellation_rate * customer_return_rate
- delivery_difficulty_score = distance_km * (floor_number * 0.5) * (1 - lift_available) * 2 * (package_weight * 0.3)
- agent_load_risk = agent_daily_load * (previous_failed_attempt_same_order * 5)
- cod_risk_flag = 1 if payment_type == "COD" else 0
- bad_weather_flag = 1 if weather in ["rain", "fog"] else 0

### ML Inference Pipeline (strict order)
1. Validate raw input → 2. **Compute 5 derived features** (customer_risk_score, delivery_difficulty_score, agent_load_risk, cod_risk_flag, bad_weather_flag) → 3. Combine raw + derived into feature vector → 4. Encode categoricals via label_encoders.pkl → 5. Exact feature order matching training → 6. predict_proba(X)[0][1] → 7. risk_score = prob * 100 → 8. Categorize (0-30 LOW, 30-70 MEDIUM, 70-100 HIGH) → 9. Generate explanation using derived feature values

### Routing Cost Function
total_cost = (distance * 0.4) + (risk_score * 0.3) + (traffic_penalty * 0.1) + (weather_penalty * 0.1) + (agent_load_penalty * 0.1)

### File Naming Decision (RESOLVED)
- **Use actual file names**: `delivery_failure_model_v2.pkl` and `label_encoders_v2.pkl`
- Code will reference these directly in config

---

## 2. CLARIFICATION DECISIONS (RESOLVED)

| Question | Decision |
|---|---|
| Model file naming | Use `_v2` suffix files as-is |
| Seed data | Seed from `logistics_dataset_v3.csv` on initial run |
| Agent assignment | Auto-assign on route generation, supervisor can override |
| Routing distances | OSRM public server (`router.project-osrm.org`) |
| User creation | Seed script (one per role) + admin can create via API |
| Auth scope | All APIs protected by JWT + demo bypass flag for local testing |
| **ML feature scope** | **Model trained on raw columns + 5 derived features. Must compute and add to vector BEFORE prediction.** |

---

## 3. ARCHITECTURE PLAN

### Backend Directory Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry, lifespan, CORS, routers
│   ├── config.py               # Settings (DB URL, JWT secret, model paths, etc.)
│   ├── database.py             # SQLAlchemy engine, session factory, Base
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User model + Role enum
│   │   ├── delivery.py         # Delivery model + status enum
│   │   ├── agent.py            # DeliveryAgent model
│   │   ├── route.py            # Route + RouteStop models
│   │   ├── alert.py            # Alert model + severity enum
│   │   └── audit_log.py        # AuditLog model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # Pydantic: UserCreate, UserLogin, UserResponse
│   │   ├── delivery.py         # Pydantic: DeliveryCreate, DeliveryResponse, PredictionRequest
│   │   ├── agent.py            # Pydantic: AgentResponse, AgentAssignment
│   │   ├── route.py            # Pydantic: RouteResponse, RerouteRequest
│   │   ├── alert.py            # Pydantic: AlertResponse
│   │   ├── audit_log.py        # Pydantic: AuditLogResponse
│   │   └── auth.py             # Pydantic: Token, TokenData
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ml_service.py       # Model loading, feature engineering, inference
│   │   ├── routing_service.py  # Cost function, OSRM integration, route optimization
│   │   ├── delivery_service.py # CRUD, risk computation, status management
│   │   ├── agent_service.py    # Agent assignment logic, load tracking
│   │   ├── alert_service.py    # Alert generation, threshold checks
│   │   ├── audit_service.py    # Audit logging
│   │   ├── auth_service.py     # JWT creation/verification, password hashing
│   │   └── user_service.py     # User CRUD, role checks
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # POST /auth/login, /auth/register
│   │   ├── deliveries.py       # CRUD + prediction endpoints
│   │   ├── agents.py           # Agent management + assignment
│   │   ├── routes.py           # Route generation + rerouting
│   │   ├── alerts.py           # Alert listing + acknowledgment
│   │   └── audit.py            # Audit log queries
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── auth.py             # get_current_user, require_role
│   │   └── db.py               # get_db session dependency
│   └── middleware/
│       └── audit.py            # Auto-audit middleware (optional)
├── models/
│   ├── delivery_failure_model_v2.pkl
│   └── label_encoders_v2.pkl
├── data/
│   └── logistics_dataset_v3.csv
├── requirements.txt
└── alembic/                    # DB migrations
    └── ...
```

### Frontend Directory Structure
```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Redirect to /dashboard
│   ├── (auth)/
│   │   ├── login/page.tsx      # Login page
│   │   └── register/page.tsx   # Register page (admin only)
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Dashboard shell (sidebar + header)
│   │   ├── dashboard/page.tsx  # Main dashboard (KPIs, charts)
│   │   ├── map/page.tsx        # Leaflet map view
│   │   ├── deliveries/page.tsx # Delivery list + detail
│   │   ├── agents/page.tsx     # Agent management
│   │   ├── routes/page.tsx     # Route visualization
│   │   ├── alerts/page.tsx     # Alert center
│   │   └── audit/page.tsx      # Audit log viewer
│   └── api/                    # (minimal, mostly proxy to FastAPI)
├── components/
│   ├── ui/                     # ShadCN components
│   ├── dashboard/
│   │   ├── KPICards.tsx
│   │   ├── RiskDistributionChart.tsx
│   │   ├── DeliveryTrendChart.tsx
│   │   └── AgentPerformanceChart.tsx
│   ├── map/
│   │   ├── DeliveryMap.tsx
│   │   ├── RouteOverlay.tsx
│   │   └── RiskMarkers.tsx
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── AuthGuard.tsx
│   └── alerts/
│       └── AlertList.tsx
├── lib/
│   ├── api.ts                  # API client (fetch wrapper)
│   ├── auth.ts                 # Auth context + hooks
│   └── utils.ts                # cn() utility
├── hooks/
│   ├── useDeliveries.ts
│   ├── useAgents.ts
│   ├── useAlerts.ts
│   └── useRoutes.ts
└── types/
    └── index.ts                # Shared TypeScript types
```

### Database Schema (PostgreSQL)
**users** — id, email, password_hash, full_name, role (enum), is_active, created_at, updated_at
**delivery_agents** — id, user_id (FK), name, phone, vehicle_type, current_lat, current_lon, current_load, max_load, success_rate, is_available, created_at
**deliveries** — id, order_id, customer_id, customer_lat, customer_lon, warehouse_lat, warehouse_lon, distance_km, delivery_zone, time_slot, day_of_week, location_type, building_type, floor_number, lift_available, payment_type, package_weight, package_size, weather, traffic_level, agent_id (FK nullable), status (enum), risk_score (nullable), risk_category (nullable), assigned_route_id (FK nullable), created_at, updated_at, delivered_at
**routes** — id, name, agent_id (FK), status (enum), total_distance, total_risk_score, created_at, completed_at
**route_stops** — id, route_id (FK), delivery_id (FK), stop_order, estimated_arrival, actual_arrival, status
**alerts** — id, delivery_id (FK nullable), agent_id (FK nullable), alert_type, severity, message, is_acknowledged, acknowledged_by (FK nullable), created_at
**audit_logs** — id, user_id (FK nullable), action_type, entity_type, entity_id, metadata (JSON), timestamp

---

## 3. IMPLEMENTATION PHASES

### Phase 1: Backend Foundation
1.1 FastAPI app setup + config + DB connection
1.2 SQLAlchemy models (all 7 tables)
1.3 Alembic migration setup
1.4 Pydantic schemas
1.5 Requirements.txt with all deps

### Phase 2: Auth & RBAC
2.1 Password hashing (bcrypt)
2.2 JWT token creation/verification
2.3 Auth dependencies (get_current_user, require_role)
2.4 Auth routes (login, register)
2.5 User service + routes
2.6 Seed admin user script

### Phase 3: ML Service
3.1 Model loading service (joblib)
3.2 Feature engineering (exact formulas)
3.3 Label encoder application
3.4 Inference pipeline (predict_proba → risk_score → category → explanation)
3.5 Single prediction endpoint
3.6 Batch prediction endpoint

### Phase 4: Delivery Service
4.1 Delivery CRUD operations
4.2 Delivery listing with filtering/pagination
4.3 Delivery status management
4.4 Risk score attachment to deliveries

### Phase 5: Routing Engine
5.1 OSRM API integration
5.2 Multi-factor cost function implementation
5.3 Delivery prioritization (HIGH risk first, then deadline)
5.4 Agent assignment logic (lowest load, nearest, best success)
5.5 Route generation with reordered stops
5.6 Dynamic rerouting triggers

### Phase 6: Alert & Audit
6.1 Alert service (threshold checks, generation)
6.2 Alert routes (list, acknowledge)
6.3 Audit logging service
6.4 Audit middleware / decorators
6.5 Audit log routes

### Phase 7: Frontend Foundation
7.1 ShadCN UI setup
7.2 Install Recharts, Leaflet, react-leaflet
7.3 Layout with sidebar + header
7.4 Auth context + login page
7.5 AuthGuard wrapper
7.6 API client layer

### Phase 8: Dashboard & Analytics
8.1 KPI cards (total deliveries, failure rate, active alerts)
8.2 Risk distribution chart (pie/donut)
8.3 Delivery trend chart (line/bar)
8.4 Agent performance chart
8.5 Real-time stats refresh

### Phase 9: Map View
9.1 Leaflet map with OpenStreetMap
9.2 Delivery markers (color-coded by risk)
9.3 Route line overlays
9.4 Marker popups with delivery details
9.5 Warehouse markers

### Phase 10: Management Pages
10.1 Deliveries list + detail view
10.2 Agent management panel
10.3 Route visualization page
10.4 Alert center with acknowledge
10.5 Audit log viewer with filters

### Phase 11: Integration & Polish
11.1 Wire all frontend to backend APIs
11.2 Error handling + loading states
11.3 Seed data script (from CSV)
11.4 Local run verification

---

## 4. KEY DESIGN DECISIONS

- **Service layer is the SINGLE source of truth** for business logic. Routers only validate + delegate + return.
- **ML service is stateless** — model loaded once at startup via lifespan, then reused.
- **Routing uses OSRM** for real road distances, then applies our cost function to reorder.
- **JWT stored in httpOnly cookies** from backend, frontend reads auth state via /auth/me endpoint.
- **Database seeding** from the existing CSV for realistic demo data.
- **No Redis/caching** — local system, PostgreSQL is sufficient.
- **No WebSocket** — polling for real-time updates (simpler, adequate for local).

---

## 5. OPEN QUESTIONS FOR CLARIFICATION

See questions section below.
