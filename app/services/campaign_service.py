from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

from models.Campaign import Campaign
from models.CampaignSchedule import CampaignSchedule
from models.schemas.campaignSchema import CampaignCreate, CampaignUpdate
from models.schemas.campaignScheduleSchema import CampaignScheduleCreate
from models.enums import Statuses


class CampaignService:
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_campaign(self, campaign_data: CampaignCreate) -> Campaign:
        create_dict = campaign_data.model_dump(exclude_unset=True)
        campaign = Campaign(**create_dict)
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)
        
        return campaign
    
    async def get_campaign(self, campaign_id: UUID) -> Optional[Campaign]:
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_campaign_with_schedules(self, campaign_id: UUID) -> Optional[Tuple[Campaign, List[CampaignSchedule]]]:
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await self.db.execute(stmt)
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            return None
        
        schedules = await self.get_campaign_schedules(campaign_id)
        return campaign, schedules
    
    async def get_campaigns(
        self,
        skip: int = 0,
        limit: int = 100,
        is_managed: Optional[bool] = None,
        needs_sync: Optional[bool] = None
    ) -> Tuple[List[Campaign], int]:
        """
        Получить список кампаний с пагинацией
        
        Args:
            skip: сколько пропустить
            limit: сколько вернуть
            is_managed: фильтр по is_managed
            needs_sync: фильтр по current_status != target_status
            
        Returns:
            (список кампаний, общее количество)
        """
        query = select(Campaign)
        
        if is_managed is not None:
            query = query.where(Campaign.is_managed == is_managed)
        
        if needs_sync is not None:
            if needs_sync:
                query = query.where(Campaign.current_status != Campaign.target_status)
            else:
                query = query.where(Campaign.current_status == Campaign.target_status)
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        campaigns = result.scalars().all()
        
        return campaigns, total
    
    async def update_campaign(
        self,
        campaign_id: UUID,
        update_data: CampaignUpdate
    ) -> Optional[Campaign]:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            return campaign
        
        stmt = (
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(**update_dict)
            .returning(Campaign)
        )
        
        result = await self.db.execute(stmt)
        updated_campaign = result.scalar_one()
        
        await self.db.flush()
        return updated_campaign
    
    
    async def set_campaign_schedule(
        self,
        campaign_id: UUID,
        schedule_slots: List[Dict[str, Any]]  # [{day_of_week: 0, start_time: ..., end_time: ...}, ...]
    ) -> List[CampaignSchedule]:
        await self.delete_campaign_schedule(campaign_id)
        
        created_slots = []
        for slot_data in schedule_slots:
            slot_data_with_campaign = {**slot_data, 'campaign_id': campaign_id}
            
            schedule_create = CampaignScheduleCreate(**slot_data_with_campaign)
            
            schedule_slot = CampaignSchedule(**schedule_create.model_dump())
            
            self.db.add(schedule_slot)
            created_slots.append(schedule_slot)
        
        await self.db.flush()
        
        if schedule_slots:
            stmt = (
                update(Campaign)
                .where(Campaign.id == campaign_id)
                .values(schedule_enabled=True)
            )
        else:
            stmt = (
                update(Campaign)
                .where(Campaign.id == campaign_id)
                .values(schedule_enabled=False)
            )
        
        await self.db.execute(stmt)
        await self.db.flush()
        
        return created_slots
    
    async def get_campaign_schedules(self, campaign_id: UUID) -> List[CampaignSchedule]:
        stmt = select(CampaignSchedule).where(CampaignSchedule.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_campaign_schedule(self, campaign_id: UUID) -> bool:
        stmt = delete(CampaignSchedule).where(CampaignSchedule.campaign_id == campaign_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        update_stmt = (
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(schedule_enabled=False)
        )
        await self.db.execute(update_stmt)
        await self.db.flush()
        
        return result.rowcount > 0
    
    
    async def update_campaign_target_status(
        self,
        campaign_id: UUID,
        new_target_status: Statuses
    ) -> Optional[Campaign]:
        stmt = (
            update(Campaign)
            .where(Campaign.id == campaign_id)
            .values(target_status=new_target_status)
            .returning(Campaign)
        )
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        return result.scalar_one_or_none()
    
    async def get_campaigns_needing_sync(self) -> List[Campaign]:
        stmt = select(Campaign).where(Campaign.current_status != Campaign.target_status)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    