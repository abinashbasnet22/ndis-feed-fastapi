from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from apps.events import services
from apps.events.schemas import EventsResponse

router = APIRouter(prefix="/events", tags=["events"])


# ── events feed (infinite scroll) ───────────────────────────────────
@router.get("/", response_model=EventsResponse)
async def get_events(
    cursor:   Optional[int] = Query(None, description="last seen event id"),
    limit:    int           = Query(20,   description="items per load"),
    category: Optional[str] = Query(None, description="filter by category"),
    db: AsyncSession = Depends(get_db),
):
    return await services.get_events(db, cursor=cursor, limit=limit, category=category)


# ── single event ─────────────────────────────────────────────────────
@router.get("/{event_id}")
async def get_event_by_id(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await services.get_event_by_id(db, event_id)
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return result