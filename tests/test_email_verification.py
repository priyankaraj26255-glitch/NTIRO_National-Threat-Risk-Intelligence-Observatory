from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models import User, Role, EmailVerificationToken
from app.core.security import hash_password
from app.services.email_verification_service import create_verification_token


client = TestClient(app)


@pytest.fixture
def user_with_token():
    db = SessionLocal()

    try:
        student_role = db.scalar(
            select(Role).where(Role.name == "Student")
        )

        user = User(
            full_name="Test User",
            email=f"test_{uuid4().hex}@example.com",
            password_hash=hash_password("TestPassword123"),
            role_id=student_role.id,
            email_verified=False,
            approval_status="not_required",
            account_status="active",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        raw_token = create_verification_token(db, user.id)

        yield {
            "user": user,
            "token": raw_token,
            "db": db,
        }

    finally:
        if "user" in locals():
            db.delete(user)
            db.commit()

        db.close()


def test_email_verification_success(user_with_token):
    response = client.post(
        "/auth/verify-email",
        json={"token": user_with_token["token"]},
    )

    assert response.status_code == 200
    assert response.json()["email_verified"] is True


def test_invalid_verification_token():
    response = client.post(
        "/auth/verify-email",
        json={"token": "invalid_token_123456789"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid verification token."


def test_expired_verification_token(user_with_token):
    db = user_with_token["db"]
    user = user_with_token["user"]

    token_record = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id
        )
    )

    token_record.expires_at = (
        datetime.now(timezone.utc) - timedelta(minutes=1)
    )
    db.commit()

    response = client.post(
        "/auth/verify-email",
        json={"token": user_with_token["token"]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Verification token has expired."


def test_verification_token_cannot_be_reused(user_with_token):
    token = user_with_token["token"]

    first_response = client.post(
        "/auth/verify-email",
        json={"token": token},
    )

    second_response = client.post(
        "/auth/verify-email",
        json={"token": token},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "Verification token has already been used."
    )


def test_already_verified_email(user_with_token):
    db = user_with_token["db"]
    user = user_with_token["user"]

    user.email_verified = True
    db.commit()

    response = client.post(
        "/auth/verify-email",
        json={"token": user_with_token["token"]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already verified."