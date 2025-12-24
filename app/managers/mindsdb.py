from typing import Any, Dict, List
from app.config import settings
from fastapi import HTTPException
import mindsdb_sdk
from loguru import logger


class MindsDBManager:
    def __init__(self):
        try:
            self.mindsdb = mindsdb_sdk.connect(settings.MINDSDB_URL)
            # Validate connection by attempting to list databases
            # This ensures the connection actually works before logging success
            # _ = self.mindsdb.list_databases()
            logger.info(
                f"MindsDB client initialized successfully: {self.mindsdb}")
        except Exception as e:
            logger.error(f"Failed to initialize MindsDB client: {str(e)}")
            raise Exception(f"Failed to initialize MindsDB client: {str(e)}")

    def create_datasource(self, name: str, engine: str, connection_data: Dict[str, Any]):
        if not self.mindsdb:
            raise Exception("MindsDB client not initialized")
        try:
            self.mindsdb.create_database(
                name=name, engine=engine, connection_args=connection_data)
            logger.info(f"Datasource {name} created successfully")
        except Exception as e:
            logger.error(f"Failed to create datasource {name}: {str(e)}")
            raise Exception(f"Failed to create datasource {name}: {str(e)}")

    def delete_datasource(self, name: str):
        if not self.mindsdb:
            raise Exception("MindsDB client not initialized")
        try:
            self.mindsdb.drop_database(name)
            logger.info(f"Datasource {name} deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete datasource {name}: {str(e)}")
            raise Exception(f"Failed to delete datasource {name}: {str(e)}")

    def get_datasources(self):
        if not self.mindsdb:
            raise Exception("MindsDB client not initialized")
        try:
            databases = self.mindsdb.list_databases()
            result = []
            for db in databases:
                # Skip system databases
                if hasattr(db, "name") and db.name not in [
                    "mindsdb",
                    "information_schema",
                    "files",
                ]:
                    result.append(
                        {
                            "name": db.name,
                            "engine": db.engine if hasattr(db, "engine") else "unknown",
                            "description": None,
                        }
                    )
            return result
        except Exception as e:
            logger.error(f"Failed to get datasources: {str(e)}")
            raise Exception(f"Failed to get datasources: {str(e)}")

    def get_datasources_tables_and_schemas_by_names(self, names: List[str]):
        """
        Get all data sources, their tables, and schemas by names.
        """
        if not self.mindsdb:
            raise Exception("MindsDB connection not available")

        try:
            db_info = {}

            for name in names:
                db_name = name
                db_info[db_name] = {}

                try:
                    # Get tables in this database
                    db = self.mindsdb.get_database(db_name)
                    query = f'SHOW TABLES FROM "{db_name}"'
                    tables = db.query(query).fetch()

                    # Extract just the table names
                    table_names = []
                    if hasattr(tables, 'iloc'):  # If it's a DataFrame
                        # Assuming first column contains table names
                        table_names = tables.iloc[:, 0].tolist()
                    elif isinstance(tables, list):
                        # If it's a list of dicts, extract table names
                        table_names = [list(row.values())[0] for row in tables]

                    for table_name in table_names:
                        try:
                            columns_query = f"""
                            SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE FROM {db_name}.INFORMATION_SCHEMA.COLUMNS
                            WHERE table_name = '{table_name}'
                            """

                            columns = db.query(columns_query).fetch()

                            # Process columns with schema information in format {column_name: data_type}
                            columns_info = {}
                            if hasattr(columns, 'iloc'):  # If it's a DataFrame
                                # Extract column name and data type for each row
                                for idx, row in columns.iterrows():
                                    column_name = row.iloc[0]
                                    # Skip is_nullable (index 1)
                                    data_type = row.iloc[2]
                                    columns_info[column_name] = data_type
                            elif isinstance(columns, list):
                                # If it's a list of dicts, extract column name and data type
                                for row in columns:
                                    if isinstance(row, dict):
                                        # If row is already a dict with proper keys
                                        column_name = row.get(
                                            'COLUMN_NAME', '')
                                        data_type = row.get('DATA_TYPE', '')
                                        if column_name:
                                            columns_info[column_name] = data_type
                                    else:
                                        # If row is a list/tuple of values
                                        values = list(row.values()) if hasattr(
                                            row, 'values') else row
                                        if len(values) >= 3:
                                            column_name = values[0]
                                            # Skip is_nullable (index 1)
                                            data_type = values[2]
                                            if column_name:
                                                columns_info[column_name] = data_type
                            else:
                                columns_info = {}

                        except Exception as e:
                            logger.error(
                                f"Error fetching columns for table {table_name}: {e}")
                            columns_info = {}

                        db_info[db_name][table_name] = columns_info

                except Exception as e:
                    logger.error(f"Error accessing database {db_name}: {e}")
                    raise Exception(f"Error accessing database {db_name}: {e}")

            return db_info

        except Exception as e:
            logger.error(f"Failed to list datasources: {str(e)}")
            raise Exception(f"Failed to list datasources: {str(e)}")

    def execute_query(self, sql_query: str, database_name: str | None = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        try:
            # Execute query
            if database_name:
                query = self.mindsdb.databases.get(
                    database_name).query(sql_query)
            else:
                query = self.mindsdb.query(sql_query)

            # Convert results to list of dictionaries
            results = query.fetch()

            if hasattr(results, 'to_dict'):
                return results.to_dict('records')
            elif isinstance(results, list):
                return results
            else:
                return [{"result": str(results)}]

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Query execution failed: {str(e)}")
