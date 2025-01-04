from pathlib import Path

from loguru import logger
from sqlalchemy import text
from sqlmodel import SQLModel, create_engine

HIDDEN_DATA_DIR = Path(".data")
HIDDEN_DATA_DIR.mkdir(parents=True, exist_ok=True)  # Ensure the hidden folder exists

# Define the database file path
DATABASE_PATH = HIDDEN_DATA_DIR / "search.sqlite"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create the engine
engine = create_engine(DATABASE_URL)


def recreate_db():
    """重新创建数据库表结构。如果表已存在则删除后重建。"""
    if DATABASE_PATH.exists():
        with engine.connect() as conn:
            # Drop `UniqueContent` and `HistoryQuery` tables if they exist
            conn.execute(text("DROP TABLE IF EXISTS uniquecontent"))
            conn.execute(text("DROP TABLE IF EXISTS historyquery"))
            conn.commit()
    else:
        logger.info(
            f"Database file does not exist at {DATABASE_PATH}. Initializing new database."
        )

    SQLModel.metadata.create_all(engine)
