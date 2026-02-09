from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
    
    id: UUID
    created_at: datetime
    updated_at: datetime

class BaseCreateSchema(BaseModel):
    model_config = ConfigDict()

class BaseUpdateSchema(BaseModel):
    model_config = ConfigDict()