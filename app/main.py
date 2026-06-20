# FastAPI application entry point
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as api_router

logger = logging.getLogger(__name__)


def create_app():
    app = FastAPI(
        title="Gap Lens Dilution API",
        description="API for the Gap Lens Dilution project",
        version="1.0.0",
    )

    from app.core.config import settings as _s
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_s.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Admin dashboard middleware (registered after CORS; Starlette applies in reverse order,
    # so TailscaleGuardMiddleware runs first as the outermost layer)
    from app.core.config import settings
    from app.core.consumer_resolver import ConsumerResolver
    from app.middleware.consumer_context_middleware import ConsumerContextMiddleware
    from app.middleware.tailscale_guard_middleware import TailscaleGuardMiddleware
    from app.api.v1.admin_routes import admin_router

    if not settings.tailscale_consumer_map:
        logger.warning(
            "TAILSCALE_CONSUMER_MAP is empty — all traffic will be attributed as 'unknown'. "
            "Set TAILSCALE_CONSUMER_MAP in .env to enable consumer attribution."
        )
    resolver = ConsumerResolver(settings.tailscale_consumer_map)
    app.add_middleware(ConsumerContextMiddleware, resolver=resolver)
    app.add_middleware(TailscaleGuardMiddleware)

    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    # Serve the index page
    @app.get("/")
    async def serve_index():
        from fastapi.responses import FileResponse
        return FileResponse("app/static/index.html")

    # Include static files
    app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")

    return app


app = create_app()
