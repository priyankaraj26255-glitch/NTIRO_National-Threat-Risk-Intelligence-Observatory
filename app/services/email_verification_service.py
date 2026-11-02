
import hashlib
import secrets

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import EmailVerificationToken, User


def generate_verification_token() -> tuple[str, str]:
    """Generate a secure raw token and its SHA-256 hash."""

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    return raw_token, token_hash


def get_token_expiry() -> datetime:
    """Set verification token expiry to 30 minutes."""

    return datetime.now(timezone.utc) + timedelta(minutes=30)


def add_verification_token(
    db: Session,
    user_id: int,
) -> str:
    """
    Add a verification token to the current transaction.

    This function does not commit.
    """

    raw_token, token_hash = generate_verification_token()

    expires_at = get_token_expiry()

    db.execute(
        delete(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user_id
        )
    )

    verification_token = EmailVerificationToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(verification_token)

    return raw_token


def create_verification_token(
    db: Session,
    user_id: int,
) -> str:
    """
    Create and commit a verification token independently.
    """

    try:
        raw_token = add_verification_token(
            db=db,
            user_id=user_id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return raw_token


def verify_email_token(
    db: Session,
    raw_token: str,
) -> User:
    """
    Validate a verification token and verify the user's email.
    """

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    statement = (
        select(EmailVerificationToken)
        .where(
            EmailVerificationToken.token_hash == token_hash
        )
        .with_for_update()
    )

    try:
        verification_token = db.scalar(statement)

        if verification_token is None:
            raise ValueError("Invalid verification token.")

        if verification_token.used_at is not None:
            raise ValueError(
                "Verification token has already been used."
            )

        now = datetime.now(timezone.utc)

        if verification_token.expires_at <= now:
            raise ValueError(
                "Verification token has expired."
            )

        user = db.get(
            User,
            verification_token.user_id,
        )

        if user is None:
            raise ValueError("User not found.")

        if user.email_verified:
            raise ValueError(
                "Email is already verified."
            )

        user.email_verified = True
        verification_token.used_at = now

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise
