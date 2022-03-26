import discord
from discord.ext.commands import Cog
from discord.ext import commands
from discord.ext.commands import Cog, Context
from discord import TextChannel, Message
from datetime import datetime
from OltreBot.util.colors import *
from OltreBot.util.discord_color import DiscordColorMsg as Dc
from enum import Enum
from typing import Dict
import time


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
        self.perf_measure: dict = {}

    def start_measure(self, name: str):
        self.perf_measure[name] = time.time_ns()

    def end_measure(self, name: str):
        if name in self.perf_measure:
            exec_ms = (time.time_ns() - self.perf_measure[name]) * float(1e-6)
            del self.perf_measure[name]
            return exec_ms
        else:
            return 0

    def log_user_call_command(self, author: Context.author, cmd_name: str, *args):
        self.log.info(f"{yellow(author.name)} -> <{magenta(cmd_name)}> : {cyan(' '.join(args))}")

    async def send_ctx_msg(self, ctx: Context, msg: str, c_level: ColorLevel = ColorLevel.WHITE) -> Message:
        console_msg, discord_msg = format_message_color(msg, c_level)
        self.log.debug(f'Send txt to user -> {yellow(ctx.author)}: {console_msg}')
        msg = await ctx.send(discord_msg)
        return msg

    async def send_channel_msg(self, channel: TextChannel, msg: str, c_level: ColorLevel = ColorLevel.WHITE) -> Message:
        console_msg, discord_msg = format_message_color(msg, c_level)
        self.log.debug(f'Send txt to channel -> {cyan(channel)}: {console_msg}')
        msg = await channel.send(discord_msg)
        return msg

    async def send_channel_embed(self, channel: TextChannel, embed: discord.Embed) -> Message:
        self.log.debug(f'To embed to channel -> {cyan(channel)}')
        msg = await channel.send(embed=embed)
        return msg

    async def modify_channel_msg_embed(self, channel: TextChannel, msg_id: int, embed: discord.Embed):
        self.log.debug(f'Modifying embed to channel -> {cyan(channel)}')
        msg = await self.get_message_with_id(channel, msg_id)
        await msg.edit(embed=embed)

    async def get_message_with_id(self, channel: TextChannel, msg_id: int) -> Message:
        return await self.bot.get_channel(channel.id).fetch_message(msg_id)

    async def broadcast_message_guild(self, message: str, c_level: ColorLevel = ColorLevel.WHITE):
        """ Broadcast a message to all the guilds """
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if isinstance(channel, TextChannel):
                    self.log.info(f'Broadcasting to {blue(guild)}::{cyan(channel)} -> {message}')
                    await self.send_channel_msg(channel, message, c_level=c_level)
                    break

    async def delete_all_message(self, channel: TextChannel):
        self.log.debug("delete_all_message")
        await channel.purge()
