from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from models.enums import Statuses
from . import BaseSchema, BaseCreateSchema, BaseUpdateSchema

class CampaignBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = Field(..., min_length=1, max_length=255)
    current_status: Statuses = Statuses.PAUSED
    target_status: Statuses = Statuses.PAUSED
    is_managed: bool = False
    budget_limit: Optional[Decimal] = None
    spend_today: Decimal = Decimal("0.00")
    stock_days_left: Optional[int] = Field(None, ge=0, le=365)
    stock_days_min: Optional[int] = Field(None, ge=0, le=365)
    schedule_enabled: bool = False

class CampaignCreate(CampaignBase, BaseCreateSchema):
    pass

class CampaignUpdate(BaseUpdateSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    current_status: Optional[Statuses] = None
    target_status: Optional[Statuses] = None
    is_managed: Optional[bool] = None
    budget_limit: Optional[Decimal] = None
    spend_today: Optional[Decimal] = None
    stock_days_left: Optional[int] = Field(None, ge=0, le=365)
    stock_days_min: Optional[int] = Field(None, ge=0, le=365)
    schedule_enabled: Optional[bool] = None

class CampaignRead(CampaignBase, BaseSchema):
    pass