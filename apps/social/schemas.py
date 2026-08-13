"""
apps/social/schemas.py
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---- Likes ----

class LikeStatus(BaseModel):
    liked: bool
    like_count: int


# ---- Comments ----

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_comment_id: Optional[int] = None


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentAuthor(BaseModel):
    id: int
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class CommentOut(BaseModel):
    id: int
    news_id: int
    parent_comment_id: Optional[int] = None
    content: str
    is_deleted: bool
    author: CommentAuthor
    reply_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentPage(BaseModel):
    items: List[CommentOut]
    next_cursor: Optional[int] = None


# ---- Bookmarks ----

class BookmarkStatus(BaseModel):
    bookmarked: bool


class BookmarkedArticle(BaseModel):
    news_id: int
    title: str
    snippet: Optional[str] = None
    image_filename: Optional[str] = None
    bookmarked_at: datetime


class BookmarkPage(BaseModel):
    items: List[BookmarkedArticle]
    next_cursor: Optional[int] = None


# ---- Shares ----

class ShareCreate(BaseModel):
    channel: Optional[str] = Field(default=None, max_length=50)


class ShareStatus(BaseModel):
    share_count: int
