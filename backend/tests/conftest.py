import os
import pathlib

# Always use SQLite for tests regardless of what .env says.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_modpanel.db"
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

import httpx
import pytest

_TEST_DB_PATH = pathlib.Path("./test_modpanel.db")


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Delete the test SQLite file after the full test session ends."""
    yield
    _TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture
async def app_client():
    """Fresh database + httpx client for each test."""
    from backend.db.database import AsyncSessionLocal, Base, engine
    from backend.api.panels import seed_panels
    from backend.main import app

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_panels(session)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def auth_headers(app_client):
    """Register a test user and return Bearer auth headers."""
    resp = await app_client.post(
        "/auth/register",
        json={"email": "testuser@example.com", "password": "testpassword123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
