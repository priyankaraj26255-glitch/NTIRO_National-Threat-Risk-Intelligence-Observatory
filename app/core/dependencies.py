
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.core.token import decode_access_token
from app.database_dependency import get_db
from app.models.role import Role
from app.models.user import User


# Roles that require administrator approval.
PROFESSIONAL_ROLES = {
    "Researcher",
    "Police Department",
    "Cybersecurity Analyst",
    "Fraud Analyst",
    "Policy Analyst",
    "Journalist",
    "Smart City Planner",
}


# Extract Bearer token from the Authorization header.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT and return the authenticated user."""

    # Check whether the request contains a bearer token.
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate and decode the JWT.
    try:
        payload = decode_access_token(credentials.credentials)

        user_id = int(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retrieve the user from the database.
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token was not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account status.
    if user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active.",
        )

    # Check email verification.
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before accessing this resource.",
        )

    return user


def require_roles(*allowed_roles: str):
    """Allow access only to users with specified roles."""

    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:

        role = db.get(Role, current_user.role_id)

        if role is None or not role.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your assigned role is unavailable.",
            )

        if role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        return current_user

    return role_checker


def require_approved_professional(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Allow only approved professional users."""

    role = db.get(Role, current_user.role_id)

    if role is None or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your assigned role is unavailable.",
        )

    if role.name not in PROFESSIONAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This resource is restricted to professional users.",
        )

    if current_user.approval_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your professional account is not approved.",
        )

    return current_user


def require_admin(
    current_user: User = Depends(
        require_roles("Administrator")
    ),
) -> User:
    """Allow access only to administrators."""

    return current_user
