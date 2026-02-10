from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_db
from app.services.campaign_service import CampaignService
from app.services.evaluation_service import EvaluationService


async def get_campaign_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[CampaignService, None]:
    yield CampaignService(db)


async def get_evaluation_service(db: AsyncSession = Depends(get_db)) -> AsyncGenerator[EvaluationService, None]:
    yield EvaluationService(db)
