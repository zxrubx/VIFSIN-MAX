from maxapi import Dispatcher
from maxapi.types import MessageCreated


def register(dp: Dispatcher) -> None:
    # регистрируется последним: срабатывает только если нет активного шага FSM
    # и сообщение не подошло ни под одну команду
    @dp.message_created(states=[None])
    async def on_unknown(event: MessageCreated):
        await event.message.answer('Не понял. Чтобы оставить обращение — /report, список команд — /help.')
