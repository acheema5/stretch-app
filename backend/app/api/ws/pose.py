"""
WebSocket endpoint for real-time pose analysis.

Path:  /ws/session/{session_id}
Flow:  connect → validate session → frame loop → disconnect
"""
import json
from collections import deque

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.models.db.workout_session import WorkoutSession
from app.models.schemas.pose import ErrorMessage, KeypointFrame
from app.services.pose_processor import PoseProcessor, RepState

router = APIRouter()

_processor = PoseProcessor()
_METRICS_HISTORY_SIZE = 5


async def _get_session(session_id: str) -> WorkoutSession | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WorkoutSession).where(WorkoutSession.id == session_id)
        )
        return result.scalar_one_or_none()


@router.websocket("/session/{session_id}")
async def pose_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    # Validate the session exists before entering the frame loop
    session = await _get_session(session_id)
    if session is None:
        await websocket.send_text(
            ErrorMessage(error=f"Session '{session_id}' not found").model_dump_json()
        )
        await websocket.close(code=4004)
        return

    # Per-connection state — isolated per client
    rep_state = RepState()
    metrics_history = deque(maxlen=_METRICS_HISTORY_SIZE)

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                frame = KeypointFrame.model_validate_json(raw)
            except (ValidationError, json.JSONDecodeError) as exc:
                await websocket.send_text(
                    ErrorMessage(error=f"Invalid frame: {exc}").model_dump_json()
                )
                continue  # keep connection alive, skip bad frame

            feedback = _processor.process_frame(frame, rep_state, metrics_history)
            await websocket.send_text(feedback.model_dump_json())

    except WebSocketDisconnect:
        pass  # client disconnected cleanly — nothing to do
