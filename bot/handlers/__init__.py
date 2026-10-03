from maxapi import Dispatcher
from . import start, feedback, fallback


def include_routers(dp: Dispatcher) -> None:
    start.register(dp)
    feedback.register(dp)
    fallback.register(dp)  # всегда последним
