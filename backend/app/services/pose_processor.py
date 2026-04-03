"""
PoseProcessor orchestrates a single frame through the pipeline:
  KeypointFrame → metrics → smoothed metrics → feedback → PoseFeedback

RepState tracks the squat rep cycle across frames. It lives in the WebSocket
connection handler so each connected client has isolated state.
"""
import time
from collections import deque
from enum import Enum

from app.models.schemas.pose import KeypointFrame, MetricsResult, PoseFeedback
from app.services import biomechanics, feedback_engine

_SMOOTHING_WINDOW = 5          # frames to average for noise reduction
_REP_DOWN_THRESHOLD = 110.0    # knee angle below this → squat bottom
_REP_UP_THRESHOLD = 150.0      # knee angle above this → standing (rep complete)


class _RepPhase(Enum):
    STANDING = "standing"
    SQUATTING = "squatting"


class RepState:
    """Per-connection mutable state for rep counting and angle smoothing."""

    def __init__(self) -> None:
        self.rep_count: int = 0
        self._phase: _RepPhase = _RepPhase.STANDING
        self._knee_history: deque[float] = deque(maxlen=_SMOOTHING_WINDOW)

    def update(self, metrics: MetricsResult) -> None:
        avg_knee = self._smooth_knee(metrics)
        if avg_knee is None:
            return

        if self._phase == _RepPhase.STANDING and avg_knee < _REP_DOWN_THRESHOLD:
            self._phase = _RepPhase.SQUATTING
        elif self._phase == _RepPhase.SQUATTING and avg_knee > _REP_UP_THRESHOLD:
            self._phase = _RepPhase.STANDING
            self.rep_count += 1

    def _smooth_knee(self, metrics: MetricsResult) -> float | None:
        """Average of left/right knee angles, smoothed over the rolling window."""
        values = [v for v in [metrics.knee_angle_left, metrics.knee_angle_right] if v is not None]
        if not values:
            return None
        self._knee_history.append(sum(values) / len(values))
        return sum(self._knee_history) / len(self._knee_history)


def _smooth_metrics(raw: MetricsResult, history: deque[MetricsResult]) -> MetricsResult:
    """Apply rolling-average smoothing across all float metrics."""
    history.append(raw)

    def avg(attr: str) -> float | None:
        vals = [getattr(m, attr) for m in history if getattr(m, attr) is not None]
        return sum(vals) / len(vals) if vals else None

    return MetricsResult(
        knee_angle_left=avg("knee_angle_left"),
        knee_angle_right=avg("knee_angle_right"),
        hip_angle_left=avg("hip_angle_left"),
        hip_angle_right=avg("hip_angle_right"),
        back_angle=avg("back_angle"),
        hip_depth=avg("hip_depth"),
    )


class PoseProcessor:
    """
    Stateless processor — call process_frame() for each incoming WebSocket frame.
    Pass the per-connection RepState and metrics_history in from the handler.
    """

    def process_frame(
        self,
        frame: KeypointFrame,
        rep_state: RepState,
        metrics_history: deque[MetricsResult],
    ) -> PoseFeedback:
        raw_metrics = biomechanics.compute_metrics(frame.keypoints)
        smoothed = _smooth_metrics(raw_metrics, metrics_history)
        rep_state.update(smoothed)
        items = feedback_engine.generate_feedback(frame.exercise, smoothed)

        return PoseFeedback(
            timestamp=time.time(),
            metrics=smoothed,
            feedback=items,
            rep_count=rep_state.rep_count,
        )
