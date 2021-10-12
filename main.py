from bot import Main
from dotenv import load_dotenv
from util import get_logger
import os

logger = get_logger('Bot')


def get_config():
    load_dotenv()
    return dict(token=os.getenv('DEVELOP_TOKEN'))


if __name__ == '__main__':
    mybot = Main(get_config(), logger)
    mybot.run()
