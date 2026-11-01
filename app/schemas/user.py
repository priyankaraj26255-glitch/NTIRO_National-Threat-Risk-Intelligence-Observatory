from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role_id: int = Field(
        gt=0,
    )


class UserRegisterResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role_id: int
    email_verified: bool
    approval_status: str
    account_status: str
    created_at: datetime