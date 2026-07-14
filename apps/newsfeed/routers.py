from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from apps.newsfeed import services
from apps.newsfeed.schemas import FeedResponse, NewsFeedItem, KeywordFeedResponse

router = APIRouter(prefix="/newsfeed", tags=["Newsfeed"])


# ── feed (infinite scroll) ───────────────────────────────────────────

@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    cursor: Optional[int] = None,
    limit: int = 20,
    primary_filter: Optional[str] = None,
    secondary_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await services.get_feed(
        db, cursor=cursor, limit=limit,
        primary_filter=primary_filter, secondary_filter=secondary_filter,
    )


@router.get("/news/{news_id}", response_model=NewsFeedItem)
async def get_news_by_id(
    news_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await services.get_news_by_id(db, news_id)
    if not result:
        raise HTTPException(status_code=404, detail="Article not found")
    return result

# ── trending in ndis ─────────────────────────────────────────────────
@router.get("/trending")
async def get_trending(
    days: int = Query(7, description="7 or 30"),
    db: AsyncSession = Depends(get_db),
):
    return await services.get_trending(db, days=days)


# ── emerging keywords ────────────────────────────────────────────────
@router.get("/emerging-keywords")
async def get_emerging_keywords(
    db: AsyncSession = Depends(get_db),
):
    return await services.get_emerging_keywords(db)


# ── sector sentiment ─────────────────────────────────────────────────
@router.get("/sector-sentiment")
async def get_sector_sentiment(
    days: int = Query(30, description="7 or 30"),
    db: AsyncSession = Depends(get_db),
):
    return await services.get_sector_sentiment(db, days=days)


# ── this week stats ──────────────────────────────────────────────────
@router.get("/weekly-stats")
async def get_weekly_stats(
    db: AsyncSession = Depends(get_db),
):
    return await services.get_weekly_stats(db)


@router.get("/keyword-feed", response_model=KeywordFeedResponse)
async def get_news_by_keyword(
    keyword: str           = Query(..., description="e.g. Price Guide History"),
    cursor:  Optional[int] = Query(None),
    limit:   int           = Query(20),
    db: AsyncSession = Depends(get_db),
):
    return await services.get_news_by_keyword(
        db=db,
        keyword=keyword,
        cursor=cursor,
        limit=limit,
    )