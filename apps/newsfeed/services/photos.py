from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
import random

from apps.newsfeed.models import StockPhoto
from config.base import settings

# ── Cloudflare R2 public URL ─────────────────────────────────────────
# R2 public URL format after enabling public access on bucket:
# https://pub-xxxx.r2.dev/photos/policy/policy_1.jpg
#
# ── AWS S3 public URL (commented out — swap in if moving to AWS) ─────
# f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/photos"

def get_base_url() -> str:
    if settings.ENVIRONMENT == "production":
        # Cloudflare R2 public bucket URL
        # get this from R2 dashboard → your bucket → Settings → Public URL
        return f"{settings.R2_PUBLIC_URL}/photos"

        # AWS S3 — uncomment below and comment above if switching to AWS
        # return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/photos"
    else:
        # local development — serve from FastAPI static files
        return "http://localhost:8000/static/photos"


VALID_PRIMARIES   = {"policy", "funding", "community", "workforce", "general"}
VALID_SECONDARIES = {"provider", "participant", "support_coordinator", "allied_health"}


def clean(value: str) -> str:
    return value.lower().strip().replace(" ", "_")


async def get_least_used(db: AsyncSession, topic: str) -> Optional[StockPhoto]:
    result = await db.execute(
        select(StockPhoto)
        .where(StockPhoto.topic == topic)
        .order_by(StockPhoto.used_count.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_photo_for_article(
    db: AsyncSession,
    primary_filter:   Optional[list] = None,
    secondary_filter: Optional[list] = None,
) -> Optional[str]:

    # extract all valid primaries — randomly pick one
    valid_primaries = [
        clean(p) for p in (primary_filter or [])
        if clean(p) in VALID_PRIMARIES
    ]

    # extract all valid secondaries — ignore "others" or unknown
    valid_secondaries = [
        clean(s) for s in (secondary_filter or [])
        if clean(s) in VALID_SECONDARIES
    ]

    # randomly pick one from each list
    primary   = random.choice(valid_primaries)   if valid_primaries   else None
    secondary = random.choice(valid_secondaries) if valid_secondaries else None

    photo = None

    # priority 1 — combined topic e.g. policy_provider
    if primary and secondary:
        photo = await get_least_used(db, f"{primary}_{secondary}")

    # priority 2 — primary only e.g. policy
    if not photo and primary:
        photo = await get_least_used(db, primary)

    # priority 3 — general fallback
    if not photo:
        photo = await get_least_used(db, "general")

    if not photo:
        return None

    # increment used count so next article gets a different photo
    await db.execute(
        update(StockPhoto)
        .where(StockPhoto.id == photo.id)
        .values(used_count=photo.used_count + 1)
    )
    await db.commit()

    base_url = get_base_url()
    return f"{base_url}/{photo.topic}/{photo.filename}"