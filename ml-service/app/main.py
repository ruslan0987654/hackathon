"""FastAPI giriş nöqtəsi."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import health, model, predict
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.models.registry import ModelNotReadyError, registry

settings = get_settings()
setup_logging(settings.log_level)
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    registry.load(settings.model_dir)
    if not settings.api_key:
        log.warning("API_KEY təyin edilməyib: /predict və /model endpoint-ləri 503 qaytaracaq. .env faylını yoxlayın.")
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan,
              description="SOCAR Smart Analytics üçün ML servisi. Analitik qərar dəstəyidir; mühəndis təsdiqi tələb olunur.")


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > settings.max_request_bytes:
        return JSONResponse(status_code=413, content={"detail": f"Sorğu həddən böyükdür (max {settings.max_request_bytes} bayt)."})
    return await call_next(request)


@app.exception_handler(ModelNotReadyError)
async def model_not_ready_handler(_: Request, exc: ModelNotReadyError):
    return JSONResponse(status_code=503, content={"detail": f"Model hazır deyil: {exc}"})


app.include_router(health.router)
app.include_router(model.router)
app.include_router(predict.router)
