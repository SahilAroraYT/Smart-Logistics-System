from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.middleware.cors import setup_cors
from app.routers import auth, deliveries, agents, routes, alerts, audit, assignments, warehouses, agent
from app.services import ml_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_service.load_model()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

setup_cors(app)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(deliveries.router, prefix="/api/deliveries", tags=["deliveries"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(routes.router, prefix="/api/routes", tags=["routes"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(warehouses.router, prefix="/api/warehouses", tags=["warehouses"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
