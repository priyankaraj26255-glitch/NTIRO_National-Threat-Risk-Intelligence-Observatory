
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, Role


PROFESSIONAL_ROLES = {
    "Researcher",
    "Police Department",
    "Cybersecurity Analyst",
    "Fraud Analyst",
    "Policy Analyst",
    "Journalist",
    "Smart City Planner",
}


def _validate_admin(db: Session, admin_id: int) -> User:
    """Validate that the requesting user is an active Administrator."""

    admin = db.get(User, admin_id)

    if admin is None:
        raise ValueError("Administrator not found.")

    admin_role = db.get(Role, admin.role_id)

    if (
        admin_role is None
        or admin_role.name != "Administrator"
        or not admin_role.is_active
        or admin.account_status != "active"
        or not admin.email_verified
    ):
        raise ValueError("Administrator access required.")

    return admin


def _get_pending_professional(
    db: Session,
    user_id: int,
) -> User:
    """Fetch and validate a professional account awaiting review."""

    statement = (
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(User.id == user_id)
    )

    user = db.scalar(statement)

    if user is None:
        raise ValueError("User not found.")

    role = db.get(Role, user.role_id)

    if role is None or role.name not in PROFESSIONAL_ROLES:
        raise ValueError("Only professional accounts can be reviewed.")

    if not role.is_active:
        raise ValueError("User role is inactive.")

    if not user.email_verified:
        raise ValueError(
            "Professional email must be verified before approval."
        )

    if user.account_status != "active":
        raise ValueError("User account is not active.")

    if user.approval_status != "pending":
        raise ValueError("Only pending accounts can be reviewed.")

    return user


def get_pending_professionals(db: Session) -> list[User]:
    """Return verified, active professionals awaiting Administrator review."""

    statement = (
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(
            User.approval_status == "pending",
            User.email_verified.is_(True),
            User.account_status == "active",
            Role.name.in_(PROFESSIONAL_ROLES),
            Role.is_active.is_(True),
        )
        .order_by(User.created_at.asc())
    )

    return list(db.scalars(statement).all())


def approve_professional(
    db: Session,
    user_id: int,
    admin_id: int,
) -> User:
    """Approve a verified professional account."""

    try:
        _validate_admin(db, admin_id)

        if user_id == admin_id:
            raise ValueError(
                "Administrator cannot approve their own account."
            )

        user = _get_pending_professional(db, user_id)

        user.approval_status = "approved"
        user.approved_by = admin_id
        user.approved_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise


def reject_professional(
    db: Session,
    user_id: int,
    admin_id: int,
) -> User:
    """Reject a verified professional account."""

    try:
        _validate_admin(db, admin_id)

        if user_id == admin_id:
            raise ValueError(
                "Administrator cannot reject their own account."
            )

        user = _get_pending_professional(db, user_id)

        user.approval_status = "rejected"
        user.approved_by = admin_id
        user.approved_at = None

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise
