from typing import Dict, Any, List, Optional
from datetime import datetime, time
from rules_engine.rules.base import Rule
from rules_engine.registrator import register_rule
from models.enums import Statuses

@register_rule
class ScheduleRule(Rule):
    def __init__(self):
        self._details = ""
    
    @property
    def name(self) -> str:
        return "schedule"
    
    @property
    def priority(self) -> int:
        return 2
    
    async def evaluate(
        self,
        campaign_data: Dict[str, Any],
        schedules: Optional[List[Dict[str, Any]]] = None,
        current_time: Optional[datetime] = None
    ) -> Optional[Statuses]:
        
        if not campaign_data.get('schedule_enabled', False):
            return None
        
        if not schedules:
            self._details = f"У компании (id: {campaign_data.get('campaign_id')}) включено управление по расписанию, но отсутствует расписание"
            return Statuses.PAUSED
        
        current_time =  datetime.now() if current_time is None else current_time
        current_day = current_time.weekday()
        current_time_only = current_time.time()
        
        today_slots = [
            slot for slot in schedules 
            if slot['day_of_week'] == current_day
        ]
        
        if not today_slots:
            self._details = f"Нет активных слотов на сегодня (день недели: {current_day})"
            return Statuses.PAUSED
        
        in_active_slot = False
        for slot in today_slots:
            start = slot['start_time']
            end = slot['end_time']
            
            if start <= current_time_only <= end:
                in_active_slot = True
                break
        
        if not in_active_slot:
            self._details = f"Текущее время: {current_time_only.strftime('%H:%M')}, день недели: {current_day} --- вне активного окна."
            return Statuses.PAUSED
        
        return None
    
    def get_details(self) -> str:
        return self._details