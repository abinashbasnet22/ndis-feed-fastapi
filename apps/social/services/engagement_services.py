from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.social.models import ArticleLike, ArticleComment, ArticleBookmark, ArticleShare
from apps.newsfeed.models import News  # for bookmark listing joins — adjust import if your News model lives elsewhere
from apps.auth.models import User

DEFAULT_PAGE_LIMIT = 20

# ==================== Feed enrichment (batch, no N+1) ====================

async def get_engagement_map(
    db: AsyncSession, news_ids: List[int], user_id: Optional[int]
) -> dict:
    """One call per feed page: returns
    {news_id: {like_count, comment_count, is_liked, is_bookmarked}}
    for every news_id in the batch, in a fixed number of queries regardless
    of page size (2 always, +2 more only if a user is logged in)."""
    if not news_ids:
        return {}

    like_counts_result = await db.execute(
        select(ArticleLike.news_id, func.count())
        .where(ArticleLike.news_id.in_(news_ids))
        .group_by(ArticleLike.news_id)
    )
    like_counts = dict(like_counts_result.all())

    comment_counts_result = await db.execute(
        select(ArticleComment.news_id, func.count())
        .where(ArticleComment.news_id.in_(news_ids), ArticleComment.is_deleted.is_(False))
        .group_by(ArticleComment.news_id)
    )
    comment_counts = dict(comment_counts_result.all())

    liked_ids, bookmarked_ids = set(), set()
    if user_id:
        liked_result = await db.execute(
            select(ArticleLike.news_id).where(
                ArticleLike.user_id == user_id, ArticleLike.news_id.in_(news_ids)
            )
        )
        liked_ids = {row[0] for row in liked_result.all()}

        bookmarked_result = await db.execute(
            select(ArticleBookmark.news_id).where(
                ArticleBookmark.user_id == user_id, ArticleBookmark.news_id.in_(news_ids)
            )
        )
        bookmarked_ids = {row[0] for row in bookmarked_result.all()}

    return {
        news_id: {
            "like_count": like_counts.get(news_id, 0),
            "comment_count": comment_counts.get(news_id, 0),
            "is_liked": news_id in liked_ids,
            "is_bookmarked": news_id in bookmarked_ids,
        }
        for news_id in news_ids
    }

