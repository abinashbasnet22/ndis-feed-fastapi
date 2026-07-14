from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from apps.newsfeed.models import News, NewsAnalytics
from apps.newsfeed.services.feed import get_time_ago


async def get_news_by_keyword(
    db: AsyncSession,
    keyword: str,
    cursor: Optional[int] = None,
    limit: int = 20,
):
    query = (
        select(News, NewsAnalytics)
        .join(NewsAnalytics, NewsAnalytics.news_id == News.id)
        .where(
            News.ndis_relevant == True,
            NewsAnalytics.keywords.any(keyword)
        )
        .order_by(desc(News.published_date), desc(News.id))
        .limit(limit + 1)
    )

    if cursor:
        query = query.where(News.id < cursor)

    result = await db.execute(query)
    rows = result.all()

    has_more = len(rows) > limit
    rows = rows[:limit]

    items = []
    for row in rows:
        news      = row[0]
        analytics = row[1]
        items.append({
            "id":                    news.id,
            "headline":              analytics.headline or news.title,
            "snippet":               news.snippet,
            "published_date":        news.published_date,
            "time_ago":              get_time_ago(news.published_date),
            "sentiment_overall":     analytics.sentiment_overall,
            "sentiment_positive_pct": analytics.sentiment_positive_pct,
            "sentiment_negative_pct": analytics.sentiment_negative_pct,
            "sentiment_neutral_pct":  analytics.sentiment_neutral_pct,
            "keywords":              analytics.keywords,
            "urgency":               analytics.urgency,
            "impactness":            analytics.impactness,
            "url":                   news.url,
        })

    next_cursor = rows[-1][0].id if has_more and rows else None
    return {
        "keyword":     keyword,
        "items":       items,
        "next_cursor": next_cursor,
        "has_more":    has_more,
    }