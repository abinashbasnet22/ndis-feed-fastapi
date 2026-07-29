from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.newsfeed.routers import router as newsfeed_router
from apps.events.routers import router as events_router
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="CareMate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(newsfeed_router, prefix="/caremate")
app.include_router(events_router,   prefix="/caremate")


# mount static only in local development
# on Railway images are served from Cloudflare R2
if os.path.exists("static") and os.path.isdir("static") and os.getenv("ENVIRONMENT") != "production":
    app.mount("/static", StaticFiles(directory="static"), name="static")
