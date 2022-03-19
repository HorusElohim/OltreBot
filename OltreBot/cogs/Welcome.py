from discord.ext.commands import Cog
from datetime import datetime
from .Base import BaseCog


class Welcome(BaseCog):

    @Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        guild = member.guild
        if channel is not None:
            msg = f'{datetime.now()}: Welcome {member.mention} to the server'
            await self.send_channel_msg(msg, self.color.BLUE)
