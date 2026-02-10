from typing import Dict, Any, List, Optional
from datetime import datetime
from rules_engine.rules.base import Rule
from rules_engine.registrator import register_rule
from models.enums import Statuses

@register_rule
class ManagementRule(Rule):
    @property
    def name(self) -> str:
        return "management_disabled"
    
    @property
    def priority(self) -> int:
        return 1
    
    async def evaluate(
        self,
        campaign_data: Dict[str, Any],
        schedules: Optional[List[Dict[str, Any]]] = None,
        current_time: Optional[datetime] = None
    ) -> Optional[Statuses]:
        
        if not campaign_data.get('is_managed', False):
            return campaign_data.get('current_status', Statuses.PAUSED)
        return None
    
    def get_details(self) -> str:
        return "Автоматическое управление выключено"