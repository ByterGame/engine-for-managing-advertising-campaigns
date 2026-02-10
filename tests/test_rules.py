import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import patch
from models.enums import Statuses


class TestRulesSimple:
    
    @pytest.mark.asyncio
    async def test_management_disabled_rule(self):
        """Тест правила: управление выключено"""
        from rules_engine.rules.rule_management import ManagementRule
        
        rule = ManagementRule()
        
        campaign_data = {
            "is_managed": False,
            "current_status": Statuses.ACTIVE
        }
        
        result = await rule.evaluate(
            campaign_data=campaign_data,
            schedules=[],
            current_time=None
        )
        assert result == Statuses.ACTIVE
        assert rule.name == "management_disabled"
    
    @pytest.mark.asyncio
    async def test_management_enabled_rule(self):
        """Тест правила: управление включено"""
        from rules_engine.rules.rule_management import ManagementRule
        
        rule = ManagementRule()
        
        campaign_data = {
            "is_managed": True,
            "current_status": Statuses.ACTIVE
        }
        
        result = await rule.evaluate(
            campaign_data=campaign_data,
            schedules=[],
            current_time=None
        )
        assert result is None
        assert rule.priority == 1
    
    @pytest.mark.asyncio
    async def test_schedule_rule_outside_schedule(self):
        """Тест правила расписания (вне активного окна)"""
        from rules_engine.rules.rule_schedule import ScheduleRule
        
        rule = ScheduleRule()
        
        campaign_data = {
            "schedule_enabled": True,
            "current_status": Statuses.ACTIVE
        }
        
        schedules = [{
            "day_of_week": 0,
            "start_time": time(9, 0),
            "end_time": time(18, 0)
        }]
        
        with patch('rules_engine.rules.rule_schedule.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 22, 0, 0)
            
            result = await rule.evaluate(
                campaign_data=campaign_data,
                schedules=schedules,
                current_time=None
            )
            
            assert result == Statuses.PAUSED
            assert rule.name == "schedule"
            assert "Текущее время: 22:00" in rule.get_details()
    
    @pytest.mark.asyncio
    async def test_schedule_rule_inside_schedule(self):
        """Тест правила расписания (внутри активного окна)"""
        from rules_engine.rules.rule_schedule import ScheduleRule
        
        rule = ScheduleRule()
        
        campaign_data = {
            "schedule_enabled": True,
            "current_status": Statuses.ACTIVE
        }
        
        schedules = [{
            "day_of_week": 0, 
            "start_time": time(9, 0),
            "end_time": time(18, 0)
        }]
        
        with patch('rules_engine.rules.rule_schedule.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 1, 10, 0, 0)
            
            result = await rule.evaluate( 
                campaign_data=campaign_data,
                schedules=schedules,
                current_time=None
            )
            
            assert result is None 
            assert rule.get_details() == ""
    
    @pytest.mark.asyncio
    async def test_stock_rule_low_stock(self):
        """Тест правила: мало остатков"""
        from rules_engine.rules.rule_stock import StockRule
        
        rule = StockRule()
        
        campaign_data = {
            "stock_days_min": 5,
            "stock_days_left": 3,
            "current_status": Statuses.ACTIVE
        }
        
        result = await rule.evaluate(
            campaign_data=campaign_data,
            schedules=[],
            current_time=None
        )
        
        assert result == Statuses.PAUSED
        assert rule.name == "low_stock"
        assert "Остатков хватит на 3 дней" in rule.get_details()
    
    @pytest.mark.asyncio
    async def test_stock_rule_sufficient_stock(self):
        """Тест правила: достаточно остатков"""
        from rules_engine.rules.rule_stock import StockRule
        
        rule = StockRule()
        
        campaign_data = {
            "stock_days_min": 5,
            "stock_days_left": 10,
            "current_status": Statuses.ACTIVE
        }
        
        result = await rule.evaluate(
            campaign_data=campaign_data,
            schedules=[],
            current_time=None
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_budget_rule_exceeded(self):
        """Тест правила: превышен бюджет"""
        from rules_engine.rules.rule_budget import BudgetRule
        
        rule = BudgetRule()
        
        campaign_data = {
            "budget_limit": Decimal('1000.00'),
            "spend_today": Decimal('1500.00'),
            "current_status": Statuses.ACTIVE
        }
        
        result = await rule.evaluate(
            campaign_data=campaign_data,
            schedules=[],
            current_time=None
        )
        
        assert result == Statuses.PAUSED
        assert rule.name == "budget_exceeded"
        assert "превышает дневной лимит" in rule.get_details()
    
    @pytest.mark.asyncio
    async def test_budget_rule_within_limit(self):
        """Тест правила: бюджет в пределах лимита"""
        from rules_engine.rules.rule_budget import BudgetRule
        
        rule = BudgetRule()
        
        campaign_data = {
            "budget_limit": Decimal('1000.00'),
            "spend_today": Decimal('500.00'),
            "current_status": Statuses.ACTIVE
        }
        
        result = await rule.evaluate(
            campaign_data=campaign_data,
            schedules=[],
            current_time=None
        )
        
        assert result is None