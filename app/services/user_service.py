from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Role
from app.core.security import hash_password

from app.models import User


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:

    statement = select(User).where(
        User.email == email
    )

    return db.scalar(statement)
def get_public_registration_role(
    db: Session,
    role_id: int,
) -> Role | None:

    statement = select(Role).where(
        Role.id == role_id,
        Role.is_active.is_(True),
        Role.name != "Administrator",
    )


    return db.scalar(statement)
def register_user(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    role_id: int,
) -> User:

    existing_user = get_user_by_email(db, email)

    if existing_user is not None:
        raise ValueError("Email is already registered.")

    role = get_public_registration_role(db, role_id)

    if role is None:
        raise ValueError("Invalid or restricted role.")

    approval_status = (
        "not_required"
        if role.name == "Student"
        else "pending"
    )

    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
        role_id=role.id,
        email_verified=False,
        approval_status=approval_status,
        account_status="active",
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise

    return new_user