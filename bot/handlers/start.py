from maxapi import Dispatcher
from maxapi.types import BotStarted, MessageCreated, Command

from bot.config import SUPPORT_CONTACT

WELCOME = (
    'Привет! Я бот для приёма обратной связи от студентов.\n\n'
    'Команды:\n'
    '/report — оставить обращение\n'
    '/status ID — узнать статус обращения\n'
    '/cancel — отменить ввод\n'
    '/privacy — как используются ваши данные\n'
    '/help — помощь'
)

PRIVACY = (
    'Как используются ваши данные\n\n'
    '• Обращение видят только сотрудники, которые его рассматривают.\n'
    '• Если вы оставите контакт, он будет доступен им для связи с вами, '
    'а статус обращения придёт вам сюда, в чат.\n'
    '• Если вместо контакта отправить "-", обращение анонимное: ваш аккаунт MAX '
    'не сохраняется, уведомлений о статусе не будет. Проверить статус можно '
    'командой /status с ID обращения — сохраните его.\n'
    '• Не указывайте в тексте лишние персональные данные (паспорт, адрес, телефоны третьих лиц).'
)


def privacy_text() -> str:
    return PRIVACY + (f'\n\nСвязь с администрацией: {SUPPORT_CONTACT}' if SUPPORT_CONTACT else '')


def register(dp: Dispatcher) -> None:
    @dp.bot_started()
    async def on_start(event: BotStarted):
        await event.bot.send_message(chat_id=event.chat_id, text=WELCOME)

    @dp.message_created(Command('start'))
    async def cmd_start(event: MessageCreated):
        await event.message.answer(WELCOME)

    @dp.message_created(Command('help'))
    async def cmd_help(event: MessageCreated):
        await event.message.answer(WELCOME)

    @dp.message_created(Command('privacy'))
    async def cmd_privacy(event: MessageCreated):
        await event.message.answer(privacy_text())
