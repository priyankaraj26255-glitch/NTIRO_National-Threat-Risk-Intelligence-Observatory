from sqlalchemy import select

from app.database import SessionLocal
from app.models import Role


ROLES = [
    ("Student", "Academic learning and project access"),
    ("Researcher", "Threat and risk research"),
    ("Police Department", "Crime intelligence and analysis"),
    ("Cybersecurity Analyst", "Cyber threat analysis"),
    ("Fraud Analyst", "Financial fraud analysis"),
    ("Policy Analyst", "Policy research and planning"),
    ("Journalist", "Public information analysis"),
    ("Smart City Planner", "Urban risk and planning"),
    ("Administrator", "Platform administration"),
]


def seed_roles():
    with SessionLocal() as db:
        for name, description in ROLES:
            existing_role = db.scalar(
                select(Role).where(Role.name == name)
            )

            if existing_role is None:
                db.add(Role(name=name, description=description))

        db.commit()


if __name__ == "__main__":
    seed_roles()
    print("NTIRO roles seeded successfully.")