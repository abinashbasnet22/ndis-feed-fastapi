from fastapi import FastAPI,Depends
from apps.auth.services import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from apps.newsfeed.routers import router as newsfeed_router
from apps.events.routers import router as events_router
from apps.auth.routers import router as auth_router
from apps.onboarding.routers import router as onboarding_router
from apps.social.routers import router as social_router
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="CareMate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth_router,
      prefix="/caremate/auth",
        tags=["auth"]
)

app.include_router(
    newsfeed_router, 
    prefix="/caremate",
    tags=["newsfeed"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    events_router,
    prefix="/caremate",
    tags=["events"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    onboarding_router,
    prefix="/caremate/onboarding",
    tags=["onboarding"],
    dependencies=[Depends(get_current_user)],
)


app.include_router(
    social_router,
    prefix="/caremate/social",
    tags=["social"],
    dependencies=[Depends(get_current_user)],
)

# mount static only in local development
# on Railway images are served from Cloudflare R2
if os.path.exists("static") and os.path.isdir("static") and os.getenv("ENVIRONMENT") != "production":
    app.mount("/static", StaticFiles(directory="static"), name="static")
