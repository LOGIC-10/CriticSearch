import sqlite3
import threading
import uuid
from pathlib import Path
import contextvars  # 新增

_DB_PATH = Path(__file__).parent.parent.parent / 'notes.db'
# 确保数据库目录存在
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
# 并发锁
_lock = threading.Lock()

# 初始化数据库和表
with _lock:
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            note TEXT
        )
        '''
    )
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.commit()
    conn.close()

# 会话上下文存储 session_id
_current_session_id = contextvars.ContextVar('session_id', default=None)

def set_session(session_id: str):
    """设置当前会话的 session_id"""
    _current_session_id.set(session_id)

# 将原有函数重命名为私有实现
def _taking_notes(session_id: str, note: str) -> dict:
    """私有：在指定会话存储笔记"""
    note_id = str(uuid.uuid4())
    with _lock:
        conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        conn.execute(
            'INSERT INTO notes (id, session_id, note) VALUES (?, ?, ?)',
            (note_id, session_id, note)
        )
        conn.commit()
        conn.close()
    return {"status": "ok", "note_id": note_id}


def _retrieve_notes(session_id: str) -> str:
    """私有：获取指定会话所有笔记"""
    with _lock:
        conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        cursor = conn.execute(
            'SELECT note FROM notes WHERE session_id = ? ORDER BY timestamp',
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
    notes = [row[0] for row in rows]
    return "\n".join(notes)

# 面向模型暴露的工具接口，无需传入 session_id

def taking_notes(note: str) -> dict:
    """
    将笔记存储到当前会话数据库中，模型仅需传入 note 内容。
    """
    session_id = _current_session_id.get()
    if not session_id:
        raise RuntimeError("Session ID 未设置，无法存储笔记。")
    return _taking_notes(session_id, note)


def retrieve_notes() -> str:
    """
    获取当前会话所有笔记拼接字符串，模型无需传入 session_id。
    """
    session_id = _current_session_id.get()
    if not session_id:
        raise RuntimeError("Session ID 未设置，无法检索笔记。")
    return _retrieve_notes(session_id)
