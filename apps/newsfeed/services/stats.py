from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta

from apps.newsfeed.models import News, NewsAnalytics


def date_since(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


def _pct_change(current: int, previous: int) -> int:
    if not previous:
        return 100 if current else 0
    return round(((current - previous) / previous) * 100)


async def get_weekly_stats(db: AsyncSession):

    this_week       = date_since(7)
    last_week_start = date_since(14)
    last_week_end   = date_since(7)

    this_total = await db.scalar(
        select(func.count(News.id))
        .where(News.published_date >= this_week)
    )
    last_total = await db.scalar(
        select(func.count(News.id))
        .where(
            News.published_date >= last_week_start,
            News.published_date < last_week_end,
        )
    )

    this_urgent = await db.scalar(
        select(func.count(NewsAnalytics.id))
        .join(News, News.id == NewsAnalytics.news_id)
        .where(
            News.published_date >= this_week,
            func.lower(NewsAnalytics.urgency) == "critical",
        )
    )
    last_urgent = await db.scalar(
        select(func.count(NewsAnalytics.id))
        .join(News, News.id == NewsAnalytics.news_id)
        .where(
            News.published_date >= last_week_start,
            News.published_date < last_week_end,
            func.lower(NewsAnalytics.urgency) == "critical",
        )
    )

    top_type_result = await db.execute(
        select(
            NewsAnalytics.key_element_type,
            func.count().label("count"),
        )
        .join(News, News.id == NewsAnalytics.news_id)
        .where(
            News.published_date >= this_week,
            NewsAnalytics.key_element_type.isnot(None),
        )
        .group_by(NewsAnalytics.key_element_type)
        .order_by(desc("count"))
        .limit(1)
    )
    top_type_row   = top_type_result.first()
    top_type       = top_type_row[0] if top_type_row else "N/A"
    top_type_count = top_type_row[1] if top_type_row else 0

    top_state_result = await db.execute(
        select(
            func.unnest(NewsAnalytics.affected_states).label("state"),
            func.count().label("count"),
        )
        .join(News, News.id == NewsAnalytics.news_id)
        .where(
            News.published_date >= this_week,
            NewsAnalytics.affected_states.isnot(None),
        )
        .group_by("state")
        .order_by(desc("count"))
        .limit(1)
    )
    top_state_row   = top_state_result.first()
    top_state       = top_state_row[0] if top_state_row else "N/A"
    top_state_count = top_state_row[1] if top_state_row else 0

    return {
        "articles": {
            "count":      this_total or 0,
            "change_pct": _pct_change(this_total, last_total),
        },
        "urgent_alerts": {
            "count":      this_urgent or 0,
            "change_pct": _pct_change(this_urgent, last_urgent),
        },
        "top_key_element": {
            "type":  top_type,
            "count": top_type_count,
        },
        "top_state": {
            "state": top_state,
            "count": top_state_count,
        },
    }