from datetime import datetime, timezone
from typing import TYPE_CHECKING, List
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class RoleType(str, Enum):
    ADMIN = "Administrateur"
    USER = "Utilisateur"
    TESTER = "Testeur"
    

class UserBase(SQLModel):
    username: str = Field(max_length=100, index=True, unique=True)
    email: EmailStr = Field(max_length=100, index=True)
    first_name: str | None = Field(max_length=100, default=None)
    last_name: str | None = Field(max_length=100, default=None)


class User(UserBase, table=True):
    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field(..., description="Mot de passe chiffre.")
    role: RoleType = Field(default=RoleType.USER, index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    username: str | None = None
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    old_password: str | None = None
    new_password: str | None = None
    is_active: bool | None = None
    role: str | None = None


class UserPublic(UserBase):
    id: int
    role: RoleType
    is_active: bool
    created_at: datetime
    updated_at: datetime
