from uuid import UUID
from sqlmodel import Field, SQLModel
from datetime import datetime
from sqlalchemy.types import JSON as JSONType


class MasterDataSourceConnection(SQLModel):
    __tablename__ = "master_datasource_connections"
    __table_args__ = {"schema": "public"}

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    name: str = Field(nullable=False)
    label: str = Field(nullable=False)
    icon: str = Field(nullable=True)
    form_schema: JSONType = Field(nullable=False)
    active: bool = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(), nullable=False)

    class Config:
        arbitrary_types_allowed = True
