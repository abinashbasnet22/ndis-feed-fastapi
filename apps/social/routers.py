"""
apps/social/routers.py
Register in main.py:

    from apps.social.routers import router as social_router
    app.include_router(
        social_router,
        prefix="/caremate/social",
        tags=["social"],
        dependencies=[Depends(get_current_user)],  # app is fully gated — see auth section
    )
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from apps.auth.services import get_current_user
from apps.auth.models import User
from apps.social.schemas import (
    LikeStatus,
    CommentCreate,
    CommentUpdate,
    CommentOut,
    CommentPage,
    BookmarkStatus,
    BookmarkPage,
    ShareCreate,
    ShareStatus,
)
from apps.social import services

router = APIRouter()


# ==================== Likes ====================

@router.post("/likes/{news_id}", response_model=LikeStatus)
async def toggle_like(
    news_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggles: likes if not already liked, unlikes if already liked."""
    liked, count = await services.toggle_like(db, current_user.id, news_id)
    return LikeStatus(liked=liked, like_count=count)


@router.get("/likes/{news_id}", response_model=LikeStatus)
async def like_status(
    news_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    liked = await services.is_liked_by_user(db, current_user.id, news_id)
    count = await services.get_like_count(db, news_id)
    return LikeStatus(liked=liked, like_count=count)


# ==================== Comments ====================

@router.post("/comments/{news_id}", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    news_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await services.create_comment(
        db, current_user.id, news_id, payload.content, payload.parent_comment_id
    )


@router.get("/comments/{news_id}", response_model=CommentPage)
async def list_comments(
    news_id: int,
    cursor: Optional[int] = Query(default=None),
    limit: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Top-level comments only — call GET /comments/replies/{comment_id} to expand a thread."""
    items, next_cursor = await services.get_comments(db, news_id, cursor, limit)
    return CommentPage(items=items, next_cursor=next_cursor)


@router.get("/comments/replies/{comment_id}", response_model=list[CommentOut])
async def list_replies(comment_id: int, db: AsyncSession = Depends(get_db)):
    return await services.get_replies(db, comment_id)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
async def edit_comment(
    comment_id: int,
    payload: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await services.update_comment(db, comment_id, current_user.id, payload.content)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await services.delete_comment(db, comment_id, current_user.id)


# ==================== Bookmarks ====================

@router.post("/bookmarks/{news_id}", response_model=BookmarkStatus)
async def toggle_bookmark(
    news_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bookmarked = await services.toggle_bookmark(db, current_user.id, news_id)
    return BookmarkStatus(bookmarked=bookmarked)


@router.get("/bookmarks", response_model=BookmarkPage)
async def my_bookmarks(
    cursor: Optional[int] = Query(default=None),
    limit: int = Query(default=20, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, next_cursor = await services.get_bookmarks(db, current_user.id, cursor, limit)
    return BookmarkPage(items=items, next_cursor=next_cursor)


# ==================== Shares ====================

@router.post("/shares/{news_id}", response_model=ShareStatus)
async def log_share(
    news_id: int,
    payload: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fire-and-forget analytics log — call this when the user taps 'Share'
    and picks a channel (or copies the link), purely for tracking share_count."""
    count = await services.log_share(db, current_user.id, news_id, payload.channel)
    return ShareStatus(share_count=count)
