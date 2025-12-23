from typing import Any, Dict
from pydantic import BaseModel


class DataSourceMetadata(BaseModel):
    name: str
    label: str
    engine: str
    description: str
    integration_id: str


class DataSourceCreateSchema(BaseModel):
    connection_data: Dict[str, Any]
    metadata: DataSourceMetadata


class GetDataSourceSchemas(BaseModel):
    name: str
