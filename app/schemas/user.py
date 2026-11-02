
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# -----------------------------------------
# USER REGISTRATION
# -----------------------------------------

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


# -----------------------------------------
# EMAIL VERIFICATION
# -----------------------------------------

class EmailVerificationRequest(BaseModel):

    token: str = Field(
        min_length=20,
        max_length=200,
    )


class EmailVerificationResponse(BaseModel):

    message: str
    email_verified: bool


# -----------------------------------------
# USER LOGIN
# -----------------------------------------

class UserLogin(BaseModel):
    """Validate user login credentials."""

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserLoginResponse(BaseModel):
    """Return authentication details after successful login."""

    access_token: str

    token_type: str = "bearer"

    user_id: int
    full_name: str
    email: EmailStr
    role_id: int
    email_verified: bool
    approval_status: str
