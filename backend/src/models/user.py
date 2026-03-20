from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
	analyst = "analyst"
	admin = "admin"
	viewer = "viewer"


class User(BaseModel):
	user_id: str = Field(min_length=1)
	username: str = Field(min_length=1)
	email: EmailStr
	password_hash: str = Field(min_length=1)
	role: UserRole
	created_at: datetime

	model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)
