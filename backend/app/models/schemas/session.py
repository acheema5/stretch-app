from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    exercise_type: str


class SessionEnd(BaseModel):
    rep_count: int


class SessionResponse(BaseModel):
    id: str
    exercise_type: str
    started_at: datetime
    ended_at: datetime | None
    rep_count: int

    model_config = {"from_attributes": True}
