from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.social.models import ArticleLike, ArticleComment, ArticleBookmark, ArticleShare
from apps.newsfeed.models import News  # for bookmark listing joins — adjust import if your News model lives elsewhere
from apps.auth.models import User

DEFAULT_PAGE_LIMIT = 20


# ==================== Bookmarks ====================

async def is_bookmarked(db: AsyncSession, user_id: int, news_id: int) -> bool:
    result = await db.execute(
        select(ArticleBookmark).where(ArticleBookmark.user_id == user_id, ArticleBookmark.news_id == news_id)
    )
    return result.scalar_one_or_none() is not None


async def toggle_bookmark(db: AsyncSession, user_id: int, news_id: int) -> bool:
    """Returns the new bookmarked state."""
    existing = await db.execute(
        select(ArticleBookmark).where(ArticleBookmark.user_id == user_id, ArticleBookmark.news_id == news_id)
    )
    row = existing.scalar_one_or_none()

    if row:
        await db.delete(row)
        await db.commit()
        return False

    db.add(ArticleBookmark(user_id=user_id, news_id=news_id))
    await db.commit()
    return True


async def get_bookmarks(
    db: AsyncSession, user_id: int, cursor: Optional[int], limit: int = DEFAULT_PAGE_LIMIT
) -> Tuple[List[dict], Optional[int]]:
    """Cursor here is the bookmark's own id (not news_id), newest bookmark first."""
    query = (
        select(ArticleBookmark, News)
        .join(News, News.id == ArticleBookmark.news_id)
        .where(ArticleBookmark.user_id == user_id)
    )
    if cursor:
        query = query.where(ArticleBookmark.id < cursor)
    query = query.order_by(ArticleBookmark.id.desc()).limit(limit + 1)

    result = await db.execute(query)
    rows = result.all()

    next_cursor = None
    if len(rows) > limit:
        next_cursor = rows[limit - 1][0].id
        rows = rows[:limit]

    items = [
        {
            "news_id": news.id,
            "title": news.title,
            "snippet": news.snippet,
            "image_filename": news.image_filename,
            "bookmarked_at": bookmark.created_at,
        }
        for bookmark, news in rows
    ]
    return items, next_cursor
