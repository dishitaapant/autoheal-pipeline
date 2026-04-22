"""
AutoHeal CI/CD Pipeline System - FastAPI Backend
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import webhook, pipelines, analytics, health
from utils.database import connect_db, disconnect_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("autoheal")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AutoHeal backend...")
    await connect_db()
    yield
    logger.info("Shutting down AutoHeal backend...")
    await disconnect_db()


app = FastAPI(
    title="AutoHeal CI/CD Pipeline System",
    description="Self-healing CI/CD pipeline monitor with GitHub Actions integration",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router, prefix="/api/webhook", tags=["Webhook"])
app.include_router(pipelines.router, prefix="/api/pipelines", tags=["Pipelines"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])


@app.get("/")
async def root():
    return {
        "service": "AutoHeal CI/CD Pipeline System",
        "version": "1.0.0",
        "status": "running",
    }
