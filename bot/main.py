import asyncio
from maxapi import Bot, Dispatcher
from bot.config import BOT_TOKEN
from bot.handlers import include_routers


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    include_routers(dp)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
