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


# only mount if directory exists and has content
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
