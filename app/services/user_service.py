from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models import User, Role
from app.core.security import hash_password
from app.services.email_verification_service import add_verification_token

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
) -> tuple[User, str]:

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

        # Obtain the database-generated user ID.
        db.flush()

        # Add verification token to the same transaction.
        raw_token = add_verification_token(
            db=db,
            user_id=new_user.id,
        )

        # Commit user and token together.
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise

    return new_user, raw_token

def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    """
    Authenticate a user using email and password.

    Returns the authenticated user if account checks pass.
    """

    user = get_user_by_email(db, email)

    # Use a generic message to avoid revealing whether an email exists.
    if user is None:
        raise ValueError("Invalid email or password.")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password.")

    # Email ownership must be verified before login.
    if not user.email_verified:
        raise ValueError("Please verify your email before logging in.")

    # Suspended and disabled accounts cannot log in.
    if user.account_status != "active":
        raise ValueError("Your account is not active.")

    # Pending and rejected professional accounts can authenticate,
    # but authorization will restrict them to their status page.
    return user
