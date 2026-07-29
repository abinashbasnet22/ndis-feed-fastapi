import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from apps.newsfeed.models import StockPhoto, Base

DATABASE_URL = "postgresql+asyncpg://abinash:ndis@localhost:5432/ndis_news"
engine       = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession)

PHOTOS_DIR = "static/photos"


async def seed():
    # create table if not exists
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("table ready")

    async with SessionLocal() as db:
        total = 0

        # scan every folder inside static/photos
        for topic_folder in os.listdir(PHOTOS_DIR):
            topic_path = os.path.join(PHOTOS_DIR, topic_folder)

            if not os.path.isdir(topic_path):
                continue

            # scan every image file in the folder
            files = [
                f for f in os.listdir(topic_path)
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
            ]

            if not files:
                print(f"skipped  → {topic_folder} (no images)")
                continue

            for filename in files:
                db.add(StockPhoto(
                    topic=topic_folder,
                    filename=filename,
                    used_count=0,
                ))
                total += 1

            print(f"seeded   → {topic_folder} ({len(files)} photos)")

        await db.commit()
        print(f"\ndone — {total} photos seeded across all topics")


asyncio.run(seed())