from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.types import JSON as JSONType


class UserMetaData(dict):
    """
    Represents user metadata structure for the User model.
    Maps to the IUserMetaData interface in the original TypeScript code.
    """

    avatar_url: str
    email: str
    email_verified: bool
    first_name: str
    full_name: str
    iss: str
    last_name: str
    name: str
    onboarding_skipped: bool
    phone_verified: bool
    picture: str
    provider_id: str
    setup_account: bool
    sub: str
    stripe_customer_id: str | None = None
    request_create_tenant: bool | None = None


class User(SQLModel):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    email: str = Field(nullable=False)
    raw_user_meta_data: UserMetaData = Field(
        default={}, nullable=True, sa_type=JSONType
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(), nullable=False)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(), nullable=False)

    class Config:
        arbitrary_types_allowed = True
