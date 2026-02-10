from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from models.enums import Statuses


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int


class EvaluateResponse(BaseModel):
    """Ответ для эндпоинта /campaigns/{id}/evaluate"""
    model_config = ConfigDict(from_attributes=True)
    
    campaign_id: UUID
    campaign_name: str
    current_status: Statuses
    previous_target_status: Statuses
    new_target_status: Statuses
    triggered_rule: Optional[str] = None
    rule_details: str
    needs_sync: bool
    dry_run: bool = False
    log_entry_id: Optional[UUID] = None
    evaluated_at: datetime
    
    @field_validator('log_entry_id', mode='before')
    @classmethod
    def validate_log_entry_id(cls, v):
        return v


class BatchEvaluateResult(BaseModel):
    """Один результат из batch оценки"""
    model_config = ConfigDict(from_attributes=True)
    
    campaign_id: UUID
    campaign_name: str
    current_status: Optional[Statuses] = None
    previous_target_status: Optional[Statuses] = None
    new_target_status: Optional[Statuses] = None
    triggered_rule: Optional[str] = None
    rule_details: Optional[str] = None
    needs_sync: Optional[bool] = None
    error: Optional[str] = None
    success: bool = True
    
    @field_validator('current_status', 'previous_target_status', 'new_target_status', mode='before')
    @classmethod
    def validate_status_fields(cls, v):
        return v


class BatchEvaluateResponse(BaseModel):
    """Ответ для эндпоинта /campaigns/evaluate-all"""
    evaluated: int
    total_managed: int
    needs_sync: int
    dry_run: bool = False
    evaluated_at: datetime
    results: List[BatchEvaluateResult]


class ScheduleSlotResponse(BaseModel):
    """Слот расписания для ответа API"""
    id: UUID
    day_of_week: int
    start_time: str
    end_time: str


class ScheduleResponse(BaseModel):
    """Ответ с расписанием кампании"""
    campaign_id: UUID
    schedule_enabled: bool
    slots: List[ScheduleSlotResponse]


class EvaluationHistoryEntry(BaseModel):
    """Запись из истории оценок"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    campaign_id: UUID
    triggered_rule: Optional[str]
    previous_target: Statuses
    new_target: Statuses
    context: Dict[str, Any]
    created_at: datetime


class EvaluationHistoryResponse(PaginatedResponse):
    """Пагинированный ответ с историей оценок"""
    entries: List[EvaluationHistoryEntry]



class CampaignSimpleResponse(BaseModel):
    """Упрощенный ответ для списка кампаний"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    current_status: Statuses
    target_status: Statuses
    is_managed: bool
    needs_sync: bool
    schedule_enabled: bool
    created_at: datetime


class CampaignsListResponse(PaginatedResponse):
    """Пагинированный ответ со списком кампаний"""
    campaigns: List[CampaignSimpleResponse]