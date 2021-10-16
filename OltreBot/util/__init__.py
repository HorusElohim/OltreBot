from .perf import perf
from . import size
from .logger import get_logger
from colorama import init, Fore, Back

init(autoreset=True)


def color(text, c=Fore.RESET, b=Back.RESET):
    return f'{b}{c}{text}'
