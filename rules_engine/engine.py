from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from models.enums import Statuses
from .registrator import RuleRegistry


class RuleEngine:
    _instance: Optional['RuleEngine'] = None
    
    def __new__(cls) -> 'RuleEngine':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.rules = RuleRegistry.get_all_rules()
        self._validate_rules_order()
        self._last_evaluation_details: Dict[str, Any] = {}
    
    def _validate_rules_order(self):
        for i in range(1, len(self.rules)):
            if self.rules[i].priority <= self.rules[i-1].priority:
                raise RuntimeError(
                    f"Правила не отсортированы по приоритету: "
                    f"{self.rules[i-1].name}({self.rules[i-1].priority}) -> "
                    f"{self.rules[i].name}({self.rules[i].priority})"
                )
    
    async def evaluate_campaign(
        self,
        campaign_data: Dict[str, Any],
        schedules: Optional[List[Dict[str, Any]]] = None,
        current_time: Optional[datetime] = None
    ) -> Tuple[Statuses, Optional[str], str]:

        if schedules is None:
            schedules = []
        
        if current_time is None:
            current_time = datetime.now()
        
        self._last_evaluation_details = {
            'campaign_id': campaign_data.get('id'),
            'campaign_name': campaign_data.get('name'),
            'current_time': current_time,
            'rules_checked': []
        }
        
        for rule in self.rules:
            self._last_evaluation_details['rules_checked'].append(rule.name)
            result = await rule.evaluate(
                campaign_data=campaign_data,
                schedules=schedules,
                current_time=current_time
            )
            if result is not None:
                self._last_evaluation_details.update({
                    'triggered_rule': rule.name,
                    'rule_details': rule.get_details(),
                    'result_status': result.value if hasattr(result, 'value') else result
                })
                return result, rule.name, rule.get_details()
        
        self._last_evaluation_details.update({
            'triggered_rule': None,
            'rule_details': "Нет ограничений",
            'result_status': Statuses.ACTIVE.value
        })
        
        return Statuses.ACTIVE, None, "Нет ограничений"
    
    
rule_engine = RuleEngine()