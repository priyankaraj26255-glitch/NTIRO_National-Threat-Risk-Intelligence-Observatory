
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models import User, Role
from app.core.security import hash_password
from app.core.token import create_access_token
from app.core.dependencies import (
    require_roles,
    require_approved_professional,
    require_admin,
)


# Test-only routes. These are not production application routes.
test_router = APIRouter(prefix="/_test/rbac")


@test_router.get("/student")
def student_endpoint(
    current_user: User = Depends(require_roles("Student")),
):
    return {"message": "Student access granted"}


@test_router.get("/admin")
def admin_endpoint(
    current_user: User = Depends(require_admin),
):
    return {"message": "Administrator access granted"}


@test_router.get("/professional")
def professional_endpoint(
    current_user: User = Depends(require_approved_professional),
):
    return {"message": "Professional access granted"}


app.include_router(test_router)
client = TestClient(app)


def create_authorization_user(
    role_name: str,
    approval_status: str = "not_required",
):
    email = f"rbac_{uuid4().hex}@example.com"

    with SessionLocal() as db:
        role = db.scalar(
            select(Role).where(Role.name == role_name)
        )

        assert role is not None, f"{role_name} role not found."

        user = User(
            full_name="RBAC Test User",
            email=email,
            password_hash=hash_password("TestPassword123"),
            role_id=role.id,
            email_verified=True,
            approval_status=approval_status,
            account_status="active",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id

    token = create_access_token(user_id=user_id)

    return email, token


def cleanup_authorization_user(email: str):
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is not None:
            db.delete(user)
            db.commit()


def test_student_can_access_student_endpoint(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-rbac-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    email, token = create_authorization_user("Student")

    try:
        response = client.get(
            "/_test/rbac/student",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Student access granted"

    finally:
        cleanup_authorization_user(email)


def test_student_cannot_access_admin_endpoint(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-rbac-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    email, token = create_authorization_user("Student")

    try:
        response = client.get(
            "/_test/rbac/admin",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    finally:
        cleanup_authorization_user(email)


def test_admin_can_access_admin_endpoint(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-rbac-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    email, token = create_authorization_user("Administrator")

    try:
        response = client.get(
            "/_test/rbac/admin",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == (
            "Administrator access granted"
        )

    finally:
        cleanup_authorization_user(email)


def test_pending_professional_cannot_access_professional_endpoint(
    monkeypatch,
):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-rbac-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    email, token = create_authorization_user(
        "Researcher",
        approval_status="pending",
    )

    try:
        response = client.get(
            "/_test/rbac/professional",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    finally:
        cleanup_authorization_user(email)


def test_approved_professional_can_access_professional_endpoint(
    monkeypatch,
):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-rbac-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    email, token = create_authorization_user(
        "Researcher",
        approval_status="approved",
    )

    try:
        response = client.get(
            "/_test/rbac/professional",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == (
            "Professional access granted"
        )

    finally:
        cleanup_authorization_user(email)


def test_rbac_endpoint_rejects_missing_token():
    response = client.get("/_test/rbac/student")

    assert response.status_code == 401


def test_rbac_endpoint_rejects_invalid_token(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-rbac-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")

    response = client.get(
        "/_test/rbac/student",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401

