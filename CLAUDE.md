# Bot MAX Institute — Project Context

## О проекте
Бот для мессенджера MAX (max.ru). Написан на Python с использованием библиотеки `maxapi`.

## Установка

```bash
pip install maxapi
# с поддержкой вебхуков:
pip install maxapi[webhook]
```

## Аутентификация и базовый URL

- **Base URL:** `https://botapi.max.ru`
- **Токен** получается через `@MasterBot` в мессенджере MAX
- Токен передаётся один раз при создании `Bot('token')` и автоматически добавляется ко всем запросам как `?access_token=<token>`
- Токен хранить в `.env` файле, не коммитить

## Структура проекта

```
bot/        # основной код бота
config/     # конфигурация
tests/      # тесты
```

## Шаблон бота (polling)

```python
import asyncio
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, MessageCreated, Command

bot = Bot('your_token')
dp = Dispatcher()

@dp.bot_started()
async def on_start(event: BotStarted):
    await event.bot.send_message(chat_id=event.chat_id, text='Привет!')

@dp.message_created(Command('start'))
async def cmd_start(event: MessageCreated):
    await event.message.answer('Запущен!')

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
```

## Ключевые типы событий (UpdateType)

| Тип | Описание |
|---|---|
| `MessageCreated` | Новое сообщение |
| `MessageEdited` | Редактирование сообщения |
| `MessageRemoved` | Удаление сообщения |
| `MessageCallback` | Нажатие inline-кнопки |
| `BotStarted` | Пользователь нажал Start |
| `BotStopped` | Пользователь остановил бота |
| `BotAdded` / `BotRemoved` | Бот добавлен/удалён из чата |
| `UserAdded` / `UserRemoved` | Пользователь добавлен/удалён |
| `ChatTitleChanged` | Изменён заголовок чата |

## Отправка сообщений

```python
# Полная версия
await bot.send_message(chat_id=123, text='Текст', parse_mode=ParseMode.MARKDOWN)

# Внутри обработчика (предпочтительно)
await event.message.answer('Ответ')        # в тот же чат
await event.message.reply('Цитата')        # с цитированием
await event.message.edit('Новый текст')
await event.message.delete()
await event.message.pin()
```

## Фильтры и команды

```python
from maxapi import F
from maxapi.types import Command, CommandStart

@dp.message_created(Command('help'))        # /help
@dp.message_created(CommandStart())         # /start
@dp.message_created(F.message.body.text == 'привет')
@dp.message_created(F.message.body.text.lower().contains('help'))
@dp.message_created(F.message.body.attachments)   # есть вложения
```

## Inline-клавиатуры и callback

```python
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton, LinkButton
from maxapi.enums import Intent

builder = InlineKeyboardBuilder()
builder.row(
    CallbackButton(text='Удалить', payload='delete:123', intent=Intent.NEGATIVE),
    LinkButton(text='Сайт', url='https://example.com'),
)
await event.message.answer(text='Выберите:', attachments=[builder.as_markup()])

# Обработка нажатия
@dp.message_callback()
async def on_callback(event: MessageCallback):
    record_id, action = event.callback.payload.split(':')
    await event.answer(notification='Готово!', new_text='Обновлено')
```

**Паттерн кодирования payload:** `f"{id}:{action}"` (например `"42:delete"`)

## FSM (состояния)

```python
from maxapi.context import MemoryContext

@dp.message_created(Command('create'))
async def ask(event: MessageCreated, context: MemoryContext):
    await context.set_state('waiting_input')
    await event.message.answer('Введите текст:')

@dp.message_created(states=['waiting_input'])
async def receive(event: MessageCreated, context: MemoryContext):
    text = event.message.body.text
    await context.clear()
    await event.message.answer(f'Получено: {text}')
```

`MemoryContext` — in-memory, не переживает рестарт. Идентифицируется по `(chat_id, user_id)`.

## Роутеры

```python
from maxapi import Router

router = Router(router_id='module_name')

@router.message_created(Command('help'))
async def help_cmd(event: MessageCreated):
    await event.message.answer('Помощь')

dp.include_routers(router)
```

## Вебхуки

```python
# Запуск вебхук-сервера (fastapi + uvicorn)
await dp.handle_webhook(bot=bot, host='0.0.0.0', port=8080)

# Перед стартом polling — удалить существующие вебхуки
await bot.delete_webhook()
await dp.start_polling(bot)
```

Разрешённые порты для вебхуков: **80, 8080, 443, 8443, 16384–32383**

## Загрузка медиафайлов

```python
from maxapi.types.input_media import InputMedia, InputMediaBuffer

attachment = InputMedia('/path/to/file.jpg')           # с диска
attachment = InputMediaBuffer(buffer=bytes, filename='photo.jpg')  # из байтов

await bot.send_message(chat_id=chat_id, text='Файл', attachments=[attachment])
```

После загрузки файла библиотека делает паузу 2 секунды (настраивается: `Bot(after_input_media_delay=2.0)`).

## Ключевые типы данных

- `message_id` (`mid`) — **строка (str)**
- `chat_id`, `user_id` — **целые числа (int)**
- `timestamp` — unix time в миллисекундах

## Важные нюансы

- Polling и вебхуки **несовместимы** одновременно
- `auto_requests=True` на `Bot` делает дополнительные API-запросы для обогащения `event.from_user` и `event.chat` — отключи если не нужно
- `RequestGeoLocationButton` и тип кнопки "chat" имеют проблемы на стороне MAX API
