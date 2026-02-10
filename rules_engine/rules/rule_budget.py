from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from rules_engine.rules.base import Rule
from rules_engine.registrator import register_rule
from models.enums import Statuses

@register_rule
class BudgetRule(Rule):
    def __init__(self):
        self._details = ""
    
    @property
    def name(self) -> str:
        return "budget_exceeded"
    
    @property
    def priority(self) -> int:
        return 4
    
    async def evaluate(
        self,
        campaign_data: Dict[str, Any],
        schedules: Optional[List[Dict[str, Any]]] = None,
        current_time: Optional[datetime] = None
    ) -> Optional[Statuses]:
        budget_limit = campaign_data.get('budget_limit')
        spend_today = campaign_data.get('spend_today', Decimal('0'))
        
        if budget_limit is None:
            return None
        
        if spend_today > budget_limit:
            self._details = (
                f"Расход за сегодня {spend_today} руб. "
                f"превышает дневной лимит в {budget_limit} руб."
            )
            return Statuses.PAUSED
        
        return None
    
    def get_details(self) -> str:
        return self._details