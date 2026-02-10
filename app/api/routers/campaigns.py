from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.dependencies import get_campaign_service, get_evaluation_service
from app.api.responses import (
    MessageResponse,
    EvaluateResponse,
    BatchEvaluateResponse,
    ScheduleResponse,
    ScheduleSlotResponse,
    EvaluationHistoryResponse,
    EvaluationHistoryEntry,
    CampaignsListResponse,
    CampaignSimpleResponse
)
from models.schemas.campaignSchema import CampaignCreate, CampaignUpdate, CampaignRead
from models.schemas.campaignScheduleSchema import CampaignScheduleCreate
from app.services.campaign_service import CampaignService
from app.services.evaluation_service import EvaluationService


router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post(
    "",
    response_model=CampaignRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать кампанию",
    description="Создает новую рекламную кампанию"
)
async def create_campaign(
    campaign_data: CampaignCreate,
    campaign_service: CampaignService = Depends(get_campaign_service)
):
    try:
        campaign = await campaign_service.create_campaign(campaign_data)
        return campaign
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании кампании: {str(e)}"
        )


@router.get(
    "",
    response_model=CampaignsListResponse,
    summary="Список кампаний",
    description="Получить список кампаний с пагинацией и фильтрацией"
)
async def get_campaigns(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, le=1000, description="Сколько записей вернуть"),
    is_managed: Optional[bool] = Query(None, description="Фильтр по автоматическому управлению"),
    needs_sync: Optional[bool] = Query(None, description="Фильтр по необходимости синхронизации"),
    campaign_service: CampaignService = Depends(get_campaign_service)
):
    campaigns, total = await campaign_service.get_campaigns(
        skip=skip,
        limit=limit,
        is_managed=is_managed,
        needs_sync=needs_sync
    )
    
    campaign_responses = []
    for campaign in campaigns:
        needs_sync_flag = campaign.current_status != campaign.target_status
        campaign_responses.append(
            CampaignSimpleResponse(
                id=campaign.id,
                name=campaign.name,
                current_status=campaign.current_status,
                target_status=campaign.target_status,
                is_managed=campaign.is_managed,
                needs_sync=needs_sync_flag,
                schedule_enabled=campaign.schedule_enabled,
                created_at=campaign.created_at
            )
        )
    
    return CampaignsListResponse(
        total=total,
        skip=skip,
        limit=limit,
        campaigns=campaign_responses
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignRead,
    summary="Получить кампанию",
    description="Получить информацию о конкретной кампании"
)
async def get_campaign(
    campaign_id: UUID,
    campaign_service: CampaignService = Depends(get_campaign_service)
):
    campaign = await campaign_service.get_campaign(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Кампания с ID {campaign_id} не найдена"
        )
    
    return campaign


@router.patch(
    "/{campaign_id}",
    response_model=CampaignRead,
    summary="Обновить кампанию",
    description="Частично обновить данные кампании"
)
async def update_campaign(
    campaign_id: UUID,
    update_data: CampaignUpdate,
    campaign_service: CampaignService = Depends(get_campaign_service)
):
    campaign = await campaign_service.update_campaign(campaign_id, update_data)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Кампания с ID {campaign_id} не найдена"
        )
    
    return campaign


@router.put(
    "/{campaign_id}/schedule",
    response_model=ScheduleResponse,
    summary="Установить расписание",
    description="Установить или заменить расписание кампании"
)
async def set_campaign_schedule(
    campaign_id: UUID,
    schedule_slots: List[Dict[str, Any]],
    campaign_service: CampaignService = Depends(get_campaign_service)
):
    validated_slots = []
    for slot in schedule_slots:
        try:
            slot_with_campaign = {**slot, "campaign_id": campaign_id}
            validated_slot = CampaignScheduleCreate(**slot_with_campaign)
            validated_slots.append(validated_slot.model_dump(exclude={"campaign_id"}))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверный формат слота расписания: {str(e)}"
            )
    
    try:
        created_slots = await campaign_service.set_campaign_schedule(
            campaign_id=campaign_id,
            schedule_slots=validated_slots
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при установке расписания: {str(e)}"
        )
    
    slot_responses = []
    for slot in created_slots:
        slot_responses.append(
            ScheduleSlotResponse(
                id=str(slot.id),
                day_of_week=slot.day_of_week,
                start_time=slot.start_time.isoformat(),
                end_time=slot.end_time.isoformat()
            )
        )
    
    campaign = await campaign_service.get_campaign(campaign_id)
    
    return ScheduleResponse(
        campaign_id=str(campaign_id),
        schedule_enabled=campaign.schedule_enabled,
        slots=slot_responses
    )


