import pytest
from fastapi.testclient import TestClient

from admin import app as admin_app
from bot import config, db

AUTH = ('admin', 'secret-pass')


@pytest.fixture
def client():
    return TestClient(admin_app.app, follow_redirects=False)


@pytest.fixture
def sent(monkeypatch):
    calls = []

    async def fake_send(user_id, text, bot=None):
        calls.append((user_id, text))
        return True

    monkeypatch.setattr(admin_app, 'send_text', fake_send)
    return calls


def test_requires_auth(client):
    assert client.get('/').status_code == 401
    assert client.get('/', auth=('admin', 'wrong')).status_code == 401
    assert client.get('/', auth=AUTH).status_code == 200


def test_weak_password_refuses_startup(monkeypatch):
    monkeypatch.setattr(config, 'ADMIN_PASSWORD', 'admin')
    with pytest.raises(RuntimeError):
        with TestClient(admin_app.app):
            pass


def test_xss_escaped(client):
    db.create_report(1, 'c', '<script>alert(1)</script>', '<b>x</b>')
    html = client.get('/', auth=AUTH).text
    assert '<script>alert' not in html and '&lt;script&gt;' in html


def test_bad_filter(client):
    assert client.get('/?status=nope', auth=AUTH).status_code == 400


def test_update_notifies_author(client, sent):
    rid = db.create_report(77, 'c', 'd', '@me')
    r = client.post(f'/update/{rid}/approved', auth=AUTH)
    assert r.status_code == 303
    assert db.get_report(rid)['status'] == 'approved'
    assert sent and sent[0][0] == 77 and rid in sent[0][1]
    client.post(f'/update/{rid}/approved', auth=AUTH)  # тот же статус — без повторного уведомления
    assert len(sent) == 1


def test_anonymous_not_notified(client, sent):
    rid = db.create_report(None, 'c', 'd', None)
    client.post(f'/update/{rid}/resolved', auth=AUTH)
    assert db.get_report(rid)['status'] == 'resolved' and not sent


def test_csrf_and_unknown(client, sent):
    rid = db.create_report(5, 'c', 'd', 'x')
    r = client.post(f'/update/{rid}/resolved', auth=AUTH, headers={'origin': 'http://evil.example'})
    assert r.status_code == 403 and db.get_report(rid)['status'] == 'pending'
    assert client.post('/update/NOPE0000/resolved', auth=AUTH).status_code == 404
    assert client.post(f'/update/{rid}/weird', auth=AUTH).status_code == 400
