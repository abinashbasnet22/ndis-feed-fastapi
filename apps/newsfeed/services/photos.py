from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional

from apps.newsfeed.models import News, StockPhoto
from config.base import settings
from core.database import SessionLocal


# ── primary filter mapping ───────────────────────────────────────────
# "other/others" in primary → None (skip → fall to general)
PRIMARY_MAP = {
    "other":     None,
    "others":    None,
    "policy":    "policy",
    "funding":   "funding",
    "community": "community",
    "workforce": "workforce",
    "general":   "general",
}

# ── secondary filter mapping ─────────────────────────────────────────
# "other/others" in secondary → None (skip → use primary only)
SECONDARY_MAP = {
    "other":         None,
    "others":        None,
    "provider":      "provider",
    "participant":   "participant",
    "support_coord": "support_coord",
    "allied_health": "allied_health",
}


def get_base_url() -> str:
    if settings.ENVIRONMENT == "production":
        return f"{settings.R2_PUBLIC_URL}/photos"
    return "http://localhost:8000/static/photos"


def clean(value: str) -> str:
    return value.lower().strip().replace(" ", "_")


def get_all_topics(
    primary_filter:   Optional[list] = None,
    secondary_filter: Optional[list] = None,
) -> list:
    """
    build ordered list of topics to check for photo selection
    priority 1 → combined  e.g. policy_provider
    priority 2 → primary only  e.g. policy
    priority 3 → general fallback
    other/others are mapped to None and skipped
    """

    # map and filter valid primaries
    valid_primaries = []
    for p in (primary_filter or []):
        mapped = PRIMARY_MAP.get(clean(p))
        if mapped and mapped not in valid_primaries:
            valid_primaries.append(mapped)

    # map and filter valid secondaries
    valid_secondaries = []
    for s in (secondary_filter or []):
        mapped = SECONDARY_MAP.get(clean(s))
        if mapped and mapped not in valid_secondaries:
            valid_secondaries.append(mapped)

    topics = []

    # priority 1 — all combinations of primary + secondary
    for p in valid_primaries:
        for s in valid_secondaries:
            topics.append(f"{p}_{s}")

    # priority 2 — primary only
    for p in valid_primaries:
        topics.append(p)

    # priority 3 — general fallback always last
    topics.append("general")

    return topics


async def get_or_assign_photo(
    db: AsyncSession,
    news: News,
    primary_filter:   Optional[list] = None,
    secondary_filter: Optional[list] = None,
) -> Optional[str]:
    """
    if news already has image assigned → return it directly (same image every time)
    if not → find least used image across all topic combinations → save to news → return it
    """

    # already assigned — return same image always
    if news.image_filename and news.image_topic:
        return f"{get_base_url()}/{news.image_topic}/{news.image_filename}"

    # use separate session for write — avoids conflict with outer feed session
    async with SessionLocal() as write_db:
        try:
            # re-fetch news in this session
            result = await write_db.execute(
                select(News).where(News.id == news.id)
            )
            fresh_news = result.scalar_one_or_none()

            # check again — another request may have assigned it already
            if fresh_news and fresh_news.image_filename and fresh_news.image_topic:
                return f"{get_base_url()}/{fresh_news.image_topic}/{fresh_news.image_filename}"

            # build topic priority list
            topics = get_all_topics(primary_filter, secondary_filter)

            # find least used photo across all valid topics
            photo_result = await write_db.execute(
                select(StockPhoto)
                .where(StockPhoto.topic.in_(topics))
                .order_by(StockPhoto.used_count.asc())
                .limit(1)
            )
            photo = photo_result.scalar_one_or_none()

            if not photo:
                return None

            # save permanently to news row
            await write_db.execute(
                update(News)
                .where(News.id == news.id)
                .values(
                    image_filename=photo.filename,
                    image_topic=photo.topic,
                )
            )

            # increment photo used count
            await write_db.execute(
                update(StockPhoto)
                .where(StockPhoto.id == photo.id)
                .values(used_count=photo.used_count + 1)
            )

            await write_db.commit()

            return f"{get_base_url()}/{photo.topic}/{photo.filename}"

        except Exception as e:
            await write_db.rollback()
            print(f"photo assign error for news {news.id}: {e}")
            return None