from maxapi import Dispatcher
from maxapi.types import MessageCreated, MessageCallback, Command, CallbackButton
from maxapi.context import MemoryContext
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from bot.db import create_report, CATEGORIES


def register(dp: Dispatcher) -> None:
    @dp.message_created(Command('report'))
    async def cmd_report(event: MessageCreated, context: MemoryContext):
        await context.clear()
        builder = InlineKeyboardBuilder()
        for i, cat in enumerate(CATEGORIES):
            builder.row(CallbackButton(text=cat, payload=f'cat:{i}'))
        await event.message.answer(
            text='Выберите категорию обращения:',
            attachments=[builder.as_markup()],
        )

    @dp.message_callback()
    async def on_category_pick(event: MessageCallback, context: MemoryContext):
        payload = event.callback.payload or ''
        if not payload.startswith('cat:'):
            return
        idx = int(payload.split(':', 1)[1])
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

    @dp.message_created(states=['report_description'])
    async def on_description(event: MessageCreated, context: MemoryContext):
        text = (event.message.body.text or '').strip()
        if not text:
            await event.message.answer('Описание не должно быть пустым. Попробуйте ещё раз:')
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
        contact = None if raw in ('-', '') else raw
        data = await context.get_data()
        report_id = create_report(
            user_id=event.message.sender.user_id,
            category=data['category'],
            description=data['description'],
            contact_info=contact,
        )
        await context.clear()
        await event.message.answer(
            f'Обращение принято.\n'
            f'ID: {report_id}\n\n'
            f'Спасибо за обратную связь.'
        )
