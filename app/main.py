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

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    # Include static files
    app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")

    return app


app = create_app()
