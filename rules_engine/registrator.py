from typing import List, Type
from .rules.base import Rule

class RuleRegistry:
    _rules: List[Type[Rule]] = []
    
    @classmethod
    def register(cls, rule_class: Type[Rule]) -> Type[Rule]:
        """
        Декоратор для регистрации класса правила.
        """
        if not issubclass(rule_class, Rule):
            raise TypeError(f"Класс {rule_class} должен наследоваться от Rule")
        
        temp_instance = rule_class()
        existing_names = {cls().name for cls in cls._rules}
        
        if temp_instance.name in existing_names:
            raise ValueError(
                f"Правило с именем '{temp_instance.name}' уже зарегистрировано. "
                f"Имена правил должны быть уникальными."
            )
        
        cls._rules.append(rule_class)
        return rule_class
    
    @classmethod
    def get_all_rules(cls) -> List[Rule]:
        """
        Возвращает все зарегистрированные правила,
        отсортированные по приоритету (меньше = выше).
        """
        instances = [rule_cls() for rule_cls in cls._rules]
        return sorted(instances, key=lambda rule: rule.priority)
    

register_rule = RuleRegistry.register