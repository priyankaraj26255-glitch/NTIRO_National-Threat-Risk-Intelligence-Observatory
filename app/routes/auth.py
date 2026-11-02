
import logging
import os
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database_dependency import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserRegister,
    UserRegisterResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    UserLogin,
    UserLoginResponse,
)

from app.services.user_service import (
    register_user,
    authenticate_user,
)

from app.services.email_verification_service import verify_email_token
from app.core.token import create_access_token


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# -----------------------------------------
# USER REGISTRATION
# -----------------------------------------

@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    try:
        new_user, raw_token = register_user(
            db=db,
            full_name=user_data.full_name,
            email=str(user_data.email),
            password=user_data.password,
            role_id=user_data.role_id,
        )

    except ValueError as exc:
        error_message = str(exc)

        if error_message == "Email is already registered.":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        ) from exc

    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration conflicts with an existing record.",
        ) from exc

    # Development-only token visibility.
    # Never log raw verification tokens in production.
    if os.getenv("APP_ENV") == "development":
        logger.warning(
            "Development verification token for %s: %s",
            new_user.email,
            raw_token,
        )

    return new_user


# -----------------------------------------
# EMAIL VERIFICATION
# -----------------------------------------

@router.post(
    "/verify-email",
    response_model=EmailVerificationResponse,
)
def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    try:
        user = verify_email_token(
            db=db,
            raw_token=verification_data.token,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "message": "Email verified successfully.",
        "email_verified": user.email_verified,
    }


# -----------------------------------------
# USER LOGIN
# -----------------------------------------

@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(
            db=db,
            email=str(user_data.email),
            password=user_data.password,
        )

    except ValueError as exc:
        error_message = str(exc)

        if error_message == "Invalid email or password.":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message,
        ) from exc

    # Read the configured access-token lifetime.
    expiry_minutes = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    access_token = create_access_token(
        user_id=user.id,
        expires_delta=timedelta(minutes=expiry_minutes),
    )

    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        role_id=user.role_id,
        email_verified=user.email_verified,
        approval_status=user.approval_status,
    )
@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role_id": current_user.role_id,
        "email_verified": current_user.email_verified,
        "approval_status": current_user.approval_status,
    }
