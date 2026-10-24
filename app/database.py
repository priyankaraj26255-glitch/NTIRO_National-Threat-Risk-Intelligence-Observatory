
import os
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

load_dotenv()

required_settings = [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
]

missing_settings = [
    key for key in required_settings
    if not os.getenv(key)
]

if missing_settings:
    raise RuntimeError(
        f"Missing database settings: {', '.join(missing_settings)}"
    )

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)
class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    
)