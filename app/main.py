from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.config import settings
from app.deps import cleanup_managers, init_managers

from app.middleware.auth import AuthMiddleware
from app.routes.datasources import router as datasources_router
from app.routes.chat import router as chat_router
from app.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        await init_managers(app)
        logger.info("Managers initialized successfully")
        yield
    finally:
        await cleanup_managers(app)
        logger.info("Managers cleaned up successfully")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

origins = settings.origins

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Configure appropriately for production
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],
)

app.add_middleware(AuthMiddleware)

# Include routes
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}}
)

app.include_router(
    datasources_router,
    prefix="/datasources",
    tags=["datasources"],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    chat_router,
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


@app.get("/")
async def root():
    return {"message": "Hello World", "app": settings.app_name}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}
