from fastapi import APIRouter
from api.models.system import HealthResponse
from api.services.market_data import get_provider_statuses
from settings import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    import api.app as app_module
    ready = app_module.controller is not None
    return HealthResponse(status="healthy" if ready else "initializing",
                          controller_ready=ready, providers=get_provider_statuses())


@router.get("/config")
async def get_config():
    return {
        "agent_models": settings.agent_models,
        "temperature": settings.temperature,
        "cache_ttl": {"prices": settings.cache_ttl_prices,
                      "historical": settings.cache_ttl_historical,
                      "top": settings.cache_ttl_top},
        "api": {"timeout": settings.api_request_timeout,
                "max_retries": settings.api_max_retries},
    }