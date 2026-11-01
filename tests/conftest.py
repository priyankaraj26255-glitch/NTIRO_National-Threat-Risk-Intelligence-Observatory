import os

# Force pytest to use the isolated test database.
os.environ["DB_NAME"] = "ntiro_test_db"

# Import the engine only after setting the database name.
from app.database import engine

# Safety check: never allow tests to run on the development database.
if engine.url.database != "ntiro_test_db":
    raise RuntimeError(
        "Safety check failed: pytest must use ntiro_test_db."
    )