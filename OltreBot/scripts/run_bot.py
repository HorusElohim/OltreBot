from pathlib import Path
from OltreBot.bot import Bot
from dotenv import load_dotenv
import os

# Load .env file containing the DS Token
load_dotenv(dotenv_path=Path.cwd() / '.env')
token = os.getenv('DEVELOP_TOKEN')
if token is None:
    print("No .env file containing DS token where found! Exiting...")
    exit(-1)


def main():
    bot = Bot(token=token)
    bot.run()


if __name__ == '__main__':
    main()
