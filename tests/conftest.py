import pytest
import asyncio
from typing import AsyncGenerator, Generator
from decimal import Decimal
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from database.config import get_db
from models.Base import Base
from models.Campaign import Campaign
from models.enums import Statuses

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

AsyncTestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncTestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncTestingSessionLocal() as session:
        yield session
        
        await session.rollback()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator:
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def sample_campaign_data() -> dict:
    return {
        "name": f"Test Campaign {uuid.uuid4().hex[:8]}",
        "current_status": "active",
        "target_status": "paused",
        "is_managed": True,
        "budget_limit": 1000.00,
        "spend_today": 500.00,
        "stock_days_left": 10,
        "stock_days_min": 5,
        "schedule_enabled": False
    }

@pytest.fixture
async def campaign_in_db(db_session: AsyncSession) -> Campaign:
    campaign = Campaign(
        name=f"Test Campaign {uuid.uuid4().hex[:8]}",
        current_status=Statuses.ACTIVE,
        target_status=Statuses.PAUSED,
        is_managed=True,
        budget_limit=Decimal('1000.00'),
        spend_today=Decimal('500.00'),
        stock_days_left=10,
        stock_days_min=5,
        schedule_enabled=False
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    return campaign

@pytest.fixture
def sample_schedule_data() -> list:
    return [
        {
            "day_of_week": 0,
            "start_time": "09:00:00",
            "end_time": "18:00:00"
        },
        {
            "day_of_week": 1,
            "start_time": "09:00:00",
            "end_time": "18:00:00"
        }
    ]