from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
import os


POSTGRES_DB = os.getenv("POSTGRES_DB", "db_name")
POSTGRES_USER = os.getenv("POSTGRES_USER", "db_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "db_password")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL,
                             pool_size=20,
                             max_overflow=10,
                             pool_timeout=30.0,
                             pool_recycle=1800,
                             pool_pre_ping=True,
                             echo=False)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
