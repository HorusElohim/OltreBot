from discord.ext.commands import Cog
from datetime import datetime
from discord import TextChannel, Member, role
from colorama import Fore
from OltreBot.util import get_logger
from OltreBot.util.colors import *
from discord.ext import commands

LOGGER = get_logger('Online', sub_folder='cog')

BOT_URL = 'https://discord.com/api/oauth2/authorize?client_id=897532478485565480&permissions=8&scope=bot'

VERSION = "1.0"
STATUS = 'ONLINE'  # DEBUG


class Online(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = LOGGER

    # On Ready
    @Cog.listener()
    async def on_ready(self):
        """ Executed on cog ready """
        self.log.info(f'Bot started {green(str(datetime.now()))}')
        self.log.info(f'Name: {green(self.bot.user.name)}')
        self.log.info(f'ID: {green(self.bot.user.id)}')

        wake_msg = ""
        if STATUS == 'ONLINE':
            wake_msg = f'Oltre Bot is back online 👽 v{VERSION}'
        elif STATUS == 'DEBUG':
            wake_msg = f'Oltre Bot is in maintenance 🚧 v{VERSION}'

        await self.broadcast_message_guild(wake_msg)

    async def broadcast_message_guild(self, message: str):
        """ Broadcast a message to all the guilds """
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if isinstance(channel, TextChannel):
                    self.log.info(f'Writing to {blue(guild)}::{cyan(channel)} -> {message}')
                    await channel.send(f'{message}')
                    break

    @commands.command()
    async def url(self, ctx):
        """ Get bot url """
        await ctx.send(f'Use this link to add the bot on your server: {BOT_URL}')

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.log.info(f'Bot terminated {green(str(datetime.now()))}')
