import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String, ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    knee_angle_left: Mapped[float | None] = mapped_column(Float, nullable=True)
    knee_angle_right: Mapped[float | None] = mapped_column(Float, nullable=True)
    hip_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    back_angle: Mapped[float | None] = mapped_column(Float, nullable=True)
    hip_depth: Mapped[float | None] = mapped_column(Float, nullable=True)
