# FastAPI application entry point
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as api_router


def create_app():
    app = FastAPI(
        title="Gap Lens Dilution API",
        description="API for the Gap Lens Dilution project",
        version="1.0.0",
    )

    # Include CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict this to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Access-Control-Allow-Origin"],
    )

    # Admin dashboard middleware (registered after CORS; Starlette applies in reverse order,
    # so TailscaleGuardMiddleware runs first as the outermost layer)
    from app.core.config import settings
    from app.core.consumer_resolver import ConsumerResolver
    from app.middleware.consumer_context_middleware import ConsumerContextMiddleware
    from app.middleware.tailscale_guard_middleware import TailscaleGuardMiddleware
    from app.api.v1.admin_routes import admin_router

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
