from discord.ext.commands import Cog
from discord.ext import commands
from datetime import datetime

__version__ = '0.0.1'


class Initialization(Cog):
    def __init__(self, bot):
        self.bot = bot

    # Events
    @Cog.listener()
    async def on_ready(self):
        print(f'Bot started {datetime.now()}')
        print(f'Name: {self.bot.user.name}')
        print(f'ID: {self.bot.user.id}')
        guilds = await self.bot.fetch_guilds(limit=150).flatten()
        for guild in guilds:
            print(f"Connected to Guild: {guild} ")

    # Default Vesion Command
    @commands.command()
    async def Initialization_version(self, ctx):
        await ctx.send(f"[Initialization] - version: {__version__}")
        print(f'Bot started {datetime.now()}')


def setup(bot):
    bot.add_cog(Initialization(bot))
