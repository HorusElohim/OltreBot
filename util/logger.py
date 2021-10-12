import logging
import sys

from logging.handlers import TimedRotatingFileHandler
from .path import get_home_path, Path, mkdir

FORMATTER = logging.Formatter("'[%(asctime)s]-%(process)d-%(levelname).4s %(message)s")


def _logger_get_console_handler(level: int = logging.DEBUG):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    console_handler.setLevel(level)
    return console_handler


def _logger_get_file_handler(logger_path, level: int = logging.DEBUG):
    file_handler = logging.handlers.TimedRotatingFileHandler(logger_path, when='midnight')
    file_handler.setFormatter(FORMATTER)
    file_handler.setLevel(level)
    return file_handler


def get_logger(logger_name, path: Path = get_home_path(), console_level: int = logging.DEBUG,
               file_level: int = logging.DEBUG):
    # Get the logger if already exist or a new one
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # better to have too much log than not enough
        logger.addHandler(_logger_get_console_handler(console_level))

    log_path = path / 'logs' / f"{logger_name}.log"
    mkdir(log_path.parent)
    logger.addHandler(_logger_get_file_handler(log_path, file_level))
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    logger.debug(f"Logger enabled. File -> {log_path}")
    return logger
