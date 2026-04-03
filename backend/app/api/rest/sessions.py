import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.db.workout_session import WorkoutSession
from app.models.schemas.session import SessionCreate, SessionEnd, SessionResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = WorkoutSession(id=str(uuid.uuid4()), exercise_type=body.exercise_type)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkoutSession).where(WorkoutSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}/end", response_model=SessionResponse)
async def end_session(session_id: str, body: SessionEnd, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkoutSession).where(WorkoutSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.ended_at = datetime.now(timezone.utc)
    session.rep_count = body.rep_count
    await db.commit()
    await db.refresh(session)
    return session
