"""
apps/social/models.py
Likes, comments, bookmarks, and share events on news articles.
All FK to news.id (apps.newsfeed.models.News) and users.id (apps.auth.models.User).
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class ArticleLike(Base):
    __tablename__ = "article_likes"
    __table_args__ = (UniqueConstraint("user_id", "news_id", name="uq_like_user_news"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ArticleComment(Base):
    __tablename__ = "article_comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)

    # Self-referential FK for one level (or more, if the frontend wants to render nested)
    # of replies. NULL = top-level comment.
    parent_comment_id = Column(Integer, ForeignKey("article_comments.id", ondelete="CASCADE"), nullable=True, index=True)

    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)  # soft delete: keeps replies intact

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    replies = relationship("ArticleComment", backref="parent", remote_side=[id])


class ArticleBookmark(Base):
    __tablename__ = "article_bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "news_id", name="uq_bookmark_user_news"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ArticleShare(Base):
    """Logged per share tap for analytics (which articles get shared, to where).
    Not unique per user — someone can share the same article multiple times."""
    __tablename__ = "article_shares"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String, nullable=True)  # e.g. "whatsapp", "copy_link", "twitter" — optional, frontend-supplied
    created_at = Column(DateTime(timezone=True), server_default=func.now())
