# Smart Logistics — Quick Start

## Backend
```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend
```bash
cd frontend
npm run dev
```

## Seed Users
| Role | Email | Password |
|---|---|---|
| Admin | admin@logistics.com | admin123 |
| Operations Manager | manager@logistics.com | manager123 |
| Delivery Supervisor | supervisor@logistics.com | supervisor123 |
| Delivery Agent | agent1@logistics.com | agent123 |

## API Docs
http://localhost:8000/docs

## Frontend
http://localhost:3000
