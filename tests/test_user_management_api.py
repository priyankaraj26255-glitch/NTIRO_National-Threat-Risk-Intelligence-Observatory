
from uuid import uuid4

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models import User, Role
from app.core.security import hash_password
from app.core.token import create_access_token


client = TestClient(app)


# -----------------------------------------
# TEST ENVIRONMENT
# -----------------------------------------

@pytest.fixture(autouse=True)
def set_test_jwt_environment(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-admin-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")


# -----------------------------------------
# TEST USER HELPERS
# -----------------------------------------

def create_test_user(
    role_name: str,
    account_status: str = "active",
    email_verified: bool = True,
):
    """Create a temporary user and generate an access token."""

    email = f"user_api_{uuid4().hex}@example.com"

    with SessionLocal() as db:
        role = db.scalar(
            select(Role).where(Role.name == role_name)
        )

        assert role is not None, f"{role_name} role not found."

        user = User(
            full_name="API Integration Test User",
            email=email,
            password_hash=hash_password("TestPassword123"),
            role_id=role.id,
            email_verified=email_verified,
            approval_status="not_required",
            account_status=account_status,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id

    token = create_access_token(user_id=user_id)

    return email, user_id, token


def cleanup_test_user(email: str):
    """Delete a temporary test user."""

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is not None:
            db.delete(user)
            db.commit()


def admin_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------
# AUTHENTICATION TESTS
# -----------------------------------------

def test_admin_api_requires_authentication():

    response = client.get("/admin/users")

    assert response.status_code == 401


def test_student_cannot_access_admin_user_list():

    email, user_id, token = create_test_user("Student")

    try:
        response = client.get(
            "/admin/users",
            headers=admin_headers(token),
        )

        assert response.status_code == 403

    finally:
        cleanup_test_user(email)


# -----------------------------------------
# USER LISTING TESTS
# -----------------------------------------

def test_admin_can_list_users():

    admin_email, admin_id, admin_token = create_test_user(
        "Administrator"
    )
    user_email, user_id, _ = create_test_user("Student")

    try:
        response = client.get(
            "/admin/users?offset=0&limit=100",
            headers=admin_headers(admin_token),
        )

        assert response.status_code == 200

        data = response.json()

        assert "users" in data
        assert data["offset"] == 0
        assert data["limit"] == 100
        assert data["returned"] >= 1

        user_ids = [user["id"] for user in data["users"]]

        assert user_id in user_ids

        # Sensitive password data must never be exposed.
        assert "password_hash" not in data["users"][0]

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_admin_user_list_rejects_invalid_pagination():

    admin_email, admin_id, token = create_test_user(
        "Administrator"
    )

    try:
        response = client.get(
            "/admin/users?offset=-1",
            headers=admin_headers(token),
        )

        assert response.status_code == 422

        response = client.get(
            "/admin/users?limit=101",
            headers=admin_headers(token),
        )

        assert response.status_code == 422

    finally:
        cleanup_test_user(admin_email)


# -----------------------------------------
# USER DETAIL TESTS
# -----------------------------------------

def test_admin_can_view_user_details():

    admin_email, admin_id, token = create_test_user(
        "Administrator"
    )
    user_email, user_id, _ = create_test_user("Student")

    try:
        response = client.get(
            f"/admin/users/{user_id}",
            headers=admin_headers(token),
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == user_id
        assert data["email"] == user_email
        assert data["account_status"] == "active"
        assert "approved_by" in data
        assert "password_hash" not in data

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_admin_get_missing_user_returns_404():

    admin_email, admin_id, token = create_test_user(
        "Administrator"
    )

    try:
        response = client.get(
            "/admin/users/999999999",
            headers=admin_headers(token),
        )

        assert response.status_code == 404

    finally:
        cleanup_test_user(admin_email)


# -----------------------------------------
# ACCOUNT STATUS LIFECYCLE TEST
# -----------------------------------------

def test_admin_can_manage_account_status():

    admin_email, admin_id, token = create_test_user(
        "Administrator"
    )
    user_email, user_id, _ = create_test_user("Student")

    headers = admin_headers(token)

    try:
        # 1. Suspend active account.
        response = client.post(
            f"/admin/users/{user_id}/suspend",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["account_status"] == "suspended"

        # 2. Reactivate suspended account.
        response = client.post(
            f"/admin/users/{user_id}/reactivate",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["account_status"] == "active"

        # 3. Suspend again.
        response = client.post(
            f"/admin/users/{user_id}/suspend",
            headers=headers,
        )

        assert response.status_code == 200

        # 4. Disable suspended account.
        response = client.post(
            f"/admin/users/{user_id}/disable",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["account_status"] == "disabled"

        # 5. Disabled account cannot be reactivated.
        response = client.post(
            f"/admin/users/{user_id}/reactivate",
            headers=headers,
        )

        assert response.status_code == 400

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


# -----------------------------------------
# ADMIN SELF-PROTECTION TEST
# -----------------------------------------

def test_admin_cannot_suspend_own_account():

    admin_email, admin_id, token = create_test_user(
        "Administrator"
    )

    try:
        response = client.post(
            f"/admin/users/{admin_id}/suspend",
            headers=admin_headers(token),
        )

        assert response.status_code == 400
        assert "own account status" in response.json()["detail"]

    finally:
        cleanup_test_user(admin_email)

