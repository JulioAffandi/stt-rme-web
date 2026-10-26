from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Status layanan + engine NLP yang aktif."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "nlp_engine": settings.nlp_engine,
    }
