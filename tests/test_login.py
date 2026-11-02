
from uuid import uuid4

import jwt

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models import User, Role
from app.core.security import hash_password


client = TestClient(app)

TEST_PASSWORD = "TestPassword123"


def create_test_user(
    email,
    role_name="Student",
    email_verified=True,
    approval_status="not_required",
    account_status="active",
):
    with SessionLocal() as db:
        role = db.scalar(
            select(Role).where(Role.name == role_name)
        )

        assert role is not None, f"{role_name} role not found."

        user = User(
            full_name="Login Test User",
            email=email,
            password_hash=hash_password(TEST_PASSWORD),
            role_id=role.id,
            email_verified=email_verified,
            approval_status=approval_status,
            account_status=account_status,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user.id


def cleanup_user(email):
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is not None:
            db.delete(user)
            db.commit()


def test_successful_login_generates_access_token(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-login-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    email = f"login_{uuid4().hex}@example.com"

    user_id = create_test_user(email)

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": TEST_PASSWORD,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["token_type"] == "bearer"
        assert data["user_id"] == user_id
        assert data["email"] == email
        assert data["email_verified"] is True
        assert "access_token" in data

        # Verify the JWT signature and claims.
        payload = jwt.decode(
            data["access_token"],
            "test-secret-key-for-ntiro-login-tests",
            algorithms=["HS256"],
        )

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

        # Sensitive password information must not be returned.
        assert "password" not in data
        assert "password_hash" not in data

    finally:
        cleanup_user(email)


def test_login_rejects_incorrect_password(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-login-tests",
    )

    email = f"wrong_password_{uuid4().hex}@example.com"

    create_test_user(email)

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "WrongPassword123",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "Invalid email or password."
        )

    finally:
        cleanup_user(email)


def test_login_rejects_unverified_email(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-login-tests",
    )

    email = f"unverified_{uuid4().hex}@example.com"

    create_test_user(
        email,
        email_verified=False,
    )

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": TEST_PASSWORD,
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Please verify your email before logging in."
        )

    finally:
        cleanup_user(email)


def test_login_rejects_suspended_account(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-login-tests",
    )

    email = f"suspended_{uuid4().hex}@example.com"

    create_test_user(
        email,
        account_status="suspended",
    )

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": TEST_PASSWORD,
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Your account is not active."
        )

    finally:
        cleanup_user(email)


def test_login_rejects_disabled_account(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-login-tests",
    )

    email = f"disabled_{uuid4().hex}@example.com"

    create_test_user(
        email,
        account_status="disabled",
    )

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": TEST_PASSWORD,
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Your account is not active."
        )

    finally:
        cleanup_user(email)


def test_pending_professional_can_login(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-login-tests",
    )

    email = f"pending_{uuid4().hex}@example.com"

    create_test_user(
        email,
        role_name="Researcher",
        email_verified=True,
        approval_status="pending",
    )

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": TEST_PASSWORD,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["approval_status"] == "pending"
        assert data["email_verified"] is True
        assert data["token_type"] == "bearer"

    finally:
        cleanup_user(email)

