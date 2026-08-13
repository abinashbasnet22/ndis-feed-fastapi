"""
apps/social/services/__init__.py
Re-exports everything so `from apps.social import services` (used in
routers.py) and `from apps.social.services import get_engagement_map` (used in
apps/newsfeed/services/feed.py) both keep working unchanged, matching the
apps/newsfeed/services/__init__.py convention.
"""

from apps.social.services.likes_services import (
    get_like_count,
    is_liked_by_user,
    toggle_like,
)
from apps.social.services.comments_services import (
    create_comment,
    get_comments,
    get_replies,
    update_comment,
    delete_comment,
)
from apps.social.services.bookmarks_services import (
    is_bookmarked,
    toggle_bookmark,
    get_bookmarks,
)
from apps.social.services.shares_services import log_share
from apps.social.services.engagement_services import get_engagement_map

__all__ = [
    "get_like_count",
    "is_liked_by_user",
    "toggle_like",
    "create_comment",
    "get_comments",
    "get_replies",
    "update_comment",
    "delete_comment",
    "is_bookmarked",
    "toggle_bookmark",
    "get_bookmarks",
    "log_share",
    "get_engagement_map",
]