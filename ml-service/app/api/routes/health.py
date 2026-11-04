from fastapi import APIRouter

from app.models.registry import registry
from app.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Servisin vəziyyəti (autentifikasiya tələb olunmur; həssas məlumat qaytarmır)."""
    if registry.ready:
        return HealthResponse(status="ok", modelsLoaded=True, modelVersion=registry.get().version)
    return HealthResponse(status="degraded", modelsLoaded=False, detail="Modellər yüklənməyib")
