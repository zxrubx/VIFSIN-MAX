import sqlite3
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

from bot.config import DB_PATH

CATEGORIES = [
    'Бытовые условия',
    'Безопасность',
    'Конфликт/Буллинг',
    'Академические вопросы',
    'Коррупция',
]

STATUSES = ('pending', 'approved', 'rejected', 'resolved')


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                contact_info TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                reviewed_at TEXT
            )
        ''')


def create_report(user_id: int, category: str, description: str, contact_info: Optional[str]) -> str:
    report_id = secrets.token_hex(4).upper()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            'INSERT INTO reports (id, user_id, category, description, contact_info, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (report_id, user_id, category, description, contact_info, datetime.utcnow().isoformat()),
        )
    return report_id


def list_reports(status: Optional[str] = None) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if status:
            cur = conn.execute('SELECT * FROM reports WHERE status = ? ORDER BY created_at DESC', (status,))
        else:
            cur = conn.execute('SELECT * FROM reports ORDER BY created_at DESC')
        return [dict(row) for row in cur.fetchall()]


def update_status(report_id: str, status: str) -> bool:
    if status not in STATUSES:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            'UPDATE reports SET status = ?, reviewed_at = ? WHERE id = ?',
            (status, datetime.utcnow().isoformat(), report_id),
        )
        return cur.rowcount > 0
