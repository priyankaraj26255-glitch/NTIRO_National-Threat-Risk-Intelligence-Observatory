
from datetime import datetime
from typing import Literal
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

# -----------------------------------------
# ADMIN USER MANAGEMENT SCHEMAS
# -----------------------------------------

class AdminUserResponse(BaseModel):
    """Public account information returned to administrators."""

    id: int
    full_name: str
    email: EmailStr
    role_id: int
    role: str
    email_verified: bool
    approval_status: str
    account_status: Literal["active", "suspended", "disabled"]
    created_at: datetime


class AdminUserDetailResponse(AdminUserResponse):
    """Detailed account information for an administrator."""

    approved_by: int | None
    approved_at: datetime | None


class AdminUserListResponse(BaseModel):
    """Paginated list of registered users."""

    offset: int
    limit: int
    returned: int
    users: list[AdminUserResponse]


class AccountStatusResponse(BaseModel):
    """Response after an account status operation."""

    message: str
    user_id: int
    account_status: Literal["active", "suspended", "disabled"]

