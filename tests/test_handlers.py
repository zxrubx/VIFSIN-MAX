import asyncio
from types import SimpleNamespace

import pytest

from bot import config, db
from bot.handlers import feedback, include_routers


class FakeDP:
    """Собирает обработчики, чтобы вызывать их напрямую."""
    def __init__(self):
        self.handlers = {}

    def _reg(self, kind):
        def deco(*filters, **kw):
            def wrap(fn):
                self.handlers[fn.__name__] = fn
                return fn
            return wrap
        return deco

    def __getattr__(self, name):
        return self._reg(name)


class Ctx:
    def __init__(self):
        self.state, self.data = None, {}

    async def clear(self): self.state, self.data = None, {}
    async def set_state(self, s): self.state = s
    async def update_data(self, **kw): self.data.update(kw)
    async def get_data(self): return dict(self.data)


class Bot:
    def __init__(self): self.sent = []
    async def send_message(self, **kw): self.sent.append(kw)


def msg(text, user_id=10, bot=None):
    replies = []

    async def answer(text=None, **kw): replies.append(text)

    m = SimpleNamespace(body=SimpleNamespace(text=text), sender=SimpleNamespace(user_id=user_id), answer=answer)
    return SimpleNamespace(message=m, bot=bot or Bot()), replies


@pytest.fixture
def h(monkeypatch):
    feedback._recent.clear()
    monkeypatch.setattr(config, 'NOTIFY_USER_IDS', [999])
    dp = FakeDP()
    include_routers(dp)
    return dp.handlers


def run(coro):
    return asyncio.run(coro)


def fill(h, ctx, contact, user_id=10, bot=None):
    ctx.data.update(category='Безопасность')
    ctx.state = 'report_description'
    run(h['on_description'](msg('Текст жалобы', user_id)[0], ctx))
    assert ctx.state == 'report_contact'
    ev, replies = msg(contact, user_id, bot)
    run(h['on_contact'](ev, ctx))
    return replies[0]


def test_named_report_flow_and_staff_notification(h):
    ctx, bot = Ctx(), Bot()
    reply = fill(h, ctx, '@student', bot=bot)
    r = db.list_reports()[0]
    assert r['user_id'] == 10 and r['contact_info'] == '@student' and r['id'] in reply
    assert ctx.state is None
    assert bot.sent and bot.sent[0]['user_id'] == 999 and r['id'] in bot.sent[0]['text']


def test_anonymous_report_stores_no_user(h):
    fill(h, Ctx(), '-')
    r = db.list_reports()[0]
    assert r['user_id'] is None and r['contact_info'] is None


def test_validation_and_lost_state(h):
    ctx = Ctx()
    ev, replies = msg('x' * (config.MAX_DESCRIPTION_LEN + 1))
    ctx.state = 'report_description'
    run(h['on_description'](ev, ctx))
    assert ctx.state == 'report_description' and 'длинно' in replies[0]
    ev, replies = msg('-')
    run(h['on_contact'](ev, Ctx()))  # состояние потеряно после рестарта
    assert 'заново' in replies[0] and not db.list_reports()


def test_status_command(h):
    rid = db.create_report(None, 'Коррупция', 'd', None)
    ev, replies = msg(f'/status {rid.lower()}')
    run(h['cmd_status'](ev))
    assert 'Ожидает' in replies[0] and 'Коррупция' in replies[0]
    ev, replies = msg('/status ZZZZZZZZ')
    run(h['cmd_status'](ev))
    assert 'не найдено' in replies[0]
    ev, replies = msg('/status')
    run(h['cmd_status'](ev))
    assert 'Укажите' in replies[0]


def test_rate_limit(h, monkeypatch):
    monkeypatch.setattr(config, 'RATE_LIMIT_PER_HOUR', 2)
    for _ in range(2):
        fill(h, Ctx(), '-', user_id=7)
    ev, replies = msg('/report', user_id=7)
    run(h['cmd_report'](ev, Ctx()))
    assert 'Слишком много' in replies[0]
    ev, replies = msg('/report', user_id=8)  # другой пользователь не затронут
    run(h['cmd_report'](ev, Ctx()))
    assert 'категорию' in replies[0]
