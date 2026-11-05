
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database_dependency import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.role import Role

from app.schemas.user import (
    AdminUserResponse,
    AdminUserDetailResponse,
    AdminUserListResponse,
    AccountStatusResponse,
)

from app.services.approval_service import (
    get_pending_professionals,
    approve_professional,
    reject_professional,
)

from app.services.User_Manag_service import (
    list_users,
    get_user_details,
    suspend_user,
    reactivate_user,
    disable_user,
)


router = APIRouter(
    prefix="/admin",
    tags=["Administrator"],
)


# -----------------------------------------
# SHARED RESPONSE HELPERS
# -----------------------------------------

def _serialize_admin_user(user: User, db: Session) -> dict:
    """Convert a User ORM object into safe admin response data."""

    role = db.get(Role, user.role_id)

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role_id": user.role_id,
        "role": role.name if role else "Unavailable",
        "email_verified": user.email_verified,
        "approval_status": user.approval_status,
        "account_status": user.account_status,
        "created_at": user.created_at,
    }


def _serialize_admin_user_detail(user: User, db: Session) -> dict:
    """Include approval information in detailed user responses."""

    result = _serialize_admin_user(user, db)

    result.update({
        "approved_by": user.approved_by,
        "approved_at": user.approved_at,
    })

    return result


def _handle_service_error(exc: ValueError) -> HTTPException:
    """Convert service-layer errors into appropriate HTTP errors."""

    message = str(exc)

    if message == "User not found.":
        error_status = status.HTTP_404_NOT_FOUND

    elif message == "Administrator not found.":
        error_status = status.HTTP_403_FORBIDDEN

    else:
        error_status = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=error_status,
        detail=message,
    )


# -----------------------------------------
# VIEW PENDING PROFESSIONAL ACCOUNTS
# -----------------------------------------

@router.get("/pending-professionals")
def list_pending_professionals(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    users = get_pending_professionals(db)

    results = []

    for user in users:
        role = db.get(Role, user.role_id)

        results.append({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": role.name if role else None,
            "email_verified": user.email_verified,
            "approval_status": user.approval_status,
            "created_at": user.created_at,
        })

    return {
        "total_pending": len(results),
        "users": results,
    }


# -----------------------------------------
# APPROVE PROFESSIONAL ACCOUNT
# -----------------------------------------

@router.post("/users/{user_id}/approve")
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    try:
        user = approve_professional(
            db=db,
            user_id=user_id,
            admin_id=current_admin.id,
        )

    except ValueError as exc:
        raise _handle_service_error(exc) from exc

    return {
        "message": "Professional account approved successfully.",
        "user_id": user.id,
        "approval_status": user.approval_status,
        "approved_by": user.approved_by,
        "approved_at": user.approved_at,
    }


# -----------------------------------------
# REJECT PROFESSIONAL ACCOUNT
# -----------------------------------------

@router.post("/users/{user_id}/reject")
def reject_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    try:
        user = reject_professional(
            db=db,
            user_id=user_id,
            admin_id=current_admin.id,
        )

    except ValueError as exc:
        raise _handle_service_error(exc) from exc

    return {
        "message": "Professional account rejected successfully.",
        "user_id": user.id,
        "approval_status": user.approval_status,
        "approved_by": user.approved_by,
        "approved_at": user.approved_at,
    }


# -----------------------------------------
# LIST ALL USERS
# -----------------------------------------

@router.get(
    "/users",
    response_model=AdminUserListResponse,
)
def admin_list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    try:
        users = list_users(
            db=db,
            offset=offset,
            limit=limit,
        )

    except ValueError as exc:
        raise _handle_service_error(exc) from exc

    results = [
        _serialize_admin_user(user, db)
        for user in users
    ]

    return {
        "offset": offset,
        "limit": limit,
        "returned": len(results),
        "users": results,
    }


# -----------------------------------------
# GET INDIVIDUAL USER DETAILS
# -----------------------------------------

@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetailResponse,
)
def admin_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    try:
        user = get_user_details(
            db=db,
            user_id=user_id,
        )

    except ValueError as exc:
        raise _handle_service_error(exc) from exc

    return _serialize_admin_user_detail(user, db)


# -----------------------------------------
# SUSPEND USER ACCOUNT
# -----------------------------------------

@router.post(
    "/users/{user_id}/suspend",
    response_model=AccountStatusResponse,
)
def admin_suspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    try:
        user = suspend_user(
            db=db,
            user_id=user_id,
            admin_id=current_admin.id,
        )

    except ValueError as exc:
        raise _handle_service_error(exc) from exc

    return {
        "message": "User account suspended successfully.",
        "user_id": user.id,
        "account_status": user.account_status,
    }


# -----------------------------------------
# REACTIVATE USER ACCOUNT
# -----------------------------------------

@router.post(
    "/users/{user_id}/reactivate",
    response_model=AccountStatusResponse,
)
def admin_reactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    try:
        user = reactivate_user(
            db=db,
            user_id=user_id,
            admin_id=current_admin.id,
        )

    except ValueError as exc:
        raise _handle_service_error(exc) from exc

    return {
        "message": "User account reactivated successfully.",
        "user_id": user.id,
        "account_status": user.account_status,
    }


# -----------------------------------------
# DISABLE USER ACCOUNT
# -----------------------------------------

@router.post(
    "/users/{user_id}/disable",
    response_model=AccountStatusResponse,
)
def admin_disable_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    try:
        user = disable_user(
            db=db,
            user_id=user_id,
            admin_id=current_admin.id,
        )

    except ValueError as exc:
        raise _handle_service_error(exc) from exc

    return {
        "message": "User account disabled successfully.",
        "user_id": user.id,
        "account_status": user.account_status,
    }
