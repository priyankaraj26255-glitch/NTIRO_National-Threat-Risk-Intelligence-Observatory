
import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Role, User
from app.core.security import hash_password


def create_admin():
    db = SessionLocal()

    try:
        print("\n=== NTIRO First Administrator Setup ===\n")

        # Require explicit confirmation before creating a privileged account.
        confirmation = input(
            "Type CREATE FIRST NTIRO ADMIN to continue: "
        ).strip()

        if confirmation != "CREATE FIRST NTIRO ADMIN":
            print("Administrator setup cancelled.")
            return

        # Prevent accidental creation of another Administrator.
        existing_admin = db.execute(
            select(User)
            .join(Role)
            .where(Role.name == "Administrator")
            .limit(1)
        ).scalars().first()

        if existing_admin:
            print("An Administrator account already exists.")
            return

        # Find the Administrator role.
        role = db.execute(
            select(Role).where(Role.name == "Administrator")
        ).scalar_one_or_none()

        if role is None:
            print("Administrator role not found. Run role seeding first.")
            return

        # Collect account information.
        full_name = input("Enter administrator name: ").strip()
        email = input("Enter administrator email: ").strip().lower()

        if not full_name or not email:
            print("Name and email are required.")
            return

        # Prevent duplicate email registration.
        existing_user = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if existing_user:
            print("This email is already registered.")
            return

        # Securely collect and confirm the password.
        password = getpass.getpass(
            "Create administrator password: "
        )
        confirm_password = getpass.getpass(
            "Confirm password: "
        )

        if len(password) < 12:
            print("Password must contain at least 12 characters.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        # Create the first Administrator account.
        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role_id=role.id,
            email_verified=True,
            approval_status="not_required",
            account_status="active",
            approved_by=None,
            approved_at=None,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\nAdministrator account created successfully!")
        print(f"Administrator ID: {admin.id}")
        print(f"Administrator email: {admin.email}")
        print(f"Role: {role.name}")
        print("Account status: active")
        print("Email verified: True")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
