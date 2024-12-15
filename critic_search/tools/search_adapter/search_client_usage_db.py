from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from loguru import logger
from sqlmodel import SQLModel, create_engine

# Define the hidden data directory (relative path)
HIDDEN_DATA_DIR = Path("critic_search/.data")
HIDDEN_DATA_DIR.mkdir(parents=True, exist_ok=True)  # Ensure the hidden folder exists

# Define the database file path
DATABASE_PATH = HIDDEN_DATA_DIR / "search_client_usage.sqlite"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL)
# Flag to mark if the database has been initialized
_db_initialized = False


def initialize_db():
    """
    Initialize the database and tables (only executed once).
    """
    global _db_initialized
    if not _db_initialized:
        SQLModel.metadata.create_all(engine)  # Create all tables
        _db_initialized = True
        logger.info(f"Database initialized at {DATABASE_PATH}")


def get_second_day_naive() -> datetime:
    """
    Get the second day of the current month (naive datetime without timezone).

    Returns:
        naive datetime (without timezone).
    """
    now = datetime.now(ZoneInfo("America/New_York"))
    # Create a naive datetime object
    return datetime(now.year, now.month, 2, 0, 0, 0)


def get_current_time_of_new_york_naive() -> datetime:
    """
    Get the current time in New York and remove the timezone information.

    Returns:
        naive datetime (without timezone).
    """
    # Get the current time with timezone information
    aware_time = datetime.now(ZoneInfo("America/New_York"))
    # Remove the timezone information
    naive_time = aware_time.replace(tzinfo=None)
    return naive_time
