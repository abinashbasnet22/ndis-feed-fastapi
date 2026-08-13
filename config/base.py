

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL:           str
    ENVIRONMENT:            str = "development"

    # Cloudflare R2 (default)
    R2_ACCESS_KEY:          str = ""
    R2_SECRET_KEY:          str = ""
    R2_ACCOUNT_ID:          str = ""
    R2_BUCKET_NAME:         str = ""
    R2_PUBLIC_URL:          str = ""

    # AWS S3 (alternative — swap in if moving to AWS)
    # AWS_ACCESS_KEY_ID:    str = ""
    # AWS_SECRET_ACCESS_KEY:str = ""
    # AWS_REGION:           str = "ap-southeast-2"
    # S3_BUCKET_NAME:       str = ""

    # Auth / JWT
    SECRET_KEY:                          str
    JWT_ALGORITHM:                       str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:         int = 43200  #30 mins on deploy
    REFRESH_TOKEN_EXPIRE_DAYS:           int = 30    #7 days on deploy
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15


    # Google Sign-In
    GOOGLE_CLIENT_ID:       str = ""
    GOOGLE_CLIENT_SECRET:   str = ""

    class Config:
        env_file = ".env"

settings = Settings()