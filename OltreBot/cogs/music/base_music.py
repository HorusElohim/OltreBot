import discord
import lavalink
from discord import Guild, TextChannel, Message
from discord.ext import commands
from discord.ext.commands import Cog, Context
from typing import Union, Dict, List
from OltreBot.util.colors import *
from .lavalink_voice_client import LavalinkVoiceClient
from lavalink import AudioTrack
from datetime import datetime
from dataclasses import dataclass
from ..Base import BaseCog
from .embed import MusicEmbed

MUSIC_CHANNEL = 'oltre-music'


@dataclass
class MessageRegister:
    guild: Guild
    channel: TextChannel
    message: Message

    def guild_id(self):
        return self.guild.id

    def channel_id(self):
        return self.channel.id

    def message_id(self):
        return self.message.id


# Create Text Channel
async def create_channel(guild: Guild, channel_name: str):
    return await guild.create_text_channel(channel_name)


# Get text channel if exist else return None
def get_text_channel(guild: Guild, channel_name: str) -> Union[TextChannel, None]:
    for channel in guild.channels:
        if isinstance(channel, TextChannel):
            if channel.name == channel_name:
                return channel
    return None


class BaseMusic(BaseCog):
    message_register_dict: dict = {}

    @Cog.listener()
    async def on_ready(self):
        """ Executed on cog ready """
        self.log.debug("on_ready")
        # Init message register dict
        await self.initialize_message_register()

    async def initialize_message_register(self):
        self.log.debug("initialize_message_register")
        # Iterate Guilds
        for guild in self.bot.guilds:
            # Check Oltre-Channel exist
            channel = get_text_channel(guild, MUSIC_CHANNEL)
            self.log.info(f'Recover channel {blue(guild)}::{cyan(channel)}')
            # Create Oltre-Channel
            if channel is None:
                self.log.info(f'Creating channel {blue(guild)}::{cyan(channel)}')
                channel = await create_channel(guild, MUSIC_CHANNEL)
            # Purging channel
            await self.delete_all_message(channel)
            # Send first message
            message = await self.send_channel_embed(channel, MusicEmbed.bot_started(self))
            self.log.info(f'Registering {blue(guild)}::{cyan(channel)}::{yellow(message.id)}')
            self.message_register_dict[guild.id] = MessageRegister(guild=guild, channel=channel, message=message)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink.cleanup()

    async def cog_before_invoke(self, ctx: Context):
        """ Command before-invoke handler. """
        self.log.debug(f"cog_before_invoke")
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            #  Ensure that the bot and command author share a mutual voice channel.
            await self.ensure_voice(ctx)

    async def cog_command_error(self, ctx: Context, error):
        if isinstance(error, commands.CommandInvokeError):
            self.log.error(f"Error <{error}> asked by {yellow(ctx.author.name)}")
            await self.send_ctx_msg(ctx, error.original, self.color.RED)
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voice channel" etc. You can modify the above
            # if you want to do things differently.

    def get_player(self, guild_id: str) -> lavalink.DefaultPlayer:
        try:
            return self.bot.lavalink.player_manager.get(guild_id)
        except lavalink.NodeError:
            self.log.error("Disconnect cmd with no player connected")

    def create_player(self, guild_id: str, guild_region: str):
        self.log.debug(f"create_player for guild: {guild_id}")
        try:
            return self.bot.lavalink.player_manager.create(guild_id, endpoint=guild_region)
        except lavalink.NodeError:
            self.log.error("Create Player with no player connected")

    def log_user_call_command(self, author: Context.author, cmd_name: str, *args):
        self.log.info(f"Command: <{magenta(cmd_name)}| {cyan(' '.join(args))}> asked by {yellow(author.name)}")

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        self.log.debug(f"ensure_voice for guild: {ctx.guild}")
        player = self.create_player(ctx.guild.id, str(ctx.guild.region))
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a voice channel (i.e. initiating playback).
        # Commands such as volume/skip etc. don't require the bot to be in a voice channel so don't need listing here.
        should_connect = ctx.command.name in ('play', 'radio')

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voice channel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise commands.CommandInvokeError('Join a voice channel first.')

        if player:
            if not player.is_connected:
                if not should_connect:
                    raise commands.CommandInvokeError('Not connected.')

                permissions = ctx.author.voice.channel.permissions_for(ctx.me)

                if not permissions.connect or not permissions.speak:  # Check user limit too?
                    raise commands.CommandInvokeError('I need the `CONNECT` and `SPEAK` permissions.')

                player.store('channel', ctx.channel.id)
                await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
            else:
                if int(player.channel_id) != ctx.author.voice.channel.id:
                    raise commands.CommandInvokeError('You need to be in my voicechannel.')
        else:
            raise commands.CommandInvokeError('The lavalink node is not running')

    @commands.command(aliases=['stop'])
    async def disconnect(self, ctx: Context):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.get_player(ctx.guild.id)

        if await self.safe_ready_proceed(ctx):
            # Clear the queue to ensure old tracks don't start playing
            # when someone else queues something.
            player.queue.clear()
            # Stop the current track so Lavalink consumes less resources.
            await player.stop()
            # Disconnect from the voice channel.
            await ctx.voice_client.disconnect(force=True)
            await self.send_ctx_msg(ctx, '**Disconnected**')

    def get_queue_tracks(self, guild_id: str) -> Union[None, List[AudioTrack]]:
        player = self.get_player(guild_id)
        if not player.is_connected:
            self.log.debug(f'get_queue_tracks. Player not connected!')
            return []

        return player.queue

    async def modify_oltrebot_message(self, guild_id: str, embed):
        await self.message_register_dict[guild_id].message.edit(embed=embed)

    async def safe_ready_proceed(self, ctx: Context):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.get_player(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            await self.send_ctx_msg(ctx, 'Not connected', self.color.YELLOW)
            return False

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            await self.send_ctx_msg(ctx, "You're not in my voice channel!", self.color.YELLOW)
            return False

        return True
