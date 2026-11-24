
"""SQLite connection (SQLAlchemy)."""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core import config
from db.tables import Base


engine = create_engine(
    f"sqlite:///{config.DB_PATH.as_posix()}",
    connect_args={
        "check_same_thread": False
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


def init_db() -> None:
    """Create tables and migrate the existing database."""

    Base.metadata.create_all(engine)

    with engine.begin() as conn:

        columns = {
            row[1]
            for row in conn.exec_driver_sql(
                "PRAGMA table_info(documents)"
            )
        }

        if "owner_id" not in columns:

            conn.exec_driver_sql(
                "ALTER TABLE documents "
                "ADD COLUMN owner_id INTEGER "
                "REFERENCES students(id)"
            )

        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS "
            "ix_documents_owner_id "
            "ON documents(owner_id)"
        )


@contextmanager
def get_session():

    session = SessionLocal()

    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
