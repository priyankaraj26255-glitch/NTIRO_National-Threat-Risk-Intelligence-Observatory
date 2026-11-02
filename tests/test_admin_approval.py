
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models import User, Role
from app.core.security import hash_password
from app.core.token import create_access_token


client = TestClient(app)


def create_test_user(
    role_name: str,
    approval_status: str = "not_required",
    email_verified: bool = True,
):
    email = f"admin_test_{uuid4().hex}@example.com"

    with SessionLocal() as db:
        role = db.scalar(
            select(Role).where(Role.name == role_name)
        )

        assert role is not None, f"{role_name} role not found."

        user = User(
            full_name="Approval Test User",
            email=email,
            password_hash=hash_password("TestPassword123"),
            role_id=role.id,
            email_verified=email_verified,
            approval_status=approval_status,
            account_status="active",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        user_id = user.id

    token = create_access_token(user_id=user_id)

    return email, user_id, token


def cleanup_test_user(email: str):
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is not None:
            db.delete(user)
            db.commit()


def set_test_jwt_environment(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-for-ntiro-admin-tests",
    )
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")


def test_admin_can_view_pending_professionals(monkeypatch):
    set_test_jwt_environment(monkeypatch)

    admin_email, _, admin_token = create_test_user(
        "Administrator"
    )

    user_email, user_id, _ = create_test_user(
        "Researcher",
        approval_status="pending",
    )

    try:
        response = client.get(
            "/admin/pending-professionals",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total_pending"] >= 1
        assert any(user["id"] == user_id for user in data["users"])

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_admin_can_approve_professional(monkeypatch):
    set_test_jwt_environment(monkeypatch)

    admin_email, admin_id, admin_token = create_test_user(
        "Administrator"
    )

    user_email, user_id, _ = create_test_user(
        "Researcher",
        approval_status="pending",
    )

    try:
        response = client.post(
            f"/admin/users/{user_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["user_id"] == user_id
        assert data["approval_status"] == "approved"
        assert data["approved_by"] == admin_id
        assert data["approved_at"] is not None

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_admin_can_reject_professional(monkeypatch):
    set_test_jwt_environment(monkeypatch)

    admin_email, admin_id, admin_token = create_test_user(
        "Administrator"
    )

    user_email, user_id, _ = create_test_user(
        "Researcher",
        approval_status="pending",
    )

    try:
        response = client.post(
            f"/admin/users/{user_id}/reject",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["user_id"] == user_id
        assert data["approval_status"] == "rejected"
        assert data["approved_by"] == admin_id
        assert data["approved_at"] is None

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_student_cannot_access_admin_endpoint(monkeypatch):
    set_test_jwt_environment(monkeypatch)

    student_email, _, student_token = create_test_user("Student")

    try:
        response = client.get(
            "/admin/pending-professionals",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 403

    finally:
        cleanup_test_user(student_email)


def test_admin_endpoint_rejects_missing_token():
    response = client.get("/admin/pending-professionals")

    assert response.status_code == 401


def test_approval_returns_404_for_nonexistent_user(monkeypatch):
    set_test_jwt_environment(monkeypatch)

    admin_email, _, admin_token = create_test_user("Administrator")

    try:
        response = client.post(
            "/admin/users/999999999/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    finally:
        cleanup_test_user(admin_email)


def test_already_approved_user_cannot_be_approved_again(
    monkeypatch,
):
    set_test_jwt_environment(monkeypatch)

    admin_email, _, admin_token = create_test_user("Administrator")

    user_email, user_id, _ = create_test_user(
        "Researcher",
        approval_status="approved",
    )

    try:
        response = client.post(
            f"/admin/users/{user_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


# --------------------------------------------------
# EMAIL VERIFICATION SECURITY TESTS
# --------------------------------------------------

def test_unverified_professional_is_excluded_from_pending_list(
    monkeypatch,
):
    set_test_jwt_environment(monkeypatch)

    admin_email, _, admin_token = create_test_user("Administrator")

    user_email, user_id, _ = create_test_user(
        "Researcher",
        approval_status="pending",
        email_verified=False,
    )

    try:
        response = client.get(
            "/admin/pending-professionals",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert all(
            user["id"] != user_id
            for user in data["users"]
        )

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_admin_cannot_approve_unverified_professional(
    monkeypatch,
):
    set_test_jwt_environment(monkeypatch)

    admin_email, _, admin_token = create_test_user("Administrator")

    user_email, user_id, _ = create_test_user(
        "Researcher",
        approval_status="pending",
        email_verified=False,
    )

    try:
        response = client.post(
            f"/admin/users/{user_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

        assert "email must be verified" in response.json()["detail"].lower()

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_admin_cannot_reject_unverified_professional(
    monkeypatch,
):
    set_test_jwt_environment(monkeypatch)

    admin_email, _, admin_token = create_test_user("Administrator")

    user_email, user_id, _ = create_test_user(
        "Researcher",
        approval_status="pending",
        email_verified=False,
    )

    try:
        response = client.post(
            f"/admin/users/{user_id}/reject",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

        assert "email must be verified" in response.json()["detail"].lower()

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)
