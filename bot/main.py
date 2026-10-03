import asyncio
import logging

from maxapi import Bot, Dispatcher

from bot.config import BOT_TOKEN
from bot.db import init_db
from bot.handlers import include_routers


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    if not BOT_TOKEN:
        raise RuntimeError('BOT_TOKEN не задан в .env файле')
    init_db()
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    include_routers(dp)
    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
