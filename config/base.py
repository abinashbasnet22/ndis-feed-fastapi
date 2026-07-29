

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL:           str
    ENVIRONMENT:            str = "development"

    # Cloudflare R2 (default)
    R2_ACCESS_KEY:          str = ""
    R2_SECRET_KEY:          str = ""
    R2_ACCOUNT_ID:          str = ""
    R2_BUCKET_NAME:         str = ""

    # AWS S3 (alternative — swap in if moving to AWS)
    # AWS_ACCESS_KEY_ID:    str = ""
    # AWS_SECRET_ACCESS_KEY:str = ""
    # AWS_REGION:           str = "ap-southeast-2"
    # S3_BUCKET_NAME:       str = ""

    class Config:
        env_file = ".env"

settings = Settings()