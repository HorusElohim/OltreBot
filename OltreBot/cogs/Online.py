from discord.ext.commands import Cog
from datetime import datetime
from OltreBot.util.colors import *
from discord.ext import commands
from .Base import BaseCog
from enum import Enum

BOT_URL = 'https://discord.com/api/oauth2/authorize?client_id=897532478485565480&permissions=8&scope=bot'

VERSION = "1.X"


class WakeupStatus(Enum):
    ONLINE = 0
    DEBUG = 1
    UPGRADE = 2


def wakeup_message(status: WakeupStatus = WakeupStatus.ONLINE):
    if status == WakeupStatus.ONLINE:
        return f'Oltre Bot is back online 👽 v{VERSION}'
    elif status == WakeupStatus.ONLINE:
        return f'Oltre Bot is in maintenance 🚧 v{VERSION}'
    elif status == WakeupStatus.UPGRADE:
        return f'Oltre Bot is currently upgrading 💻 v{VERSION}'


class Online(BaseCog):

    # On Ready
    @Cog.listener()
    async def on_ready(self):
        """ Executed on cog ready """
        self.log.info(f'Bot started {green(str(datetime.now()))}')
        self.log.info(f'Name: {green(self.bot.user.name)}')
        self.log.info(f'ID: {green(self.bot.user.id)}')

        # await self.broadcast_message_guild(wakeup_message(WakeupStatus.UPGRADE), c_level=self.color.BLUE)

    @commands.command()
    async def url(self, ctx):
        """ Get bot url """
        await ctx.send(f'Use this link to add the bot on your server: {BOT_URL}')

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.log.info(f'Bot terminated {green(str(datetime.now()))}')
