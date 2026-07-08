from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.newsfeed.routers import router as newsfeed_router
from apps.events.routers import router as events_router

app = FastAPI(title="CareMate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(newsfeed_router, prefix="/caremate")
app.include_router(events_router,   prefix="/caremate")

