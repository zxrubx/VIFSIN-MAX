import time
from collections import defaultdict, deque

from maxapi import Dispatcher
from maxapi.types import MessageCreated, MessageCallback, Command, CallbackButton
from maxapi.context import MemoryContext
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from bot import config
from bot.db import create_report, get_report, CATEGORIES, STATUS_LABELS
from bot.notify import send_text

# user_id -> времена последних обращений (в RAM, как и FSM)
_recent: dict[int, deque] = defaultdict(deque)


def _rate_limited(user_id: int) -> bool:
    now = time.monotonic()
    q = _recent[user_id]
    while q and now - q[0] > 3600:
        q.popleft()
    return len(q) >= config.RATE_LIMIT_PER_HOUR


def _command_arg(event: MessageCreated) -> str:
    parts = (event.message.body.text or '').split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ''


def register(dp: Dispatcher) -> None:
    @dp.message_created(Command('report'))
    async def cmd_report(event: MessageCreated, context: MemoryContext):
        await context.clear()
        if _rate_limited(event.message.sender.user_id):
            await event.message.answer('Слишком много обращений за последний час. Попробуйте позже.')
            return
        builder = InlineKeyboardBuilder()
        for i, cat in enumerate(CATEGORIES):
            builder.row(CallbackButton(text=cat, payload=f'cat:{i}'))
        await event.message.answer(
            text='Выберите категорию обращения (отмена — /cancel, о данных — /privacy):',
            attachments=[builder.as_markup()],
        )

    @dp.message_callback()
    async def on_category_pick(event: MessageCallback, context: MemoryContext):
        payload = event.callback.payload or ''
        if not payload.startswith('cat:'):
            return
        try:
            idx = int(payload.split(':', 1)[1])
        except ValueError:
            return
        if not 0 <= idx < len(CATEGORIES):
            return
        category = CATEGORIES[idx]
        await context.update_data(category=category)
        await context.set_state('report_description')
        await event.answer(notification='Категория выбрана')
        await event.bot.send_message(
            chat_id=event.message.recipient.chat_id,
            text=f'Категория: {category}\n\nОпишите проблему подробно одним сообщением:',
        )

    @dp.message_created(Command('cancel'))
    async def cmd_cancel(event: MessageCreated, context: MemoryContext):
        await context.clear()
        await event.message.answer('Ввод отменён.')

    @dp.message_created(Command('status'))
    async def cmd_status(event: MessageCreated):
        report_id = _command_arg(event)
        if not report_id:
            await event.message.answer('Укажите ID обращения: /status A3F9B21C')
            return
        report = get_report(report_id)
        if not report:
            await event.message.answer('Обращение с таким ID не найдено.')
            return
        await event.message.answer(
            f'Обращение {report["id"]}\n'
            f'Категория: {report["category"]}\n'
            f'Статус: {STATUS_LABELS.get(report["status"], report["status"])}'
        )

    @dp.message_created(states=['report_description'])
    async def on_description(event: MessageCreated, context: MemoryContext):
        text = (event.message.body.text or '').strip()
        if not text:
            await event.message.answer('Нужен текст. Опишите проблему сообщением (или /cancel):')
            return
        if len(text) > config.MAX_DESCRIPTION_LEN:
            await event.message.answer(
                f'Слишком длинно ({len(text)} симв.). Сократите до {config.MAX_DESCRIPTION_LEN} и отправьте снова:'
            )
            return
        await context.update_data(description=text)
        await context.set_state('report_contact')
        await event.message.answer(
            'Контакт для связи (телефон, почта или ник). '
            'Отправьте "-" чтобы оставить обращение анонимным:'
        )

    @dp.message_created(states=['report_contact'])
    async def on_contact(event: MessageCreated, context: MemoryContext):
        raw = (event.message.body.text or '').strip()
        if len(raw) > config.MAX_CONTACT_LEN:
            await event.message.answer('Слишком длинный контакт. Отправьте короче или "-":')
            return
        contact = None if raw in ('-', '') else raw
        data = await context.get_data()
        if 'category' not in data or 'description' not in data:
            await context.clear()
            await event.message.answer('Данные обращения потеряны (бот перезапускался). Начните заново: /report')
            return

        sender_id = event.message.sender.user_id
        # анонимное обращение не связываем с аккаунтом вообще
        report_id = create_report(
            user_id=None if contact is None else sender_id,
            category=data['category'],
            description=data['description'],
            contact_info=contact,
        )
        _recent[sender_id].append(time.monotonic())
        await context.clear()

        tail = (
            'Обращение анонимное. Сохраните ID — по нему можно узнать статус: /status ' + report_id
            if contact is None else
            'Когда статус изменится, я напишу вам сюда. Узнать его можно и командой /status.'
        )
        await event.message.answer(f'Обращение принято.\nID: {report_id}\n\n{tail}')

        for staff_id in config.NOTIFY_USER_IDS:
            await send_text(
                staff_id,
                f'Новое обращение {report_id}\nКатегория: {data["category"]}',
                bot=event.bot,
            )
