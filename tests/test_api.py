class TestCampaignAPISimple:
    def test_root_endpoint(self, client):
        """Тест корневого эндпоинта"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Campaign Rules Engine Test Task" in data["message"]
    
    def test_health_check(self, client):
        """Тест health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_create_campaign(self, client, sample_campaign_data):
        """Тест создания кампании"""
        response = client.post("/campaigns", json=sample_campaign_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_campaign_data["name"]
        assert "id" in data
        assert data["is_managed"] == sample_campaign_data["is_managed"]
    
    def test_get_campaign(self, client, campaign_in_db):
        """Тест получения кампании по ID"""
        response = client.get(f"/campaigns/{campaign_in_db.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(campaign_in_db.id)
        assert data["name"] == campaign_in_db.name
    
    def test_update_campaign(self, client, campaign_in_db):
        """Тест обновления кампании"""
        update_data = {
            "name": "Updated Campaign Name",
            "budget_limit": 2000.00
        }
        
        response = client.patch(f"/campaigns/{campaign_in_db.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert float(data["budget_limit"]) == update_data["budget_limit"]


class TestScheduleAPI:
    
    def test_set_and_get_schedule(self, client, campaign_in_db, sample_schedule_data):
        """Тест установки и получения расписания"""
        client.patch(f"/campaigns/{campaign_in_db.id}", json={"schedule_enabled": True})
        
        response = client.put(
            f"/campaigns/{campaign_in_db.id}/schedule",
            json=sample_schedule_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        
        if "slots" in data:
            assert len(data["slots"]) == len(sample_schedule_data)
        else:
            assert "schedule_enabled" in data
            assert data["schedule_enabled"] is True
        
        response = client.get(f"/campaigns/{campaign_in_db.id}/schedule")
        assert response.status_code == 200
        data = response.json()
        
        if isinstance(data, list):
            assert len(data) == len(sample_schedule_data)
        elif isinstance(data, dict) and "slots" in data:
            assert len(data["slots"]) == len(sample_schedule_data)
        else:
            assert data
    
    def test_delete_schedule(self, client, campaign_in_db, sample_schedule_data):
        """Тест удаления расписания"""
        client.patch(f"/campaigns/{campaign_in_db.id}", json={"schedule_enabled": True})
        client.put(f"/campaigns/{campaign_in_db.id}/schedule", json=sample_schedule_data)
        
        response = client.delete(f"/campaigns/{campaign_in_db.id}/schedule")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        response = client.get(f"/campaigns/{campaign_in_db.id}/schedule")
        assert response.status_code == 200
        data = response.json()
        assert len(data["slots"]) == 0


class TestEvaluationAPI:
    
    def test_evaluate_campaign_dry_run(self, client, campaign_in_db):
        """Тест оценки кампании в режиме dry-run"""
        response = client.post(
            f"/campaigns/{campaign_in_db.id}/evaluate",
            params={"dry_run": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "new_target_status" in data
        assert "triggered_rule" in data
        assert "rule_details" in data
        assert "dry_run" in data
        assert data["dry_run"] is True
    
    def test_evaluate_all_campaigns(self, client):
        """Тест оценки всех кампаний"""
        response = client.post(
            "/campaigns/evaluate-all",
            params={"dry_run": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "evaluated" in data
        assert "results" in data
        assert isinstance(data["results"], list)
    
    def test_evaluation_history(self, client, campaign_in_db):
        """Тест получения истории оценок"""
        client.post(f"/campaigns/{campaign_in_db.id}/evaluate", params={"dry_run": False})
        
        response = client.get(
            f"/campaigns/{campaign_in_db.id}/evaluation-history",
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "entries" in data
        assert "total" in data
        assert isinstance(data["entries"], list)