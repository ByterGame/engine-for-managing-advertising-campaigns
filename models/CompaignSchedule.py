from sqlalchemy import Integer, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import time
from models.Base import Base
import uuid


class CompaignSchedule(Base):
    __tablename__ = "compaign_schedules"

    compaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                   ForeignKey("compaigns.id", ondelete="CASCADE"),
                                                   nullable=False,
                                                   index=True)
    
    day_of_week: Mapped[int] = mapped_column(Integer(), nullable=False)

    start_time: Mapped[time] = mapped_column(Time(), nullable=False)

    end_time: Mapped[time] = mapped_column(Time(), nullable=False)
