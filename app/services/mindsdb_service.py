from app.managers.mindsdb import MindsDBManager
from fastapi import HTTPException
from typing import Any


class MindsDBService:
    def __init__(self, minds_db_manager: MindsDBManager):
        self.minds_db_manager = minds_db_manager

    def query(self, name: str, query: str) -> Any:
        if not self.minds_db_manager:
            raise HTTPException(
                status_code=400, detail="MindsDB manager not initialized")

        try:
            limit = 100
            database = self.minds_db_manager.mindsdb.get_database(name)
            if not database:
                raise HTTPException(
                    status_code=400, detail=f"Database '{name}' not found")

            # Add limit to query if not present
            # if limit and "limit" not in query.lower():
            #     query = f"{query} LIMIT {limit}"

            # Execute query
            result = database.query(query)
            df = result.fetch()

            # The result is already a pandas DataFrame
            if df is not None:
                return {
                    "columns": list(df.columns),
                    "data": df.to_dict("records"),
                    "row_count": len(df),
                }
            else:
                return {"columns": [], "data": [], "row_count": 0}

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
