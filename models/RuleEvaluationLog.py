from sqlalchemy import String, Enum, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
from models.Base import Base
from models.enums import Statuses
import uuid


class RuleEvaluationLog(Base):
    __tablename__ = "rule_evaluation_logs"

    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                   ForeignKey("campaigns.id", ondelete='CASCADE'),
                                                   nullable=False,
                                                   index=True)
    
    triggered_rule: Mapped[Optional[str]] = mapped_column(String(80), default=None)
    
    previous_target: Mapped[Statuses] = mapped_column(Enum(Statuses, name="status_enum"), 
                                                      default=Statuses.PAUSED,
                                                      nullable=False)
    
    new_target: Mapped[Statuses] = mapped_column(Enum(Statuses, name="status_enum"),
                                                 default=Statuses.PAUSED,
                                                 nullable=False)
    
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
