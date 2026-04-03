"""
Rules-based feedback engine for squat form analysis.
Maps MetricsResult → list[FeedbackItem].
Add new exercise types by implementing additional rule sets.
"""
from app.models.schemas.pose import FeedbackItem, MetricsResult

# Squat thresholds
_SQUAT_DEPTH_THRESHOLD = 0.92      # hip_depth must reach this to count as deep enough
_SQUAT_FORWARD_LEAN_MAX = 40.0     # back_angle degrees before flagging forward lean
_SQUAT_ASYMMETRY_MAX = 15.0        # degree difference between left/right knee angles


def _squat_feedback(metrics: MetricsResult) -> list[FeedbackItem]:
    items: list[FeedbackItem] = []

    # Depth check: hip must descend to at least knee level
    if metrics.hip_depth is not None and metrics.hip_depth < _SQUAT_DEPTH_THRESHOLD:
        items.append(FeedbackItem(
            severity="warning",
            message="Squat deeper — hips should reach knee level",
            joint="hip",
        ))

    # Forward lean check
    if metrics.back_angle is not None and metrics.back_angle > _SQUAT_FORWARD_LEAN_MAX:
        severity = "critical" if metrics.back_angle > 55 else "warning"
        items.append(FeedbackItem(
            severity=severity,
            message="Reduce forward lean — keep chest up",
            joint="back",
        ))

    # Knee symmetry check
    if metrics.knee_angle_left is not None and metrics.knee_angle_right is not None:
        diff = abs(metrics.knee_angle_left - metrics.knee_angle_right)
        if diff > _SQUAT_ASYMMETRY_MAX:
            items.append(FeedbackItem(
                severity="warning",
                message="Uneven weight distribution — balance left and right",
                joint="knee",
            ))

    if not items:
        items.append(FeedbackItem(severity="info", message="Good form", joint=None))

    return items


_EXERCISE_RULES: dict[str, callable] = {
    "squat": _squat_feedback,
}


def generate_feedback(exercise: str, metrics: MetricsResult) -> list[FeedbackItem]:
    rule_fn = _EXERCISE_RULES.get(exercise.lower())
    if rule_fn is None:
        return []
    return rule_fn(metrics)
