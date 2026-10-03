# Bot MAX Institute — сбор обратной связи

## Что это
Бот в мессенджере MAX для приёма обращений студентов: жалобы, вопросы, конфликты. Хранит обращения в SQLite. Админ-панель на FastAPI для модерации.

## Стек
- `maxapi` — клиент MAX Bot API (polling)
- `sqlite3` — хранение обращений (без ORM, минимум зависимостей)
- `fastapi` + `uvicorn` — админ-панель с HTTP Basic Auth
- `python-dotenv` — конфиг через `.env`

## Структура

```
bot/
├── main.py              # точка входа, polling
├── config.py            # читает .env (BOT_TOKEN, DB_PATH, ADMIN_*)
├── db.py                # SQLite: init_db, create_report, get_report, list_reports, count_by_status, update_status
├── notify.py            # send_text — личные сообщения (уведомления об изменении статуса)
└── handlers/
    ├── start.py         # /start, /help, /privacy
    ├── feedback.py      # /report (FSM), /status ID, /cancel, лимит в час
    └── fallback.py      # ответ на непонятные сообщения (регистрируется ПОСЛЕДНИМ)

admin/
└── app.py               # FastAPI: список обращений, фильтр по статусу, действия

data/                    # SQLite БД (создаётся автоматически, в .gitignore)
```

## Модель данных

Таблица `reports`:

| Поле | Тип | Описание |
|---|---|---|
| `id` | TEXT PK | 8-символьный hex (например `A3F9B21C`) |
| `user_id` | INTEGER NULL | MAX user_id автора; **NULL для анонимных** (контакт `-`) — они не хранятся и не получают уведомлений |
| `category` | TEXT | одна из 5 категорий (см. `db.CATEGORIES`) |
| `description` | TEXT | текст обращения |
| `contact_info` | TEXT NULL | контакт или NULL (анонимно) |
| `status` | TEXT | `pending` / `approved` / `rejected` / `resolved` |
| `created_at` | TEXT | ISO timestamp |
| `reviewed_at` | TEXT NULL | время последней смены статуса |

Категории заданы списком в `bot/db.py:CATEGORIES`. Статусы — `bot/db.py:STATUSES`.

## Поток сбора обратной связи

`/report` → inline-кнопки с категориями → `MemoryContext` ставит state `report_description` → пользователь шлёт текст → state `report_contact` → пользователь шлёт контакт или `-` → запись в БД, ID возвращается пользователю.

`/cancel` сбрасывает состояние на любом шаге. `/status ID` — статус по ID. При смене статуса в админке автору с `user_id` уходит личное сообщение (admin вызывает `bot.notify.send_text`).

## Запуск

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # вставить BOT_TOKEN и ADMIN_PASSWORD

# бот (polling)
python -m bot.main

# админка (отдельный процесс)
uvicorn admin.app:app --host 127.0.0.1 --port 8000
# открыть http://127.0.0.1:8000  (логин admin, пароль из ADMIN_PASSWORD)

pytest                     # тесты (БД подменяется на временную)
```

Python 3.10+ (maxapi). Админка не стартует со слабым `ADMIN_PASSWORD`.

## Аутентификация и URL MAX API

- **Base URL:** `https://botapi.max.ru`
- Токен берётся через `@MasterBot` в MAX, кладётся в `.env` (`BOT_TOKEN`)
- Все запросы автоматически дополняются `?access_token=<token>`

## Ключевые паттерны maxapi

### Шаблон handler-а
```python
@dp.message_created(Command('report'))
async def cmd_report(event: MessageCreated, context: MemoryContext):
    await context.set_state('report_description')
    await event.message.answer('Опишите проблему:')
```

### Inline-кнопки и callback
```python
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton

builder = InlineKeyboardBuilder()
builder.row(CallbackButton(text='Категория', payload='cat:0'))
await event.message.answer(text='Выберите:', attachments=[builder.as_markup()])

@dp.message_callback()
async def on_cb(event: MessageCallback):
    await event.answer(notification='Принято')
```

Payload формат: `f"{key}:{value}"` (например `"cat:3"`).

### FSM (MemoryContext)
```python
@dp.message_created(states=['report_description'])
async def step(event: MessageCreated, context: MemoryContext):
    text = event.message.body.text
    await context.update_data(description=text)
    await context.set_state('report_contact')
```

`MemoryContext` живёт в RAM. Идентифицируется парой `(chat_id, user_id)`. При рестарте теряется — для production стоит подключить Redis-backed state.

## Типы данных
- `message_id` (`mid`) — **str**
- `chat_id`, `user_id` — **int**
- `timestamp` — unix-time в миллисекундах

## Важные нюансы
- Polling и вебхуки несовместимы — `bot.delete_webhook()` вызывается перед `start_polling`
- В админке используется HTTP Basic Auth (один пользователь `admin` + пароль из env). Для multi-user — добавить полноценные сессии
- Бота в MAX может создать только самозанятый/ИП/юрлицо РФ, физлицо нельзя (см. README)
- БД-файл создаётся в `data/reports.db` при первом запуске
- `RequestGeoLocationButton` и кнопка типа `chat` нестабильны на стороне MAX API
