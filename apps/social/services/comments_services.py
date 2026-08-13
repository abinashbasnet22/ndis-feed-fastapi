from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.social.models import ArticleLike, ArticleComment, ArticleBookmark, ArticleShare
from apps.newsfeed.models import News  # for bookmark listing joins — adjust import if your News model lives elsewhere
from apps.auth.models import User

DEFAULT_PAGE_LIMIT = 20

# ==================== Comments ====================

async def _reply_count(db: AsyncSession, comment_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(ArticleComment).where(
            ArticleComment.parent_comment_id == comment_id, ArticleComment.is_deleted.is_(False)
        )
    )
    return result.scalar_one()


async def _enrich_comments(db: AsyncSession, comments: List[ArticleComment]) -> List[dict]:
    """Attaches author info + reply_count to each comment in 2 extra queries total,
    instead of 2 queries per comment (N+1)."""
    if not comments:
        return []

    comment_ids = [c.id for c in comments]
    user_ids = list({c.user_id for c in comments})

    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_by_id = {u.id: u for u in users_result.scalars().all()}

    counts_result = await db.execute(
        select(ArticleComment.parent_comment_id, func.count())
        .where(ArticleComment.parent_comment_id.in_(comment_ids), ArticleComment.is_deleted.is_(False))
        .group_by(ArticleComment.parent_comment_id)
    )
    reply_counts = {parent_id: count for parent_id, count in counts_result.all()}

    enriched = []
    for c in comments:
        author = users_by_id.get(c.user_id)
        enriched.append(
            {
                "id": c.id,
                "news_id": c.news_id,
                "parent_comment_id": c.parent_comment_id,
                "content": c.content,
                "is_deleted": c.is_deleted,
                "author": {
                    "id": author.id if author else c.user_id,
                    "full_name": author.full_name if author else None,
                    "avatar_url": author.avatar_url if author else None,
                },
                "reply_count": reply_counts.get(c.id, 0),
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
        )
    return enriched


async def create_comment(
    db: AsyncSession, user_id: int, news_id: int, content: str, parent_comment_id: Optional[int]
) -> dict:
    if parent_comment_id is not None:
        parent = await db.execute(
            select(ArticleComment).where(
                ArticleComment.id == parent_comment_id, ArticleComment.news_id == news_id
            )
        )
        if parent.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")

    comment = ArticleComment(
        user_id=user_id, news_id=news_id, content=content, parent_comment_id=parent_comment_id
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    enriched = await _enrich_comments(db, [comment])
    return enriched[0]


async def get_comments(
    db: AsyncSession, news_id: int, cursor: Optional[int], limit: int = DEFAULT_PAGE_LIMIT
) -> Tuple[List[dict], Optional[int]]:
    """Top-level comments only (parent_comment_id IS NULL), newest first, cursor = last seen id."""
    query = select(ArticleComment).where(
        ArticleComment.news_id == news_id, ArticleComment.parent_comment_id.is_(None)
    )
    if cursor:
        query = query.where(ArticleComment.id < cursor)
    query = query.order_by(ArticleComment.id.desc()).limit(limit + 1)

    result = await db.execute(query)
    comments = list(result.scalars().all())

    next_cursor = None
    if len(comments) > limit:
        next_cursor = comments[limit - 1].id
        comments = comments[:limit]

    enriched = await _enrich_comments(db, comments)
    return enriched, next_cursor


async def get_replies(db: AsyncSession, parent_comment_id: int) -> List[dict]:
    result = await db.execute(
        select(ArticleComment)
        .where(ArticleComment.parent_comment_id == parent_comment_id)
        .order_by(ArticleComment.id.asc())
    )
    replies = list(result.scalars().all())
    return await _enrich_comments(db, replies)


async def update_comment(db: AsyncSession, comment_id: int, user_id: int, content: str) -> dict:
    result = await db.execute(select(ArticleComment).where(ArticleComment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment or comment.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")

    comment.content = content
    await db.commit()
    await db.refresh(comment)

    enriched = await _enrich_comments(db, [comment])
    return enriched[0]


async def delete_comment(db: AsyncSession, comment_id: int, user_id: int) -> None:
    result = await db.execute(select(ArticleComment).where(ArticleComment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment or comment.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")

    # Soft delete: keeps the row (and any replies) intact, content is hidden by the frontend
    # when is_deleted is true (e.g. show "[deleted]") instead of orphaning a reply thread.
    comment.is_deleted = True
    comment.content = ""
    await db.commit()

