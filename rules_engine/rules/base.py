from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from models.enums import Statuses

class Rule(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        pass
    
    @abstractmethod
    async def evaluate(
        self,
        campaign_data: Dict[str, Any],
        schedules: Optional[List[Dict[str, Any]]],
        current_time: Optional[datetime] = None
    ) -> Optional[Statuses]:
        pass
    
    @abstractmethod
    def get_details(self) -> str:
        pass