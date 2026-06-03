from maxapi import Dispatcher
from . import start


def include_routers(dp: Dispatcher):
    start.register(dp)
