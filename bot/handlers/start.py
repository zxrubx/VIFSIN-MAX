from maxapi import Dispatcher
from maxapi.types import BotStarted, MessageCreated, Command


def register(dp: Dispatcher):
    @dp.bot_started()
    async def on_start(event: BotStarted):
        await event.bot.send_message(chat_id=event.chat_id, text='Привет! Я бот института.')

    @dp.message_created(Command('start'))
    async def cmd_start(event: MessageCreated):
        await event.message.answer('Привет! Я бот института.')

    @dp.message_created(Command('help'))
    async def cmd_help(event: MessageCreated):
        await event.message.answer('Доступные команды:\n/start — начать\n/help — помощь')
