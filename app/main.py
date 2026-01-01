import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.api.routes import router
from app.core.logging import setup_logging
from app.observability.tracing import setup_tracer
from app.core.config import get_settings
from app.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

settings = get_settings()
setup_logging()
setup_tracer(settings.app_name, settings.otel_endpoint)

app = FastAPI(title=settings.app_name)
app.include_router(router)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start) * 1000
    REQUEST_LATENCY.labels(request.url.path).observe(latency_ms)
    REQUEST_COUNT.labels(request.url.path, str(response.status_code)).inc()
    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "internal_error"})
