from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from uuid import UUID
from typing import Optional, Dict, Any
import json
from models.enums import Statuses
from . import BaseSchema, BaseCreateSchema, BaseUpdateSchema

class RuleEvaluationLogBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    compaign_id: UUID = Field(...)
    triggered_rule: Optional[str] = Field(None, max_length=80)
    previous_target: Statuses = Statuses.PAUSED
    new_target: Statuses = Statuses.PAUSED
    context: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('triggered_rule')
    @classmethod
    def validate_triggered_rule(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            return None
        return value.strip() if value else None
    
    @field_validator('context')
    @classmethod
    def validate_context(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        json_str = json.dumps(value, ensure_ascii=False)
        if len(json_str) > 100000:
            raise ValueError('Context too large (max 100KB)')
        
        cleaned = {}
        for key, val in value.items():
            if isinstance(val, (str, bytes)):
                if len(str(val)) > 10000:
                    cleaned[key] = str(val)[:10000] + "..."
                else:
                    cleaned[key] = val
            else:
                cleaned[key] = val
        
        return cleaned
    

class RuleEvaluationLogCreate(RuleEvaluationLogBase, BaseCreateSchema):
    pass

class RuleEvaluationLogUpdate(BaseUpdateSchema):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    compaign_id: Optional[UUID] = None
    triggered_rule: Optional[str] = Field(None, max_length=80)
    previous_target: Optional[Statuses] = None
    new_target: Optional[Statuses] = None
    context: Optional[Dict[str, Any]] = None
    
    @field_validator('context')
    @classmethod
    def validate_context_update(cls, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if value is not None:
            json_str = json.dumps(value, ensure_ascii=False)
            if len(json_str) > 100000:
                raise ValueError('Context too large (max 100KB)')
        return value

class RuleEvaluationLogRead(RuleEvaluationLogBase, BaseSchema):
    pass
