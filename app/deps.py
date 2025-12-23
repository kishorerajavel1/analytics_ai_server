from fastapi import FastAPI

from app.managers.db import DBManager
from app.managers.mindsdb import MindsDBManager
from app.config import settings


def create_db_manager() -> DBManager:
    """Create a new database manager instance"""
    return DBManager(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
    )


def create_minds_db_manager() -> MindsDBManager:
    """Create a new MindsDB manager instance"""
    return MindsDBManager()


async def init_managers(app: FastAPI):
    """Initialize all managers"""
    app.state.db_manager = create_db_manager()
    app.state.minds_db_manager = create_minds_db_manager()


async def cleanup_managers(app: FastAPI):
    """Cleanup all managers"""
    app.state.db_manager = None
    app.state.minds_db_manager = None
