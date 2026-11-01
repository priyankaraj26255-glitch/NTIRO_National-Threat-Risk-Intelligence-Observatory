from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database_dependency import get_db
from app.schemas.user import UserRegister, UserRegisterResponse
from app.services.user_service import register_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


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
        new_user = register_user(
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

    return new_user