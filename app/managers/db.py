from supabase import create_client
from loguru import logger


class DBManager:
    def __init__(self, supabase_url: str, supabase_key: str):
        try:
            self.client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise Exception(f"Failed to initialize Supabase client: {str(e)}")
