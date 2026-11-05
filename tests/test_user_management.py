
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, Role
from app.core.security import hash_password

from app.services.User_Manag_service import (
    list_users,
    get_user_details,
    suspend_user,
    reactivate_user,
    disable_user,
)


def create_test_user(
    role_name: str,
    account_status: str = "active",
    email_verified: bool = True,
):
    """Create a temporary user for service testing."""

    email = f"user_management_{uuid4().hex}@example.com"

    with SessionLocal() as db:
        role = db.scalar(
            select(Role).where(Role.name == role_name)
        )

        assert role is not None, f"{role_name} role not found."

        user = User(
            full_name="User Management Test",
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

    return email, user_id


def cleanup_test_user(email: str):
    """Remove temporary test users."""

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is not None:
            db.delete(user)
            db.commit()


# -----------------------------------------
# USER LISTING TESTS
# -----------------------------------------

def test_list_users_returns_users():

    email, user_id = create_test_user("Student")

    try:
        with SessionLocal() as db:
            users = list_users(db)

            assert any(user.id == user_id for user in users)

    finally:
        cleanup_test_user(email)


def test_list_users_rejects_invalid_pagination():

    with SessionLocal() as db:

        with pytest.raises(ValueError):
            list_users(db, offset=-1)

        with pytest.raises(ValueError):
            list_users(db, limit=101)


# -----------------------------------------
# USER DETAIL TESTS
# -----------------------------------------

def test_get_user_details():

    email, user_id = create_test_user("Student")

    try:
        with SessionLocal() as db:
            user = get_user_details(db, user_id)

            assert user.id == user_id

    finally:
        cleanup_test_user(email)


def test_get_user_details_returns_error_for_missing_user():

    with SessionLocal() as db:

        with pytest.raises(ValueError, match="User not found"):
            get_user_details(db, 999999999)


# -----------------------------------------
# ACCOUNT SUSPENSION TESTS
# -----------------------------------------

def test_admin_can_suspend_active_user():

    admin_email, admin_id = create_test_user("Administrator")
    user_email, user_id = create_test_user("Student")

    try:
        with SessionLocal() as db:
            user = suspend_user(db, user_id, admin_id)

            assert user.account_status == "suspended"

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_suspending_already_suspended_user_fails():

    admin_email, admin_id = create_test_user("Administrator")
    user_email, user_id = create_test_user(
        "Student",
        account_status="suspended",
    )

    try:
        with SessionLocal() as db:
            with pytest.raises(
                ValueError,
                match="Only active accounts can be suspended",
            ):
                suspend_user(db, user_id, admin_id)

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


# -----------------------------------------
# ACCOUNT REACTIVATION TESTS
# -----------------------------------------

def test_admin_can_reactivate_suspended_user():

    admin_email, admin_id = create_test_user("Administrator")
    user_email, user_id = create_test_user(
        "Student",
        account_status="suspended",
    )

    try:
        with SessionLocal() as db:
            user = reactivate_user(db, user_id, admin_id)

            assert user.account_status == "active"

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_disabled_user_cannot_be_reactivated():

    admin_email, admin_id = create_test_user("Administrator")
    user_email, user_id = create_test_user(
        "Student",
        account_status="disabled",
    )

    try:
        with SessionLocal() as db:
            with pytest.raises(
                ValueError,
                match="Only suspended accounts can be reactivated",
            ):
                reactivate_user(db, user_id, admin_id)

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


# -----------------------------------------
# ACCOUNT DISABLING TESTS
# -----------------------------------------

def test_admin_can_disable_active_user():

    admin_email, admin_id = create_test_user("Administrator")
    user_email, user_id = create_test_user("Student")

    try:
        with SessionLocal() as db:
            user = disable_user(db, user_id, admin_id)

            assert user.account_status == "disabled"

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_admin_can_disable_suspended_user():

    admin_email, admin_id = create_test_user("Administrator")
    user_email, user_id = create_test_user(
        "Student",
        account_status="suspended",
    )

    try:
        with SessionLocal() as db:
            user = disable_user(db, user_id, admin_id)

            assert user.account_status == "disabled"

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


def test_disabled_user_cannot_be_disabled_again():

    admin_email, admin_id = create_test_user("Administrator")
    user_email, user_id = create_test_user(
        "Student",
        account_status="disabled",
    )

    try:
        with SessionLocal() as db:
            with pytest.raises(
                ValueError,
                match="Only active or suspended accounts can be disabled",
            ):
                disable_user(db, user_id, admin_id)

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)


# -----------------------------------------
# ADMIN SELF-PROTECTION TESTS
# -----------------------------------------

def test_admin_cannot_suspend_own_account():

    admin_email, admin_id = create_test_user("Administrator")

    try:
        with SessionLocal() as db:
            with pytest.raises(
                ValueError,
                match="cannot change their own account status",
            ):
                suspend_user(db, admin_id, admin_id)

    finally:
        cleanup_test_user(admin_email)


def test_admin_cannot_disable_own_account():

    admin_email, admin_id = create_test_user("Administrator")

    try:
        with SessionLocal() as db:
            with pytest.raises(
                ValueError,
                match="cannot change their own account status",
            ):
                disable_user(db, admin_id, admin_id)

    finally:
        cleanup_test_user(admin_email)


# -----------------------------------------
# ADMIN AUTHORIZATION TESTS
# -----------------------------------------

def test_student_cannot_manage_user_accounts():

    student_email, student_id = create_test_user("Student")
    user_email, user_id = create_test_user("Student")

    try:
        with SessionLocal() as db:
            with pytest.raises(
                ValueError,
                match="Administrator access required",
            ):
                suspend_user(db, user_id, student_id)

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(student_email)


def test_unverified_admin_cannot_manage_user_accounts():

    admin_email, admin_id = create_test_user(
        "Administrator",
        email_verified=False,
    )
    user_email, user_id = create_test_user("Student")

    try:
        with SessionLocal() as db:
            with pytest.raises(
                ValueError,
                match="Administrator access required",
            ):
                suspend_user(db, user_id, admin_id)

    finally:
        cleanup_test_user(user_email)
        cleanup_test_user(admin_email)
