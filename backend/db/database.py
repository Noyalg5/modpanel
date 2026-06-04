from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from backend.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


def get_database_type() -> str:
    """Return 'sqlite' or 'postgresql' based on the configured DATABASE_URL."""
    return "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql"