@router.get(
    "/{campaign_id}/schedule",
    response_model=ScheduleResponse,
    summary="Получить расписание",
    description="Получить расписание кампании"
)
async def get_campaign_schedule(
    campaign_id: UUID,
    campaign_service: CampaignService = Depends(get_campaign_service)
):
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Кампания с ID {campaign_id} не найдена"
        )
    schedules = await campaign_service.get_campaign_schedules(campaign_id)
    slot_responses = []
    for schedule in schedules:
        slot_responses.append(
            ScheduleSlotResponse(
                id=str(schedule.id),
                day_of_week=schedule.day_of_week,
                start_time=schedule.start_time.isoformat(),
                end_time=schedule.end_time.isoformat()
            )
        )
    
    return ScheduleResponse(
        campaign_id=str(campaign_id),
        schedule_enabled=campaign.schedule_enabled,
        slots=slot_responses
    )


@router.delete(
    "/{campaign_id}/schedule",
    response_model=MessageResponse,
    summary="Удалить расписание",
    description="Удалить всё расписание кампании"
)
async def delete_campaign_schedule(
    campaign_id: UUID,
    campaign_service: CampaignService = Depends(get_campaign_service)
):
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Кампания с ID {campaign_id} не найдена"
        )
    
    deleted = await campaign_service.delete_campaign_schedule(campaign_id)
    
    if deleted:
        return MessageResponse(message="Расписание успешно удалено")
    else:
        return MessageResponse(
            message="Расписание не найдено или уже удалено",
            success=True
        )


@router.post(
    "/{campaign_id}/evaluate",
    response_model=EvaluateResponse,
    summary="Оценить кампанию",
    description="Вычислить target_status для кампании по правилам"
)
async def evaluate_campaign(
    campaign_id: UUID,
    dry_run: bool = Query(False, description="Dry-run режим"),
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    try:
        result = await evaluation_service.evaluate_single_campaign(
            campaign_id=campaign_id,
            dry_run=dry_run
        )
        
        result["campaign_id"] = str(result["campaign_id"])
        if result.get("log_entry_id"):
            result["log_entry_id"] = str(result["log_entry_id"])
        
        return EvaluateResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при оценке кампании: {str(e)}"
        )


@router.post(
    "/evaluate-all",
    response_model=BatchEvaluateResponse,
    summary="Оценить все кампании",
    description="Вычислить target_status для всех управляемых кампаний"
)
async def evaluate_all_campaigns(
    dry_run: bool = Query(False, description="Dry-run режим (не сохранять изменения)"),
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    try:
        result = await evaluation_service.evaluate_all_campaigns(dry_run=dry_run)
        for item in result["results"]:
            if "campaign_id" in item:
                item["campaign_id"] = str(item["campaign_id"])
        
        return BatchEvaluateResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при оценке всех кампаний: {str(e)}"
        )

@router.get(
    "/{campaign_id}/evaluation-history",
    response_model=EvaluationHistoryResponse,
    summary="История оценок",
    description="Получить историю вычислений правил для кампании"
)
async def get_evaluation_history(
    campaign_id: UUID,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, le=1000, description="Сколько записей вернуть"),
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    campaign_service = CampaignService(evaluation_service.db)
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Кампания с ID {campaign_id} не найдена"
        )
    logs, total = await evaluation_service.get_evaluation_history(
        campaign_id=campaign_id,
        skip=skip,
        limit=limit
    )
    entries = []
    for log in logs:
        entries.append(
            EvaluationHistoryEntry(
                id=str(log.id),
                campaign_id=str(log.campaign_id),
                triggered_rule=log.triggered_rule,
                previous_target=log.previous_target,
                new_target=log.new_target,
                context=log.context,
                created_at=log.created_at
            )
        )
    
    return EvaluationHistoryResponse(
        total=total,
        skip=skip,
        limit=limit,
        entries=entries
    )