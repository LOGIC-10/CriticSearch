import sqlite3
import threading
import uuid
from pathlib import Path
import contextvars 

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
    Store notes for the current session.

    This function expects a JSON-formatted string representing a list of note entries,
    each in the following format:

        [
            "<note>First note content with <citation>original URL</citation> where data was used.</note>",
            "<note>Second note content with <citation>another URL</citation> example.</note>"
        ]

    The notes will be parsed, validated, and each entry saved under the current session.

    Args:
        note: A JSON string representing a list of <note>...</note> entries.

    Returns:
        dict: A result object with keys:
            status: 'ok' if saved successfully, otherwise 'error'.
            note_ids: List of generated note IDs when status is 'ok'.
            message: Detailed error message when status is 'error'.

    Raises:
        RuntimeError: If session_id is not set.
    """
    session_id = _current_session_id.get()
    if not session_id:
        raise RuntimeError("Session ID 未设置，无法存储笔记。")
    # Parse input string to list
    import json
    try:
        notes_list = json.loads(note)
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON format: {e}"}
    if not isinstance(notes_list, list):
        return {"status": "error", "message": "Input must be a JSON list of note strings."}

    saved_ids = []
    for idx, raw in enumerate(notes_list):
        if not isinstance(raw, str):
            return {"status": "error", "message": f"Element at index {idx} is not a string."}
        if not (raw.strip().startswith('<note>') and raw.strip().endswith('</note>')):
            return {"status": "error", "message": f"Invalid note format at index {idx}: must start with <note> and end with </note>."}
        # Save each note entry
        res = _taking_notes(session_id, raw)
        if res.get("status") == "ok":
            saved_ids.append(res.get("note_id"))
        else:
            return {"status": "error", "message": f"Failed to save note at index {idx}: {res}"}
    return {"status": "ok", "note_ids": saved_ids}

def retrieve_notes() -> str:
    """
    Retrieve all notes for the current session.

    Returns a single string concatenating all stored notes for this session,
    each separated by a newline. The string is intended for model consumption
    and retains original <note>...</note> formatting.

    Args:
        None

    Returns:
        str: All notes concatenated with '\n', or an empty string if none exist.

    Raises:
        RuntimeError: If session_id is not set.
    """
    session_id = _current_session_id.get()
    if not session_id:
        raise RuntimeError("Session ID 未设置，无法检索笔记。")
    return _retrieve_notes(session_id)
