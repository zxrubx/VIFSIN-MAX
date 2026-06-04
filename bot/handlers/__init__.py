from maxapi import Dispatcher
from . import start, feedback


def include_routers(dp: Dispatcher) -> None:
    start.register(dp)
    feedback.register(dp)
