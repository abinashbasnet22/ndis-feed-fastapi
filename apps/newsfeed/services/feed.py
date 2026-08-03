from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from datetime import datetime, date
from apps.newsfeed.services.photos import get_or_assign_photo
from apps.newsfeed.models import News, NewsAnalytics


def get_time_ago(published_date: str) -> str:
    """converts a date/timestamp string to '3 days ago', 'today', 'yesterday' etc."""
    if not published_date:
        return ""
    try:
        date_part = published_date[:10]
        pub = datetime.strptime(date_part, "%Y-%m-%d").date()
        today = date.today()
        diff = (today - pub).days

        if diff == 0:
            return "today"
        elif diff == 1:
            return "yesterday"
        elif diff <= 7:
            return f"{diff} days ago"
        elif diff <= 14:
            return "1 week ago"
        elif diff <= 30:
            return f"{diff // 7} weeks ago"
        elif diff <= 60:
            return "1 month ago"
        else:
            return f"{diff // 30} months ago"
    except (ValueError, TypeError):
        return ""

async def build_items(db, rows):
    """shared helper — builds items list from rows"""
    items = []
    for row in rows:
        news      = row[0]
        analytics = row[1]

        photo_url = await get_or_assign_photo(
            db=db,
            news=news,
            primary_filter=analytics.primary_filter   if analytics else None,
            secondary_filter=analytics.secondary_filter if analytics else None,
        )

        items.append({
            "news":      news,
            "analytics": analytics,
            "time_ago":  get_time_ago(news.published_date),
            "photo_url": photo_url,
        })
    return items

async def get_feed(
    db: AsyncSession,
    cursor: Optional[int] = None,
    limit: int = 20,
    primary_filter: Optional[str] = None,
    secondary_filter: Optional[str] = None,
):
    query = (
        select(News, NewsAnalytics)
        .outerjoin(NewsAnalytics, NewsAnalytics.news_id == News.id)
        .where(News.ndis_relevant == True)
        .order_by(desc(News.id))
        .limit(limit + 1)
    )

    if cursor:
        query = query.where(News.id < cursor)

    if primary_filter and primary_filter.lower() != "all":
        query = query.where(
            NewsAnalytics.primary_filter.any(primary_filter)
            )

    if secondary_filter:
        query = query.where(
                NewsAnalytics.secondary_filter.any(secondary_filter)
            )
    

    result = await db.execute(query)
    rows = result.all()

    has_more = len(rows) > limit
    rows = rows[:limit]

    items = await build_items(db, rows)
    next_cursor = rows[-1][0].id if has_more and rows else None
    return {
        "items":       items,
        "next_cursor": next_cursor,
        "has_more":    has_more,
        "anchor_id":   None,
    }

async def get_feed_at_article(
    db: AsyncSession,
    anchor_id: int,
    limit: int = 20,
    primary_filter: Optional[str] = None,
    secondary_filter: Optional[str] = None,
):
    query = (
        select(News, NewsAnalytics)
        .outerjoin(NewsAnalytics, NewsAnalytics.news_id == News.id)
        .where(
            News.ndis_relevant == True,
            News.id <= anchor_id,
        )
        .order_by(desc(News.id))
        .limit(limit + 1)
    )
    if primary_filter and primary_filter.lower() != "all":
        query = query.where(
            NewsAnalytics.primary_filter.any(primary_filter)
        )

    if secondary_filter:
        query = query.where(
            NewsAnalytics.secondary_filter.any(secondary_filter)
        )

    result   = await db.execute(query)
    rows     = result.all()
    has_more = len(rows) > limit
    rows     = rows[:limit]
    items    = await build_items(db, rows)

    next_cursor = rows[-1][0].id if has_more and rows else None
    return {
        "items":       items,
        "next_cursor": next_cursor,
        "has_more":    has_more,
        "anchor_id":   anchor_id,
    }


async def get_news_by_id(db: AsyncSession, news_id: int):
    result = await db.execute(
        select(News, NewsAnalytics)
        .outerjoin(NewsAnalytics, NewsAnalytics.news_id == News.id)
        .where(News.id == news_id)
    )
    row = result.first()
    if not row:
        return None

    news      = row[0]
    analytics = row[1]

    photo_url = await get_or_assign_photo(
        db=db,
        news=news,
        primary_filter=analytics.primary_filter   if analytics else None,
        secondary_filter=analytics.secondary_filter if analytics else None,
    )

    return {
        "news":      news,
        "analytics": analytics,
        "time_ago":  get_time_ago(news.published_date),
        "photo_url": photo_url,
    }