from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.base import Base, engine
from app.api.rest.sessions import router as sessions_router
from app.api.ws.pose import router as pose_ws_router

# Import models so SQLAlchemy registers them with Base.metadata
import app.models.db.workout_session  # noqa: F401
import app.models.db.metric  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Stretch App API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router, prefix="/api/v1")
app.include_router(pose_ws_router, prefix="/ws")


@app.get("/health")
async def health():
    return {"status": "running"}
