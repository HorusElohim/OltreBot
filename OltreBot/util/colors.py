from colorama import init, Fore, Back, Style

init(autoreset=True)


def color(text, c=Fore.RESET, b=Back.RESET):
    return f'{b}{c}{text}{Style.RESET_ALL}'


def green(text, light=False, b=Back.RESET):
    if light:
        return color(text, c=Fore.GREEN, b=b)
    else:
        return color(text, c=Fore.LIGHTGREEN_EX, b=b)


def cyan(text, light=False, b=Back.RESET):
    if light:
        return color(text, c=Fore.CYAN, b=b)
    else:
        return color(text, c=Fore.LIGHTCYAN_EX, b=b)


def blue(text, light=False, b=Back.RESET):
    if light:
        return color(text, c=Fore.BLUE, b=b)
    else:
        return color(text, c=Fore.LIGHTBLUE_EX, b=b)


def red(text, light=False, b=Back.RESET):
    if light:
        return color(text, c=Fore.RED, b=b)
    else:
        return color(text, c=Fore.LIGHTRED_EX, b=b)


def yellow(text, light=False, b=Back.RESET):
    if light:
        return color(text, c=Fore.YELLOW, b=b)
    else:
        return color(text, c=Fore.LIGHTYELLOW_EX, b=b)


def white(text, light=False, b=Back.RESET):
    if light:
        return color(text, c=Fore.WHITE, b=b)
    else:
        return color(text, c=Fore.LIGHTWHITE_EX, b=b)


def magenta(text, light=False, b=Back.RESET):
    if light:
        return color(text, c=Fore.MAGENTA, b=b)
    else:
        return color(text, c=Fore.LIGHTMAGENTA_EX, b=b)


def black(text, light=False, b=Back.RESET):
    if light:
        return color(text, c=Fore.BLACK, b=b)
    else:
        return color(text, c=Fore.LIGHTBLACK_EX, b=b)
