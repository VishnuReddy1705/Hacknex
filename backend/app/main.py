from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.api.videos import router as videos_router
from backend.app.api.events import router as events_router
from backend.app.api.questions import router as questions_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=f"HNX26PSI02 — {settings.TAGLINE}",
    version=settings.VERSION
)

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

app.include_router(videos_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(questions_router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "gpu_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "llm_configured": bool(settings.LLM_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
