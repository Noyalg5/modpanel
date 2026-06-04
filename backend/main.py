import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth import router as auth_router
from backend.api.optimiser import projects_router as optimiser_projects_router
from backend.api.optimiser import router as optimiser_router
from backend.api.panels import router as panels_router, seed_panels
from backend.api.projects import router as projects_router
from backend.api.quotes import projects_router as quotes_projects_router
from backend.api.quotes import router as quotes_router
from backend.api.reports import projects_router as reports_projects_router
from backend.api.reports import router as reports_router
from backend.db.database import AsyncSessionLocal, Base, engine, get_database_type
from backend.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed_panels(db)
    logger.info(f"Database: {get_database_type()} — {settings.DATABASE_URL[:40]}...")
    yield


app = FastAPI(
    title="ModPanel AI Platform",
    version="1.0.0",
    description="AI-powered modular construction planning",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(panels_router)
app.include_router(optimiser_router)
app.include_router(optimiser_projects_router)
app.include_router(quotes_router)
app.include_router(quotes_projects_router)
app.include_router(reports_router)
app.include_router(reports_projects_router)


@app.get("/")
async def root():
    return {"status": "ModPanel API running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
