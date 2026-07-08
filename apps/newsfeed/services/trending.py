from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, cast, DateTime
from datetime import datetime, timedelta, timezone

from apps.newsfeed.models import News, NewsAnalytics

# Matches ISO-ish date/timestamp strings like "2026-06-25" or
# "2026-06-25T08:01:00+00:00". Rows that don't match this are skipped
# rather than crashing the whole aggregate query.
ISO_TIMESTAMP_PATTERN = r'^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}:\d{2})?'


def since_datetime(days: int) -> datetime:
    """Return a UTC datetime cutoff for 'N days ago'."""
    return datetime.now(timezone.utc) - timedelta(days=days)


def valid_published_at():
    """Filter predicate: only rows whose published_at looks like a real timestamp."""
    return News.published_at.op("~")(ISO_TIMESTAMP_PATTERN)


async def get_trending(db: AsyncSession, days: int = 7, half_life_days: float = 3.0):
    since = since_datetime(days)
    published_at_ts = cast(News.published_at, DateTime(timezone=True))

    age_days = func.extract("epoch", func.now() - published_at_ts) / 86400.0
    recency_weight = func.power(2.0, -age_days / half_life_days)

    result = await db.execute(
        select(
            func.unnest(NewsAnalytics.keywords).label("keyword"),
            func.count().label("mentions"),
            func.sum(recency_weight).label("weighted_mentions"),
            func.avg(NewsAnalytics.impactness).label("avg_impact"),
        )
        .join(News, News.id == NewsAnalytics.news_id)
        .where(
            valid_published_at(),
            published_at_ts >= since,
            NewsAnalytics.keywords.isnot(None),
        )
        .group_by("keyword")
        .order_by(desc("weighted_mentions"))
        .limit(20)
    )
    rows = result.all()

    scored = []
    for row in rows:
        try:
            avg_impact = float(row.avg_impact or 0)
        except (ValueError, TypeError):
            avg_impact = 0

        weighted_mentions = float(row.weighted_mentions or 0)
        raw_score = (weighted_mentions * 2) + avg_impact

        scored.append({
            "keyword":  row.keyword,
            "mentions": row.mentions,
            "raw":      raw_score,
        })

    if not scored:
        return []

    # Percentile rank instead of ratio-to-max: each item's score reflects
    # what % of the other trending keywords it outperforms (or ties),
    # so one dominant keyword no longer flattens everything else to 0.
    raw_values = [s["raw"] for s in scored]
    n = len(raw_values)

    for s in scored:
        count_le = sum(1 for v in raw_values if v <= s["raw"])
        s["score"] = round((count_le / n) * 100)
        del s["raw"]

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:10]

async def get_emerging_keywords(db: AsyncSession):
    published_at_ts = cast(News.published_at, DateTime(timezone=True))

    recent_since   = since_datetime(7)
    baseline_start = since_datetime(30)
    baseline_end   = since_datetime(7)

    recent_result = await db.execute(
        select(
            func.unnest(NewsAnalytics.keywords).label("keyword"),
            func.count().label("count"),
        )
        .join(News, News.id == NewsAnalytics.news_id)
        .where(
            valid_published_at(),
            published_at_ts >= recent_since,
            NewsAnalytics.keywords.isnot(None),
        )
        .group_by("keyword")
    )
    recent = {row.keyword: row.count for row in recent_result.all()}

    baseline_result = await db.execute(
        select(
            func.unnest(NewsAnalytics.keywords).label("keyword"),
            func.count().label("count"),
        )
        .join(News, News.id == NewsAnalytics.news_id)
        .where(
            valid_published_at(),
            published_at_ts >= baseline_start,
            published_at_ts < baseline_end,
            NewsAnalytics.keywords.isnot(None),
        )
        .group_by("keyword")
    )
    baseline = {row.keyword: row.count for row in baseline_result.all()}

    emerging = []
    for keyword, recent_count in recent.items():
        base_count = baseline.get(keyword, 0)
        rise_pct = 100 if base_count == 0 else round(
            ((recent_count - base_count) / base_count) * 100
        )
        emerging.append({
            "keyword":      keyword,
            "recent_count": recent_count,
            "rise_pct":     rise_pct,
        })

    emerging.sort(key=lambda x: x["rise_pct"], reverse=True)
    return emerging[:10]