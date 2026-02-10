from datetime import time
from pydantic import BaseModel, ConfigDict, Field, field_validator
from uuid import UUID
from typing import Optional
from . import BaseSchema, BaseCreateSchema, BaseUpdateSchema

class CampaignScheduleBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    campaign_id: UUID = Field(...)
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time
    
    @field_validator('end_time')
    @classmethod
    def validate_times(cls, end_time: time, info) -> time:
        if 'start_time' in info.data and end_time <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return end_time
    

class CampaignScheduleCreate(CampaignScheduleBase, BaseCreateSchema):
    pass

class CampaignScheduleUpdate(BaseUpdateSchema):
    campaign_id: Optional[UUID] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    
    @field_validator('end_time')
    @classmethod
    def validate_times_update(cls, end_time: time, info) -> time:
        if 'start_time' in info.data and info.data['start_time'] is not None:
            if end_time <= info.data['start_time']:
                raise ValueError('End time must be after start time')
        return end_time

class CampaignScheduleRead(CampaignScheduleBase, BaseSchema):
    pass
