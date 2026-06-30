from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import github, review

app = FastAPI(
    title="AI Code Review Assistant",
    description="AI-powered GitHub pull request review platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github.router)
app.include_router(review.router)


@app.get("/")
def root():
    return {
        "message": "AI Code Review Assistant API",
        "docs": "/docs",
        "health": "/api/health",
        "frontend": "http://localhost:5173",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "github_configured": bool(settings.github_token),
        "openai_configured": bool(settings.openai_api_key),
        "gemini_configured": bool(settings.gemini_api_key) and settings.gemini_api_key != "your_gemini_api_key_here",
        "active_provider": settings.ai_provider,
    }
