"""
scripts/create_tables.py
Creates every table that doesn't exist yet, across all apps. Safe to run
repeatedly — create_all() skips tables that already exist and never alters
or drops existing ones.

Run once locally:
    python scripts/create_tables.py

Run once against Railway (point DATABASE_URL at the public Railway URL
first, e.g. via a temporary env var override or a second .env.railway file):
    DATABASE_URL="postgresql+asyncpg://postgres:PASS@hayabusa.proxy.rlwy.net:48992/railway" python scripts/create_tables.py
"""

import asyncio
import sys
from pathlib import Path

# Running `python scripts/create_tables.py` directly only puts scripts/ on
# sys.path, not the project root — so core/ and apps/ aren't importable
# without this. (Your existing scripts/seed_photos.py may already handle
# this differently, e.g. if you run it as `python -m scripts.seed_photos`
# instead — either approach works, this just makes plain `python scripts/x.py`
# work too.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import engine, Base

# Each import registers that app's tables on Base.metadata as a side effect —
# nothing needs to be done with these names directly, but the import must
# happen before create_all() runs, or SQLAlchemy won't know these tables exist.
import apps.newsfeed.models   # News, NewsAnalytics, StockPhoto
import apps.events.models     # existing events tables
import apps.auth.models       # User  <- new
import apps.onboarding.models # OnboardingProfile  <- new
import apps.social.models     # ArticleLike, ArticleComment, ArticleBookmark, ArticleShare  <- new


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created (or already existed) — no errors.")


if __name__ == "__main__":
    asyncio.run(create_tables())