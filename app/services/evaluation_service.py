from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, time
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from enum import Enum

from models.Campaign import Campaign
from models.CampaignSchedule import CampaignSchedule
from models.RuleEvaluationLog import RuleEvaluationLog
from models.enums import Statuses
from models.schemas.ruleEvaluationLogSchema import RuleEvaluationLogCreate
from rules_engine.engine import rule_engine
from .campaign_service import CampaignService


class EvaluationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.campaign_service = CampaignService(db)
    
    async def evaluate_single_campaign(
        self,
        campaign_id: UUID,
        current_time: datetime = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        
        campaign_data = await self.campaign_service.get_campaign_with_schedules(campaign_id)
        if not campaign_data:
            raise ValueError(f"Кампания с ID {campaign_id} не найдена")
        
        campaign, schedules = campaign_data
        
        campaign_dict = self._campaign_to_dict(campaign)
        schedule_dicts = self._schedules_to_dicts(schedules)
        
        target_status, triggered_rule, rule_details = await rule_engine.evaluate_campaign(
            campaign_data=campaign_dict,
            schedules=schedule_dicts,
            current_time=datetime.now() if current_time is None else current_time
        )
        
        log_entry = None
        if not dry_run:
            log_entry = await self._log_evaluation(
                campaign=campaign,
                triggered_rule=triggered_rule,
                new_target_status=target_status,
                rule_details=rule_details,
                campaign_snapshot=campaign_dict,
                schedule_snapshot=schedule_dicts,
                current_time=current_time
            )
            
            if target_status != campaign.target_status:
                await self.campaign_service.update_campaign_target_status(
                    campaign_id=campaign_id,
                    new_target_status=target_status
                )
        
        result = {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "current_status": campaign.current_status,
            "previous_target_status": campaign.target_status,
            "new_target_status": target_status,
            "triggered_rule": triggered_rule,
            "rule_details": rule_details,
            "needs_sync": target_status != campaign.current_status,
            "dry_run": dry_run,
            "log_entry_id": log_entry.id if log_entry else None,
            "evaluated_at": datetime.now() if current_time is None else current_time
        }
        
        return result
    
    async def evaluate_all_campaigns(
        self,
        current_time: datetime = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:

        current_time = datetime.now() if current_time is None else current_time
        campaigns, total = await self.campaign_service.get_campaigns(is_managed=True)
        
        results = []
        evaluated_count = 0
        sync_needed_count = 0
        
        for campaign in campaigns:
            try:
                result = await self.evaluate_single_campaign(
                    campaign_id=campaign.id,
                    current_time=current_time,
                    dry_run=dry_run
                )
                
                results.append(result)
                evaluated_count += 1
                
                if result["needs_sync"]:
                    sync_needed_count += 1
                    
            except Exception as e:
                results.append({
                    "campaign_id": campaign.id,
                    "campaign_name": campaign.name,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "evaluated": evaluated_count,
            "total_managed": total,
            "needs_sync": sync_needed_count,
            "dry_run": dry_run,
            "evaluated_at": current_time,
            "results": results
        }
    
    async def get_evaluation_history(
        self,
        campaign_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[RuleEvaluationLog], int]:
        """
        Returns:
            (список записей лога, общее количество)
        """

        count_query = select(
            func.count()
        ).where(
            RuleEvaluationLog.campaign_id == campaign_id
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()
        
        query = (
            select(RuleEvaluationLog)
            .where(RuleEvaluationLog.campaign_id == campaign_id)
            .order_by(RuleEvaluationLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return logs, total
    
    
    def _campaign_to_dict(self, campaign: Campaign) -> Dict[str, Any]:
        return {
            "id": campaign.id,
            "name": campaign.name,
            "current_status": campaign.current_status,
            "target_status": campaign.target_status,
            "is_managed": campaign.is_managed,
            "budget_limit": campaign.budget_limit,
            "spend_today": campaign.spend_today or Decimal("0.00"),
            "stock_days_left": campaign.stock_days_left,
            "stock_days_min": campaign.stock_days_min,
            "schedule_enabled": campaign.schedule_enabled,
            "created_at": campaign.created_at,
            "updated_at": campaign.updated_at
        }
    
    def _schedules_to_dicts(self, schedules: List[CampaignSchedule]) -> List[Dict[str, Any]]:
        return [
            {
                "id": schedule.id,
                "campaign_id": schedule.campaign_id,
                "day_of_week": schedule.day_of_week,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "created_at": schedule.created_at,
                "updated_at": schedule.updated_at
            }
            for schedule in schedules
        ]
    
    async def _log_evaluation(
        self,
        campaign: Campaign,
        triggered_rule: Optional[str],
        new_target_status: Statuses,
        rule_details: str,
        campaign_snapshot: Dict[str, Any],
        schedule_snapshot: List[Dict[str, Any]],
        current_time: datetime = None
    ) -> RuleEvaluationLog:

        def convert_for_json(obj):
            if isinstance(obj, UUID):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, time):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, Enum):
                return obj.value
            return obj
        
        processed_campaign_snapshot = {}
        for key, value in campaign_snapshot.items():
            processed_campaign_snapshot[key] = convert_for_json(value)
        
        processed_schedule_snapshot = []
        for schedule in schedule_snapshot:
            processed_schedule = {}
            for key, value in schedule.items():
                processed_schedule[key] = convert_for_json(value)
            processed_schedule_snapshot.append(processed_schedule)
        
        context = {
            "campaign_snapshot": processed_campaign_snapshot,
            "schedule_snapshot": processed_schedule_snapshot,
            "rule_details": rule_details,
            "current_time": current_time.isoformat() if current_time else None
        }
        
        log_data = RuleEvaluationLogCreate(
            campaign_id=campaign.id,
            triggered_rule=triggered_rule,
            previous_target=campaign.target_status,
            new_target=new_target_status,
            context=context
        )
        
        log_entry = RuleEvaluationLog(**log_data.model_dump())
        self.db.add(log_entry)
        await self.db.flush()
        
        return log_entry
    