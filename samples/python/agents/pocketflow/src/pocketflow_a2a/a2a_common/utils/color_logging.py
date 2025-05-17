import logging

import colorama

from colorama import Fore, Style


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

colorama.init(autoreset=True)

COLOR_MAP = {
    'red': Fore.RED,
    'green': Fore.GREEN,
    'yellow': Fore.YELLOW,
    'blue': Fore.BLUE,
    'magenta': Fore.MAGENTA,
    'cyan': Fore.CYAN,
    'white': Fore.WHITE,
    'gray': Fore.LIGHTBLACK_EX,
    'bright_magenta': Fore.LIGHTMAGENTA_EX,
    'bold': Style.BRIGHT,
}


def colorize(color, text):
    color_code = COLOR_MAP.get(color, '')
    return f'{color_code}{text}{Style.RESET_ALL}'
