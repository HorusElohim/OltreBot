from pathlib import Path
from discord.ext import commands
from discord import Status
import OltreBot as ob

LOGGER = ob.util.get_logger('OltreBot')
PREFIX = '.'
STATUS = Status.online


class Bot:
    def __init__(self, token, cogs_path: Path = Path(ob.__path__[0]) / 'cogs'):
        self.log = LOGGER
        self.log.debug(f"Started")
        self.token = token
        self.bot = commands.Bot(command_prefix=PREFIX, status=STATUS)
        self.cogs_path = cogs_path
        self.load_cogs()

    def load_cogs(self):
        self.log.debug("Loading Cogs")
        if self.cogs_path.exists():
            self.bot.load_extension(f'OltreBot.cogs')
        else:
            self.log.error("No Cogs folder was found")
        self.log.debug("Loading cogs completed.")

    def run(self):
        try:
            self.bot.run(self.token)
        except Exception as e:
            self.log.error(e)
