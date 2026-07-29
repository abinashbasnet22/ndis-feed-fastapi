import boto3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.base import settings

# ── Cloudflare R2 client ─────────────────────────────────────────────
r2 = boto3.client(
    "s3",
    endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=settings.R2_ACCESS_KEY,
    aws_secret_access_key=settings.R2_SECRET_KEY,
    region_name="auto",
)

# ── AWS S3 client (commented out — swap in if moving to AWS) ────────
# s3 = boto3.client(
#     "s3",
#     region_name=settings.AWS_REGION,
#     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
# )
# use s3 instead of r2 below if switching

PHOTOS_DIR  = "static/photos"
BUCKET_NAME = settings.R2_BUCKET_NAME

# map extension to content type
CONTENT_TYPES = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".webp": "image/webp",
}


def upload_all():
    total  = 0
    failed = 0

    for topic_folder in os.listdir(PHOTOS_DIR):
        topic_path = os.path.join(PHOTOS_DIR, topic_folder)

        if not os.path.isdir(topic_path):
            continue

        files = [
            f for f in os.listdir(topic_path)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]

        if not files:
            print(f"skipped  → {topic_folder} (no images)")
            continue

        for filename in files:
            local_path   = os.path.join(topic_path, filename)
            s3_key       = f"photos/{topic_folder}/{filename}"
            ext          = os.path.splitext(filename)[1].lower()
            content_type = CONTENT_TYPES.get(ext, "image/jpeg")

            try:
                r2.upload_file(         # ← change r2 to s3 for AWS
                    local_path,
                    BUCKET_NAME,
                    s3_key,
                    ExtraArgs={"ContentType": content_type}
                )
                print(f"uploaded → {s3_key}")
                total += 1
            except Exception as e:
                print(f"failed   → {s3_key}: {e}")
                failed += 1

    print(f"\ndone — {total} uploaded, {failed} failed")


upload_all()