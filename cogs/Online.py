from discord.ext.commands import Cog
from datetime import datetime
from discord import TextChannel
from util import get_logger

LOGGER = get_logger('Oltre.Online')


# Playlist internal
# Auto-Disconnect when no more music
# play if receive a url stream url else search and then play


class Online(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = LOGGER

    # On Ready
    @Cog.listener()
    async def on_ready(self):
        self.log.info(f'Bot started {datetime.now()}')
        self.log.info(f'Name: {self.bot.user.name}')
        self.log.info(f'ID: {self.bot.user.id}')
        for guild in self.bot.guilds:
            self.log.info(f"Connected to Guild: {guild} ")
            for channel in guild.channels:
                if isinstance(channel, TextChannel):
                    self.log.info(f'Writing to {guild}::{channel}')
                    # await channel.send(f'Oltre Bot is back online 👽')


def setup(bot):
    bot.add_cog(Online(bot))
