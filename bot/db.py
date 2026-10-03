import sqlite3
import secrets
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from bot import config

CATEGORIES = [
    'Бытовые условия',
    'Безопасность',
    'Конфликт/Буллинг',
    'Академические вопросы',
    'Коррупция',
]

STATUSES = ('pending', 'approved', 'rejected', 'resolved')

STATUS_LABELS = {
    'pending': 'Ожидает рассмотрения',
    'approved': 'Принято в работу',
    'rejected': 'Отклонено',
    'resolved': 'Решено',
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    # путь читаем из config на каждом вызове — так БД можно подменить в тестах
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        # WAL: бот пишет, админка читает — из разных процессов
        conn.execute('PRAGMA journal_mode=WAL')
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
        conn.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status, created_at)')


def create_report(user_id: Optional[int], category: str, description: str,
                  contact_info: Optional[str]) -> str:
    """user_id=None — полностью анонимное обращение (автор не хранится, уведомить его нельзя)."""
    with _connect() as conn:
        for _ in range(5):
            report_id = secrets.token_hex(4).upper()
            try:
                conn.execute(
                    'INSERT INTO reports (id, user_id, category, description, contact_info, created_at) '
                    'VALUES (?, ?, ?, ?, ?, ?)',
                    (report_id, user_id, category, description, contact_info, _now()),
                )
                return report_id
            except sqlite3.IntegrityError:
                continue  # коллизия id — крайне маловероятна, пробуем другой
    raise RuntimeError('не удалось сгенерировать уникальный id обращения')


def get_report(report_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute('SELECT * FROM reports WHERE id = ?', (report_id.strip().upper(),)).fetchone()
        return dict(row) if row else None


def list_reports(status: Optional[str] = None, limit: int = 500) -> list[dict]:
    with _connect() as conn:
        if status:
            cur = conn.execute(
                'SELECT * FROM reports WHERE status = ? ORDER BY created_at DESC LIMIT ?', (status, limit))
        else:
            cur = conn.execute('SELECT * FROM reports ORDER BY created_at DESC LIMIT ?', (limit,))
        return [dict(row) for row in cur.fetchall()]


def count_by_status() -> dict[str, int]:
    with _connect() as conn:
        rows = conn.execute('SELECT status, COUNT(*) AS n FROM reports GROUP BY status').fetchall()
    counts = {s: 0 for s in STATUSES}
    counts.update({r['status']: r['n'] for r in rows})
    return counts


def update_status(report_id: str, status: str) -> bool:
    if status not in STATUSES:
        return False
    with _connect() as conn:
        cur = conn.execute(
            'UPDATE reports SET status = ?, reviewed_at = ? WHERE id = ?',
            (status, _now(), report_id),
        )
        return cur.rowcount > 0
