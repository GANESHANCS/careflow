from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import (
    request_context_and_security_middleware,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from backend.app.api.router import api_router
from backend.app.db.session import engine, SessionLocal
from backend.app.db.models.base import Base
from backend.app.db.seed import seed_standard_indicators, seed_initial_users

# Initialize structured logging setup
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # automatic create_all & seed only in development/testing environments
    if settings.ENVIRONMENT.lower() in ["development", "testing"]:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_standard_indicators(db)
            seed_initial_users(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Custom Request ID & HTTP Security Headers Middleware
app.middleware("http")(request_context_and_security_middleware)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handlers for Error Sanitization & Standardized Response Contracts
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, generic_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Mount primary API router under both /api and /api/v1 for seamless compatibility
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} Platform API",
        "docs": "/api/docs",
        "health": "/api/health"
    }
