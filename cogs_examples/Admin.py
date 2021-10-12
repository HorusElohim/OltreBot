from tdbm.logger import GetFileLogger
from discord.ext.commands import Cog
from discord.ext import commands

__version__ = '0.0.1'

class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Log = GetFileLogger('logs', __name__)

    @commands.command()
    async def load(self, ctx, extension):
        self.bot.load_extension(f'cogs.{extension}')
        await ctx.send(f"Extension: {extension} Loaded!")
        self.Log.debug(f"Load extension: {extension}")


    @commands.command()
    async def unload(self, ctx, extension):
        self.bot.unload_extension(f'cogs.{extension}')
        await ctx.send(f"Extension: {extension} Unloaded!")
        self.Log.debug(f"Unload extension: {extension}")


    @commands.command()
    async def reload(self, ctx, extension):
        self.bot.unload_extension(f'cogs.{extension}')
        self.bot.load_extension(f'cogs.{extension}')
        await ctx.send(f"Extension: {extension} Reloaded!")
        self.Log.debug(f"Reload extension: {extension}")

    # Default Vesion Command
    @commands.command()
    async def Admin_version(self, ctx):
        await ctx.send(f"[Admin] - version: {__version__}")
        self.Log.debug(f"Version: {__version__}")

def setup(bot):
    bot.add_cog(Admin(bot))
