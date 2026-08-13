from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.social.models import ArticleLike, ArticleComment, ArticleBookmark, ArticleShare
from apps.newsfeed.models import News  # for bookmark listing joins — adjust import if your News model lives elsewhere
from apps.auth.models import User

DEFAULT_PAGE_LIMIT = 20

# ==================== Likes ====================

async def get_like_count(db: AsyncSession, news_id: int) -> int:
    result = await db.execute(select(func.count()).select_from(ArticleLike).where(ArticleLike.news_id == news_id))
    return result.scalar_one()


async def is_liked_by_user(db: AsyncSession, user_id: int, news_id: int) -> bool:
    result = await db.execute(
        select(ArticleLike).where(ArticleLike.user_id == user_id, ArticleLike.news_id == news_id)
    )
    return result.scalar_one_or_none() is not None


async def toggle_like(db: AsyncSession, user_id: int, news_id: int) -> Tuple[bool, int]:
    """Likes if not already liked, unlikes if already liked. Returns (liked, like_count)."""
    existing = await db.execute(
        select(ArticleLike).where(ArticleLike.user_id == user_id, ArticleLike.news_id == news_id)
    )
    like_row = existing.scalar_one_or_none()

    if like_row:
        await db.delete(like_row)
        await db.commit()
        liked = False
    else:
        db.add(ArticleLike(user_id=user_id, news_id=news_id))
        await db.commit()
        liked = True

    count = await get_like_count(db, news_id)
    return liked, count
