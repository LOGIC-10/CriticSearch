# critic_search/search_adapter/adapter_usage_db.py
import calendar
from datetime import datetime
from pathlib import Path

from sqlmodel import SQLModel, create_engine

# 定义隐藏数据目录（相对路径）
HIDDEN_DATA_DIR = Path("critic_search/.data")
HIDDEN_DATA_DIR.mkdir(parents=True, exist_ok=True)  # 确保隐藏文件夹存在

# 定义数据库文件路径
DATABASE_PATH = HIDDEN_DATA_DIR / "adapter_usage.sqlite"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


engine = create_engine(DATABASE_URL)
# 用于标记是否已经初始化
_db_initialized = False


def initialize_db():
    """
    初始化数据库和表（只执行一次）
    """
    global _db_initialized
    if not _db_initialized:
        SQLModel.metadata.create_all(engine)  # 创建所有表
        _db_initialized = True
        print(f"Database initialized at {DATABASE_PATH}")


def get_end_of_month() -> datetime:
    """
    获取当前日期的当月最后一天
    """
    now = datetime.now()
    last_day = calendar.monthrange(now.year, now.month)[1]
    return datetime(now.year, now.month, last_day, 23, 59, 59)
