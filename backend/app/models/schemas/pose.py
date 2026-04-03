from typing import Literal

from pydantic import BaseModel


class KeypointFrame(BaseModel):
    """Sent by the frontend each frame (~30fps)."""
    session_id: str
    timestamp: float
    exercise: str
    # landmark_name -> [x, y] normalized 0..1 in image space
    keypoints: dict[str, list[float]]


class FeedbackItem(BaseModel):
    severity: Literal["info", "warning", "critical"]
    message: str
    joint: str | None = None


class MetricsResult(BaseModel):
    knee_angle_left: float | None = None
    knee_angle_right: float | None = None
    hip_angle_left: float | None = None
    hip_angle_right: float | None = None
    back_angle: float | None = None
    hip_depth: float | None = None


class PoseFeedback(BaseModel):
    """Sent back to the frontend after each processed frame."""
    timestamp: float
    metrics: MetricsResult
    feedback: list[FeedbackItem]
    rep_count: int


class ErrorMessage(BaseModel):
    error: str
