from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from sqlalchemy.types import JSON as JSONType

from app.models.master_datasource_connections import MasterDataSourceConnection
from app.models.user import User


class UserDataSourceConnection(SQLModel):
    __tablename__ = "user_datasource_connections"
    __table_args__ = {"schema": "public"}

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    name: str = Field(nullable=False)
    label: str = Field(nullable=False)
    engine: str = Field(nullable=False)
    description: str = Field(nullable=False)
    connection_data: JSONType = Field(nullable=True)
    schemas: JSONType = Field(nullable=True)
    relationships: JSONType = Field(nullable=True)
    semantics: JSONType = Field(nullable=True)
    user_id: UUID = Field(nullable=False)
    integration_id: UUID = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(), nullable=False)

    # relationships
    user: User = Relationship(sa_relationship_kwargs={
                              "foreign_keys": "[UserDataSourceConnection.user_id]"})
    integration: MasterDataSourceConnection = Relationship(sa_relationship_kwargs={
                                                           "foreign_keys": "[UserDataSourceConnection.integration_id]"})

    class Config:
        arbitrary_types_allowed = True
