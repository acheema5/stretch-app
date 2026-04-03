"""
Pure stateless geometry functions for computing biomechanical metrics.
All inputs are (x, y) tuples in normalized image coordinates (0..1).
"""
import math

from app.models.schemas.pose import MetricsResult

Point = tuple[float, float]

# MediaPipe landmark names used by this engine
REQUIRED_LANDMARKS = {
    "left_shoulder", "right_shoulder",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
}


def _angle_at_joint(a: Point, b: Point, c: Point) -> float:
    """Angle in degrees at point b formed by the rays b→a and b→c."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])

    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

    if mag_ba < 1e-6 or mag_bc < 1e-6:
        return 0.0

    cos_angle = dot / (mag_ba * mag_bc)
    cos_angle = max(-1.0, min(1.0, cos_angle))  # clamp for floating-point safety
    return math.degrees(math.acos(cos_angle))


def _angle_from_vertical(top: Point, bottom: Point) -> float:
    """
    Angle in degrees of the line (bottom → top) relative to vertical.
    0° = perfectly upright, 90° = horizontal.
    Uses image coordinates where y increases downward.
    """
    dx = top[0] - bottom[0]
    dy = bottom[1] - top[1]  # flip y so up = positive
    return math.degrees(math.atan2(abs(dx), max(abs(dy), 1e-6)))


def _midpoint(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def compute_metrics(keypoints: dict[str, list[float]]) -> MetricsResult:
    """
    Compute all biomechanical metrics from a keypoint dict.
    Returns a MetricsResult with None for any metric that can't be computed.
    """
    kp = keypoints  # alias for brevity

    def pt(name: str) -> Point | None:
        v = kp.get(name)
        return (v[0], v[1]) if v and len(v) >= 2 else None

    left_shoulder = pt("left_shoulder")
    right_shoulder = pt("right_shoulder")
    left_hip = pt("left_hip")
    right_hip = pt("right_hip")
    left_knee = pt("left_knee")
    right_knee = pt("right_knee")
    left_ankle = pt("left_ankle")
    right_ankle = pt("right_ankle")

    knee_angle_left = (
        _angle_at_joint(left_hip, left_knee, left_ankle)
        if all([left_hip, left_knee, left_ankle])
        else None
    )
    knee_angle_right = (
        _angle_at_joint(right_hip, right_knee, right_ankle)
        if all([right_hip, right_knee, right_ankle])
        else None
    )

    hip_angle_left = (
        _angle_at_joint(left_shoulder, left_hip, left_knee)
        if all([left_shoulder, left_hip, left_knee])
        else None
    )
    hip_angle_right = (
        _angle_at_joint(right_shoulder, right_hip, right_knee)
        if all([right_shoulder, right_hip, right_knee])
        else None
    )

    back_angle = None
    if all([left_shoulder, right_shoulder, left_hip, right_hip]):
        mid_shoulder = _midpoint(left_shoulder, right_shoulder)
        mid_hip = _midpoint(left_hip, right_hip)
        back_angle = _angle_from_vertical(mid_shoulder, mid_hip)

    # Hip depth: ratio of hip y to knee y. 1.0 = hip at knee level (parallel squat).
    # Values > 1.0 = below parallel. Uses average of left/right sides.
    hip_depth = None
    if all([left_hip, right_hip, left_knee, right_knee]):
        avg_hip_y = (left_hip[1] + right_hip[1]) / 2
        avg_knee_y = (left_knee[1] + right_knee[1]) / 2
        if avg_knee_y > 1e-6:
            hip_depth = avg_hip_y / avg_knee_y

    return MetricsResult(
        knee_angle_left=knee_angle_left,
        knee_angle_right=knee_angle_right,
        hip_angle_left=hip_angle_left,
        hip_angle_right=hip_angle_right,
        back_angle=back_angle,
        hip_depth=hip_depth,
    )
