from sqlalchemy import String, Numeric, Boolean, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from typing import Optional
from models.Base import Base
from models.enums import Statuses


class Campaign(Base):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    current_status: Mapped[Statuses] = mapped_column(Enum(Statuses, name="status_enum"),
                                                     default=Statuses.PAUSED,
                                                     nullable=False)
    
    target_status: Mapped[Statuses] = mapped_column(Enum(Statuses, name="status_enum"),
                                                    default=Statuses.PAUSED,
                                                    nullable=False)
    
    is_managed: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)

    budget_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(64, 2),
                                                            default=None)
    
    spend_today: Mapped[Decimal] = mapped_column(Numeric(64, 2),
                                                 default=Decimal("0.00"),
                                                 nullable=False)
    
    stock_days_left: Mapped[Optional[int]] = mapped_column(Integer(), default=None)

    stock_days_min: Mapped[Optional[int]] = mapped_column(Integer(), default=None)

    schedule_enabled: Mapped[bool] = mapped_column(Boolean(), default=False)
