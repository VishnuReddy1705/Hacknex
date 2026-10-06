from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.app.database.session import init_db
from backend.app.api.videos import router as videos_router
from backend.app.api.events import router as events_router
from backend.app.api.entities import router as entities_router
from backend.app.api.query import router as query_router

app = FastAPI(
    title="TemporalLens API",
    description="Video Understanding & Temporal Reasoning Engine for HackNex 2026",
    version="1.0.0"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# Mount API routers
app.include_router(videos_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(entities_router, prefix="/api")
app.include_router(query_router, prefix="/api")

@app.get("/api/health")
def health_check():
    import torch
    return {
        "status": "healthy",
        "service": "TemporalLens Video Reasoning",
        "gpu_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
