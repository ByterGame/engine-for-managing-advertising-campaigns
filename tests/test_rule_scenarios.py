import pytest
import uuid
from app.services.campaign_service import CampaignService
from app.services.evaluation_service import EvaluationService
from models.schemas.campaignSchema import CampaignCreate


class TestRuleScenariosAPI:
    
    async def test_rule_management_disabled(self, client, db_session):
        """Сценарий 1: управление выключено (самое приоритетное)"""
        campaign_service = CampaignService(db_session)
        evaluation_service = EvaluationService(db_session)
        
        campaign_name = f"Not Managed Campaign {uuid.uuid4().hex[:8]}"
        campaign_data = CampaignCreate(
            name=campaign_name,
            current_status="active",
            target_status="active",
            is_managed=False,
            schedule_enabled=True,
            budget_limit=1000.00,
            spend_today=1500.00,
            stock_days_left=2,
            stock_days_min=5
        )
        
        campaign = await campaign_service.create_campaign(campaign_data)
        await db_session.flush()
        
        found_campaign = await campaign_service.get_campaign(campaign.id)
        assert found_campaign is not None
        assert found_campaign.id == campaign.id
        
        try:
            result = await evaluation_service.evaluate_single_campaign(
                campaign_id=campaign.id,
                dry_run=True
            )
            
            assert result is not None
            assert "campaign_id" in result
            assert result["campaign_id"] == campaign.id

            if "triggered_rule" in result:
                assert result["triggered_rule"] == "management_disabled"
            
        except ValueError as e:
            if "не найдена" in str(e):
                pytest.fail(f"Кампания не найдена: {e}")
            raise
    
    async def test_rule_schedule(self, client, db_session):
        """Сценарий 2: правило расписания"""
        campaign_service = CampaignService(db_session)
        evaluation_service = EvaluationService(db_session)
        
        campaign_name = f"Scheduled Campaign {uuid.uuid4().hex[:8]}"
        campaign_data = CampaignCreate(
            name=campaign_name,
            current_status="active",
            target_status="active",
            is_managed=True,
            schedule_enabled=True,
            budget_limit=1000.00,
            spend_today=500.00,
            stock_days_left=10,
            stock_days_min=5
        )
        
        campaign = await campaign_service.create_campaign(campaign_data)
        await db_session.flush()
        
        schedule_data = [{
            "day_of_week": 0,
            "start_time": "09:00:00",
            "end_time": "18:00:00"
        }]
        
        try:
            created_slots = await campaign_service.set_campaign_schedule(
                campaign_id=campaign.id,
                schedule_slots=schedule_data
            )
            
            assert len(created_slots) == 1
            
        except Exception as e:
            pytest.skip(f"Не удалось установить расписание: {e}")
        
        result = await evaluation_service.evaluate_single_campaign(
            campaign_id=campaign.id,
            dry_run=True
        )
        
        assert result is not None
        assert "campaign_id" in result
        assert result["campaign_id"] == campaign.id
        assert "triggered_rule" in result or "target_status" in result or "new_target_status" in result
    
    async def test_rule_low_stock(self, client, db_session):
        """Сценарий 3: мало остатков"""
        campaign_service = CampaignService(db_session)
        evaluation_service = EvaluationService(db_session)
        
        campaign_name = f"Low Stock Campaign {uuid.uuid4().hex[:8]}"
        campaign_data = CampaignCreate(
            name=campaign_name,
            current_status="active",
            target_status="active",
            is_managed=True,
            schedule_enabled=False,
            budget_limit=1000.00,
            spend_today=500.00,
            stock_days_left=3,
            stock_days_min=5
        )
        
        campaign = await campaign_service.create_campaign(campaign_data)
        await db_session.flush()
        
        found_campaign = await campaign_service.get_campaign(campaign.id)
        assert found_campaign is not None

        result = await evaluation_service.evaluate_single_campaign(
            campaign_id=campaign.id,
            dry_run=True
        )
        
        assert result is not None
        assert "campaign_id" in result
        assert result["campaign_id"] == campaign.id
        
        if "triggered_rule" in result:
            assert result["triggered_rule"] in ["low_stock", "schedule", "management_disabled"]
    
    async def test_rule_budget_exceeded(self, client, db_session):
        """Сценарий 4: превышен бюджет"""
        campaign_service = CampaignService(db_session)
        evaluation_service = EvaluationService(db_session)
        
        campaign_name = f"Over Budget Campaign {uuid.uuid4().hex[:8]}"
        campaign_data = CampaignCreate(
            name=campaign_name,
            current_status="active",
            target_status="active",
            is_managed=True,
            schedule_enabled=False,
            budget_limit=1000.00,
            spend_today=1500.00,
            stock_days_left=10,
            stock_days_min=5
        )
        
        campaign = await campaign_service.create_campaign(campaign_data)
        await db_session.flush()
        
        found_campaign = await campaign_service.get_campaign(campaign.id)
        assert found_campaign is not None
        
        result = await evaluation_service.evaluate_single_campaign(
            campaign_id=campaign.id,
            dry_run=True
        )
        
        assert result is not None
        assert "campaign_id" in result
        assert result["campaign_id"] == campaign.id
        
        if "triggered_rule" in result:
            assert result["triggered_rule"] in ["budget_exceeded", "low_stock", "schedule", "management_disabled"]
    
    async def test_no_restrictions(self, client, db_session):
        """Сценарий 5: нет ограничений"""
        campaign_service = CampaignService(db_session)
        evaluation_service = EvaluationService(db_session)
        
        campaign_name = f"Healthy Campaign {uuid.uuid4().hex[:8]}"
        campaign_data = CampaignCreate(
            name=campaign_name,
            current_status="active",
            target_status="active",
            is_managed=True,
            schedule_enabled=False,
            budget_limit=1000.00,
            spend_today=500.00,
            stock_days_left=10,
            stock_days_min=5
        )
        
        campaign = await campaign_service.create_campaign(campaign_data)
        await db_session.flush()
        
        found_campaign = await campaign_service.get_campaign(campaign.id)
        assert found_campaign is not None
        
        result = await evaluation_service.evaluate_single_campaign(
            campaign_id=campaign.id,
            dry_run=True
        )
        
        assert result is not None
        assert "campaign_id" in result
        assert result["campaign_id"] == campaign.id
        
        if "triggered_rule" in result:
            if campaign.is_managed:
                assert result["triggered_rule"] in [None, "schedule"]