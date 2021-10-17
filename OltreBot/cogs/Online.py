from discord.ext.commands import Cog
from datetime import datetime
from discord import TextChannel
from colorama import Fore
from OltreBot.util import get_logger
from OltreBot.util.colors import *
from discord.ext import commands

LOGGER = get_logger('Online', sub_folder='cog')

BOT_URL = 'https://discord.com/api/oauth2/authorize?client_id=897532478485565480&permissions=8&scope=bot'


class Online(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = LOGGER

    # On Ready
    @Cog.listener()
    async def on_ready(self):
        self.log.info(f'Bot started {green(str(datetime.now()))}')
        self.log.info(f'Name: {green(self.bot.user.name)}')
        self.log.info(f'ID: {green(self.bot.user.id)}')
        for guild in self.bot.guilds:
            self.log.info(f"Connected to Guild: {blue(guild)} ")
            for channel in guild.channels:
                if isinstance(channel, TextChannel):
                    self.log.info(f'Writing to {blue(guild)}::{cyan(channel)}')
                    # await channel.send(f'Oltre Bot is back online 👽')

    @commands.command()
    async def url(self, ctx):
        """ Get bot url """
        await ctx.send(f'Use this link to add the bot on your server: {BOT_URL}')


