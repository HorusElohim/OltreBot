from discord.ext.commands import Cog
from discord.ext import commands
from discord.ext.commands import Cog, Context
from discord import TextChannel
from datetime import datetime
from OltreBot.util.colors import *
from OltreBot.util.discord_color import DiscordColorMsg as Dc
from enum import Enum


class ColorLevel(Enum):
    RED = 0
    L_GREEN = 1
    D_GREEN = 2
    ORANGE = 3
    YELLOW = 4
    BLUE = 5
    WHITE = 6


def format_message_color(msg: str, level: ColorLevel):
    console_msg = ""
    discord_msg = ""
    if level == ColorLevel.WHITE:
        console_msg = msg
        discord_msg = msg
    elif level == ColorLevel.RED:
        console_msg = red(msg)
        discord_msg = Dc.red(msg)
    elif level == ColorLevel.L_GREEN:
        console_msg = green(msg)
        discord_msg = Dc.light_green(msg)
    elif level == ColorLevel.D_GREEN:
        console_msg = green(msg)
        discord_msg = Dc.dark_green(msg)
    elif level == ColorLevel.ORANGE:
        console_msg = yellow(msg)
        discord_msg = Dc.orange(msg)
    elif level == ColorLevel.YELLOW:
        console_msg = yellow(msg)
        discord_msg = Dc.yellow(msg)
    elif level == ColorLevel.BLUE:
        console_msg = blue(msg)
        discord_msg = Dc.blue(msg)
    return console_msg, discord_msg


class BaseCog(Cog):

    def __init__(self, bot, logger):
        self.bot = bot
        self.log = logger
        self.color = ColorLevel

    async def send_ctx_msg(self, ctx: Context, msg: str, c_level: ColorLevel = ColorLevel.WHITE):
        console_msg, discord_msg = format_message_color(msg, c_level)
        self.log.debug(f'To user -> {yellow(ctx.author)}: {console_msg}')
        await ctx.send(discord_msg)

    async def send_channel_msg(self, channel: TextChannel, msg: str, c_level: ColorLevel = ColorLevel.WHITE):
        console_msg, discord_msg = format_message_color(msg, c_level)
        self.log.debug(f'To channel -> {cyan(channel)}: {console_msg}')
        await channel.send(discord_msg)

    async def broadcast_message_guild(self, message: str, c_level: ColorLevel = ColorLevel.WHITE):
        """ Broadcast a message to all the guilds """
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if isinstance(channel, TextChannel):
                    self.log.info(f'Broadcasting to {blue(guild)}::{cyan(channel)} -> {message}')
                    await self.send_channel_msg(channel, message, c_level=c_level)
                    break
