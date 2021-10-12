from tdbm.logger import GetFileLogger
from discord.ext.commands import Cog
from discord.ext import commands
from datetime import datetime


__version__ = '0.0.1'


class Welcome(Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.Log = GetFileLogger('logs', __name__)

    @Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome {member.mention} to the best Warzone Tournament Bot for the moment {datetime.now()}.')
            self.Log.info(f'New menber join {member.mention}')

    @commands.command()
    async def hello(self, ctx, *args):
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send(f'Hi {member.name}')
            self.Log.info(f'Said hi to {member.mention}')
        else:
            await ctx.send(f'Hi again {member.name}!')
            self.Log.info(f'Said hi again to {member.mention}')
            self._last_member = member

def setup(bot):
    bot.add_cog(Welcome(bot))
