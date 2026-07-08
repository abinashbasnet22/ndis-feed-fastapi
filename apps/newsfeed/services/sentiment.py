from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import json

from apps.newsfeed.models import News, NewsAnalytics


def date_since(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")


async def get_sector_sentiment(db: AsyncSession, days: int = 30):
    result = await db.execute(
        select(NewsAnalytics.sentiment_aspect_notes)
        .join(News, News.id == NewsAnalytics.news_id)
        .where(
            News.published_date >= date_since(days),
            NewsAnalytics.sentiment_aspect_notes.isnot(None),
        )
    )
    rows = result.scalars().all()

    topic_counts: dict = {}

    for raw in rows:
        if not raw:
            continue
        try:
            notes = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(notes, list):
            continue

        for note in notes:
            if not note or not isinstance(note, dict):
                continue

            topic     = note.get("topic", "").strip()
            sentiment = note.get("sentiment", "").strip().lower()

            if not topic or not sentiment:
                continue

            if topic not in topic_counts:
                topic_counts[topic] = {"positive": 0, "negative": 0, "neutral": 0}

            if sentiment in topic_counts[topic]:
                topic_counts[topic][sentiment] += 1

    sentiment_data = []
    for topic, counts in topic_counts.items():
        total = counts["positive"] + counts["negative"] + counts["neutral"]
        if total == 0:
            continue

        net = round(((counts["positive"] - counts["negative"]) / total) * 100)
        sentiment_data.append({
            "topic":        topic,
            "positive_pct": round((counts["positive"] / total) * 100),
            "negative_pct": round((counts["negative"] / total) * 100),
            "neutral_pct":  round((counts["neutral"]  / total) * 100),
            "net":          net,
            "total":        total,
        })

    sentiment_data.sort(key=lambda x: x["total"], reverse=True)
    return sentiment_data[:10]