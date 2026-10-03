import pytest

from bot import config, db


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'DB_PATH', str(tmp_path / 'test.db'))
    monkeypatch.setattr(config, 'ADMIN_PASSWORD', 'secret-pass')
    db.init_db()
