from maxapi import Dispatcher
from maxapi.types import BotStarted, MessageCreated, Command


WELCOME = (
    'Привет! Я бот для приёма обратной связи.\n\n'
    'Команды:\n'
    '/report — оставить обращение\n'
    '/cancel — отменить ввод\n'
    '/help — помощь'
)


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
