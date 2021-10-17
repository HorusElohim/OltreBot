from discord.ext.commands import Cog
from discord.ext import commands
from datetime import datetime
from OltreBot.util import get_logger

LOGGER = get_logger('Welcome', sub_folder='cog')


class Welcome(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = LOGGER
        self._last_member = None

    @Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        guild = member.guild
        if channel is not None:
            await channel.send(f'{datetime.now()} Welcome {member.mention} to the server {guild}.')
            self.log.info(f'New member join in the server: {guild}++ -> {member.mention}')


