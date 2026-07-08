from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from apps.events.models import Event


async def get_events(
    db: AsyncSession,
    cursor: Optional[int] = None,
    limit: int = 20,
    category: Optional[str] = None,
):
    query = (
        select(Event)
        .where(Event.ndis_relevant == True)
        .order_by(desc(Event.id))
        .limit(limit + 1)
    )

    if cursor:
        query = query.where(Event.id < cursor)

    if category:
        query = query.where(Event.categories.any(category))

    result = await db.execute(query)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = rows[-1].id if has_more and rows else None

    return {"items": rows, "next_cursor": next_cursor, "has_more": has_more}


async def get_event_by_id(db: AsyncSession, event_id: int):
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    return result.scalar_one_or_none()