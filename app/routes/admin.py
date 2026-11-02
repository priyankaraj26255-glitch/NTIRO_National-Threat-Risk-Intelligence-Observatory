
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database_dependency import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.role import Role

from app.services.approval_service import (
    get_pending_professionals,
    approve_professional,
    reject_professional,
)


router = APIRouter(
    prefix="/admin",
    tags=["Administrator"],
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
        error_message = str(exc)

        if error_message == "User not found.":
            error_status = status.HTTP_404_NOT_FOUND
        elif error_message == "Administrator not found.":
            error_status = status.HTTP_403_FORBIDDEN
        else:
            error_status = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=error_status,
            detail=error_message,
        ) from exc

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
        error_message = str(exc)

        if error_message == "User not found.":
            error_status = status.HTTP_404_NOT_FOUND
        elif error_message == "Administrator not found.":
            error_status = status.HTTP_403_FORBIDDEN
        else:
            error_status = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=error_status,
            detail=error_message,
        ) from exc

    return {
        "message": "Professional account rejected successfully.",
        "user_id": user.id,
        "approval_status": user.approval_status,
        "approved_by": user.approved_by,
        "approved_at": user.approved_at,
    }
