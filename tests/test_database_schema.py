
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine


def test_schema_relationships():
    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            category_id = connection.execute(
                text("""
                    INSERT INTO incident_categories (name, is_active)
                    VALUES ('Test Category', TRUE)
                    RETURNING id
                """)
            ).scalar_one()

            state_id = connection.execute(
                text("""
                    INSERT INTO states (name, code)
                    VALUES ('Test State', 'TST')
                    RETURNING id
                """)
            ).scalar_one()

            district_id = connection.execute(
                text("""
                    INSERT INTO districts (state_id, name, code)
                    VALUES (:state_id, 'Test District', 'TSTD')
                    RETURNING id
                """),
                {"state_id": state_id},
            ).scalar_one()

            incident_id = connection.execute(
                text("""
                    INSERT INTO incidents (
                        category_id, state_id, district_id,
                        validation_status
                    )
                    VALUES (
                        :category_id, :state_id, :district_id,
                        'pending_review'
                    )
                    RETURNING id
                """),
                {
                    "category_id": category_id,
                    "state_id": state_id,
                    "district_id": district_id,
                },
            ).scalar_one()

            connection.execute(
                text("""
                    INSERT INTO source_reports (
                        incident_id, source_name,
                        review_status, evidence_status
                    )
                    VALUES (
                        :incident_id, 'Test Source',
                        'pending_review', 'unassessed'
                    )
                """),
                {"incident_id": incident_id},
            )

        finally:
            transaction.rollback()


def test_incident_rejects_district_from_another_state():
    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            category_id = connection.execute(
                text("""
                    INSERT INTO incident_categories (name, is_active)
                    VALUES ('Test Category', TRUE)
                    RETURNING id
                """)
            ).scalar_one()

            state_a_id = connection.execute(
                text("""
                    INSERT INTO states (name, code)
                    VALUES ('Test State A', 'TSTA')
                    RETURNING id
                """)
            ).scalar_one()

            state_b_id = connection.execute(
                text("""
                    INSERT INTO states (name, code)
                    VALUES ('Test State B', 'TSTB')
                    RETURNING id
                """)
            ).scalar_one()

            district_b_id = connection.execute(
                text("""
                    INSERT INTO districts (state_id, name, code)
                    VALUES (:state_id, 'Test District B', 'TSTDB')
                    RETURNING id
                """),
                {"state_id": state_b_id},
            ).scalar_one()

            try:
                connection.execute(
                    text("""
                        INSERT INTO incidents (
                            category_id, state_id, district_id,
                            validation_status
                        )
                        VALUES (
                            :category_id, :state_id, :district_id,
                            'pending_review'
                        )
                    """),
                    {
                        "category_id": category_id,
                        "state_id": state_a_id,
                        "district_id": district_b_id,
                    },
                )

                assert False, (
                    "Expected PostgreSQL to reject a district "
                    "belonging to a different state."
                )

            except IntegrityError as exc:
                assert exc.orig.sqlstate == "23503"

        finally:
            transaction.rollback()
