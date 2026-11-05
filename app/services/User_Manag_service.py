
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, Role


# -----------------------------------------
# ADMINISTRATOR VALIDATION
# -----------------------------------------

def _validate_admin(db: Session, admin_id: int) -> User:
    """Validate that the requesting user is an active Administrator."""

    admin = db.get(User, admin_id)

    if admin is None:
        raise ValueError("Administrator not found.")

    role = db.get(Role, admin.role_id)

    if (
        role is None
        or role.name != "Administrator"
        or not role.is_active
        or admin.account_status != "active"
        or not admin.email_verified
    ):
        raise ValueError("Administrator access required.")

    return admin


# -----------------------------------------
# USER VALIDATION
# -----------------------------------------

def _get_target_user(db: Session, user_id: int) -> User:
    """Retrieve a user account by ID."""

    user = db.get(User, user_id)

    if user is None:
        raise ValueError("User not found.")

    return user


def _prevent_self_management(admin_id: int, user_id: int) -> None:
    """Prevent administrators from changing their own account status."""

    if admin_id == user_id:
        raise ValueError(
            "Administrator cannot change their own account status."
        )


# -----------------------------------------
# LIST ALL USERS
# -----------------------------------------

def list_users(
    db: Session,
    offset: int = 0,
    limit: int = 50,
) -> list[User]:
    """Return user accounts with pagination."""

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100.")

    statement = (
        select(User)
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


# -----------------------------------------
# GET USER DETAILS
# -----------------------------------------

def get_user_details(
    db: Session,
    user_id: int,
) -> User:
    """Return details of a specific user."""

    return _get_target_user(db, user_id)


# -----------------------------------------
# SUSPEND USER ACCOUNT
# -----------------------------------------

def suspend_user(
    db: Session,
    user_id: int,
    admin_id: int,
) -> User:
    """Suspend an active user account."""

    try:
        _validate_admin(db, admin_id)
        _prevent_self_management(admin_id, user_id)

        user = _get_target_user(db, user_id)

        if user.account_status != "active":
            raise ValueError("Only active accounts can be suspended.")

        user.account_status = "suspended"

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise


# -----------------------------------------
# REACTIVATE USER ACCOUNT
# -----------------------------------------

def reactivate_user(
    db: Session,
    user_id: int,
    admin_id: int,
) -> User:
    """Reactivate a suspended user account."""

    try:
        _validate_admin(db, admin_id)
        _prevent_self_management(admin_id, user_id)

        user = _get_target_user(db, user_id)

        if user.account_status != "suspended":
            raise ValueError(
                "Only suspended accounts can be reactivated."
            )

        user.account_status = "active"

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise


# -----------------------------------------
# DISABLE USER ACCOUNT
# -----------------------------------------

def disable_user(
    db: Session,
    user_id: int,
    admin_id: int,
) -> User:
    """Disable an active or suspended user account."""

    try:
        _validate_admin(db, admin_id)
        _prevent_self_management(admin_id, user_id)

        user = _get_target_user(db, user_id)

        if user.account_status not in {"active", "suspended"}:
            raise ValueError(
                "Only active or suspended accounts can be disabled."
            )

        user.account_status = "disabled"

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise
