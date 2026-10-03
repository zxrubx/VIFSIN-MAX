import logging

from maxapi import Bot

from bot.config import BOT_TOKEN
from bot.db import STATUS_LABELS

log = logging.getLogger(__name__)


async def send_text(user_id: int, text: str, bot: Bot | None = None) -> bool:
    """Отправить личное сообщение. Ошибки не пробрасываются — уведомление не критично."""
    own = bot is None
    if own:
        if not BOT_TOKEN:
            return False
        bot = Bot(BOT_TOKEN)
    try:
        await bot.send_message(user_id=user_id, text=text)
        return True
    except Exception:
        log.exception('не удалось отправить сообщение user_id=%s', user_id)
        return False
    finally:
        if own:
            await bot.close_session()


def status_changed_text(report_id: str, status: str) -> str:
    return f'Статус вашего обращения {report_id} изменён: {STATUS_LABELS.get(status, status)}.'
