from typing import Dict, Any, List, Optional
from datetime import datetime
from rules_engine.rules.base import Rule
from rules_engine.registrator import register_rule
from models.enums import Statuses

@register_rule
class StockRule(Rule):
    
    def __init__(self):
        self._details = ""
    
    @property
    def name(self) -> str:
        return "low_stock"
    
    @property
    def priority(self) -> int:
        return 3
    
    async def evaluate(
        self,
        campaign_data: Dict[str, Any],
        schedules: Optional[List[Dict[str, Any]]] = None,
        current_time: Optional[datetime] = None
    ) -> Optional[Statuses]:
        stock_days_min = campaign_data.get('stock_days_min')
        stock_days_left = campaign_data.get('stock_days_left')
        
        if stock_days_min is None:
            return None
        
        # Если stock_days_left не задан, считаю что остатки есть, хотя моментик тут спорный
        if stock_days_left is None:
            return None
        
        if stock_days_left < stock_days_min:
            self._details = (
                f"Остатков хватит на {stock_days_left} дней, "
                f"что меньше минимального порога в {stock_days_min} дней"
            )
            return Statuses.PAUSED
        
        return None
    
    def get_details(self) -> str:
        return self._details