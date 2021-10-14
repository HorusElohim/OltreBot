from pathlib import Path
from discord.ext import commands
from discord import Status

PREFIX = '.'
STATUS = Status.do_not_disturb


class Main:
    def __init__(self, config, logger):
        self.log = logger
        self.log.debug(f"Started")
        self.config = config
        self.bot = commands.Bot(command_prefix=PREFIX, status=STATUS)
        self.path = Path("./").absolute()
        self.extensions_path = self.path / "cogs"
        self.load_extensions()

    def load_extensions(self):
        self.log.debug("Loading Extensions")
        self.log.debug(f"Path:{self.path}")
        if self.extensions_path.exists():
            for file in self.extensions_path.iterdir():
                filename = file.name
                if filename.endswith('.py'):
                    self.log.info(f'Loading extension: {filename}.')
                    self.bot.load_extension(f'cogs.{filename[:-3]}')
            self.log.info("Extensions Loaded.")
        else:
            self.log.error("No Cogs Extensions folder")
        self.log.debug("Extensions all loaded")

    def run(self):
        try:
            self.bot.run(self.config['token'])
        except Exception as e:
            self.log.error(e)
