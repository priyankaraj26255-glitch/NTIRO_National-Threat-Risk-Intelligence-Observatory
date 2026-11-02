
from uuid import uuid4

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models import User, Role, EmailVerificationToken


client = TestClient(app)


def get_student_role_id(db):
    return db.scalar(
        select(Role.id).where(Role.name == "Student")
    )


def cleanup_user(email):
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is not None:
            db.delete(user)
            db.commit()


def test_registration_creates_user_and_verification_token():
    email = f"registration_{uuid4().hex}@example.com"

    with SessionLocal() as db:
        student_role_id = get_student_role_id(db)

    try:
        response = client.post(
            "/auth/register",
            json={
                "full_name": "Registration Test",
                "email": email,
                "password": "TestPassword123",
                "role_id": student_role_id,
            },
        )

        assert response.status_code == 201

        response_data = response.json()

        assert response_data["email"] == email
        assert response_data["email_verified"] is False
        assert response_data["approval_status"] == "not_required"

        # The public response must not contain the raw token.
        assert "token" not in response_data
        assert "password_hash" not in response_data

        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(User.email == email)
            )

            assert user is not None

            token_record = db.scalar(
                select(EmailVerificationToken).where(
                    EmailVerificationToken.user_id == user.id
                )
            )

            assert token_record is not None
            assert len(token_record.token_hash) == 64
            assert token_record.used_at is None

    finally:
        cleanup_user(email)


def test_duplicate_email_registration_is_rejected():
    email = f"duplicate_{uuid4().hex}@example.com"

    with SessionLocal() as db:
        student_role_id = get_student_role_id(db)

    payload = {
        "full_name": "Duplicate Test",
        "email": email,
        "password": "TestPassword123",
        "role_id": student_role_id,
    }

    try:
        first_response = client.post(
            "/auth/register",
            json=payload,
        )

        second_response = client.post(
            "/auth/register",
            json=payload,
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 409
        assert second_response.json()["detail"] == (
            "Email is already registered."
        )

    finally:
        cleanup_user(email)


def test_registration_rejects_administrator_role():
    with SessionLocal() as db:
        admin_role_id = db.scalar(
            select(Role.id).where(
                Role.name == "Administrator"
            )
        )

    email = f"admin_test_{uuid4().hex}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Admin Registration Test",
            "email": email,
            "password": "TestPassword123",
            "role_id": admin_role_id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or restricted role."
    )


def test_user_creation_rolls_back_if_token_creation_fails(
    monkeypatch,
):
    from app.services import user_service

    email = f"rollback_{uuid4().hex}@example.com"

    with SessionLocal() as db:
        student_role_id = get_student_role_id(db)

    def simulate_token_failure(db, user_id):
        raise RuntimeError("Simulated token creation failure.")

    monkeypatch.setattr(
        user_service,
        "add_verification_token",
        simulate_token_failure,
    )

    try:
        with SessionLocal() as db:
            with pytest.raises(RuntimeError):
                user_service.register_user(
                    db=db,
                    full_name="Rollback Test",
                    email=email,
                    password="TestPassword123",
                    role_id=student_role_id,
                )

            # The failed transaction must not leave a user behind.
            user = db.scalar(
                select(User).where(User.email == email)
            )

            assert user is None

    finally:
        cleanup_user(email)
