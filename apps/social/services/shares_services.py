from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.social.models import ArticleLike, ArticleComment, ArticleBookmark, ArticleShare
from apps.newsfeed.models import News  # for bookmark listing joins — adjust import if your News model lives elsewhere
from apps.auth.models import User

DEFAULT_PAGE_LIMIT = 20


# ==================== Shares ====================

async def log_share(db: AsyncSession, user_id: int, news_id: int, channel: Optional[str]) -> int:
    db.add(ArticleShare(user_id=user_id, news_id=news_id, channel=channel))
    await db.commit()

    result = await db.execute(
        select(func.count()).select_from(ArticleShare).where(ArticleShare.news_id == news_id)
    )
    return result.scalar_one()