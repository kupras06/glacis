from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings


def ensure_database_exists(db_url: str):
    url = make_url(db_url)

    db_name = url.database

    # connect to default postgres database
    default_url = url.set(database="postgres")

    engine = create_engine(default_url)

    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname=:name"),
            {"name": db_name},
        ).scalar()

        if not result:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            print(f"[DB] Created database: {db_name}")
        else:
            print(f"[DB] Database already exists: {db_name}")


# 🔥 ensure DB exists before creating engine
ensure_database_exists(settings.DATABASE_URL)
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def ensure_tables_exist():
    import models  # IMPORTANT: register models

    Base.metadata.create_all(bind=engine)
    print("[DB] Tables ensured")
