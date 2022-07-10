import re
import discord
import lavalink
from typing import Union, Dict
from discord.ext import commands
from discord.ext.commands import Cog, Context
from OltreBot.util import get_logger
from OltreBot.util.colors import *
from .lavalink_voice_client import LavalinkVoiceClient
from .embed import MusicEmbed
import time
# import ytm

# YTM = ytm.YouTubeMusic()

LOGGER = get_logger('Music', sub_folder='cog')

url_rx = re.compile(r'https?://(?:www\.)?.+')


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = LOGGER
        self.embed_id: Union[Dict, None] = None

    # On Ready
    @Cog.listener()
    async def on_ready(self):

        if not hasattr(self.bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            self.bot.lavalink = lavalink.Client(self.bot.user.id)
            # Host, Port, Password, Region, Name
            self.bot.lavalink.add_node('127.0.0.1', 2333, 'oltrebot-secret-password', 'eu', 'default-node')

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink.cleanup()

    async def send_msg(self, ctx: Context, msg: str):
        self.log.debug(f'For user: {ctx.author} -> {msg}')
        await ctx.send(msg)

    async def cog_before_invoke(self, ctx: Context):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voice channel.

        if ctx.author.id == 165927011280224257:
            raise commands.CommandInvokeError('Toxic people cannot use this bot!')

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            self.log.error(f"Error <{error}> asked by {yellow(ctx.author.name)}")
            await self.send_msg(ctx, error.original)
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voice channel" etc. You can modify the above
            # if you want to do things differently.

    def get_player(self, guild_id: str) -> lavalink.DefaultPlayer:
        return self.bot.lavalink.player_manager.get(guild_id)

    def log_user_call_command(self, ctx: Context, cmd_name: str, *args):
        self.log.info(f"Command: <{magenta(cmd_name)}| {cyan(' '.join(args))}> asked by {yellow(ctx.author.name)}")

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
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

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            self.log.debug(f"Lavalink.Event QueueEndEvent")
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            for text_channel in guild.text_channels:
                if text_channel.id in self.embed_id:
                    del self.embed_id[text_channel.id]

            await guild.voice_client.disconnect(force=True)

        if isinstance(event, lavalink.events.TrackEndEvent):
            self.log.debug(f"Lavalink.Event TrackEndEvent")

        if isinstance(event, lavalink.events.TrackStartEvent):
            # When a new track start
            self.log.debug(f"Lavalink.Event TrackStartEvent")
            player: lavalink.DefaultPlayer = event.player
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            if player.current is not None:
                embed = self.get_track_embed(self.bot.user, player.current)
                for text_channel in guild.text_channels:
                    await self.send_music_embed(embed, text_channel=text_channel)

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        # Get the player for this guild from cache.
        self.log_user_call_command(ctx, 'play', query)

        player = self.get_player(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        start_time = time.time_ns()
        results = await player.node.get_tracks(query)
        exec_stamp = (time.time_ns() - start_time) / int(1e6)
        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # AAlternatively, results['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results['tracks']:
            return await self.send_msg(ctx, 'Nothing found!')

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results['loadType'] == 'SEARCH_RESULT':
            track = results['tracks'][0]
            # You can attach additional information to audio tracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lavalink.models.AudioTrack(track, ctx.author, recommended=True)
            embed = MusicEmbed.search(self, ctx.author, track, exec_stamp)
            player.add(requester=ctx.author.id, track=track)

        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for idx, track in enumerate(tracks):
                # Add all the tracks from the playlist to the queue.
                player.add(requester=ctx.author, track=track)
            embed = MusicEmbed.playlist(self, ctx.author, results["playlistInfo"]["name"], tracks, exec_stamp)

        elif results['loadType'] == 'TRACK_LOADED':
            track = results['tracks'][0]
            track = lavalink.models.AudioTrack(track, ctx.author, recommended=True)
            embed = self.get_track_embed(ctx.author, track)
            player.add(requester=ctx.author, track=track)

        elif results['loadType'] == 'NO_MATCHES':
            embed = MusicEmbed.failed(self, ctx.author, "No Match found", exec_stamp)

        elif results['loadType'] == 'LOAD_FAILED':
            embed = MusicEmbed.failed(self, ctx.author, "Load failed", exec_stamp)

        await ctx.send(embed=embed)

        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()

    # @commands.command(aliases=['r'])
    # async def radio(self, ctx: Context, *, query: str):
    #     # Logs
    #     self.log_user_call_command(ctx, 'radio', query)
    #     start_time = time.time_ns()
    #     # Retrieve final link
    #     try:
    #         songs = YTM.search_songs(query)
    #         song_id = songs['items'][0]['id']
    #         radio_id = songs['items'][0]['radio']['playlist_id']
    #         final_url = f"https://music.youtube.com/watch?v={song_id}&list={radio_id}"
    #         # Get Player
    #         await self.play(ctx, query=final_url)
    #     except Exception as e:
    #         exec_stamp = (time.time_ns() - start_time) * int(1e-6)
    #         embed = MusicEmbed.failed(self, ctx.author, "Failed Radio", exec_stamp)
    #         await ctx.send(embed=embed)

    @commands.command()
    async def current(self, ctx: Context):
        """ Get current Track info. """
        player = self.get_player(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await self.send_msg(ctx, 'Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await self.send_msg(ctx, "You're not in my voice-channel!")

        if player.current:
            track = player.current
            embed = self.get_track_embed(ctx.author, track)
        else:
            embed = self.get_track_embed(ctx.author)

        await self.send_music_embed(embed, ctx=ctx)

    @commands.command(alias=['q'])
    async def queue(self, ctx: Context):
        """ Get current Track info. """
        player = self.get_player(ctx.guild.id)
        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await self.send_msg(ctx, 'Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await self.send_msg(ctx, "You're not in my voice channel!")

        embed = MusicEmbed.playlist(self, ctx.author, "Current Queue", player.queue, 0.0)

        await ctx.send(embed=embed)

    @commands.command()
    async def clear(self, ctx: Context):
        """ Clear queue Tracks """
        player = self.get_player(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await self.send_msg(ctx, 'Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await self.send_msg(ctx, "You're not in my voicechannel!")

        embed = discord.Embed()
        tracks = len(player.queue)
        embed.title = 'Queue cleared'
        embed.description = f'removed {tracks} tracks.'

        player.queue.clear()

        await ctx.send(embed=embed)

    def get_track_embed(self, author: discord.client, track: lavalink.AudioTrack = None) -> discord.Embed:
        if isinstance(track, lavalink.AudioTrack):
            return MusicEmbed.track(self, author, track)
        else:
            return MusicEmbed.empty(self, author)

    async def send_music_embed(self, embed: discord.Embed, ctx: Context = None,
                               text_channel: discord.TextChannel = None):
        if self.embed_id is None:
            self.embed_id = dict()

        if ctx:
            if ctx.channel.id not in self.embed_id:
                message = await ctx.send(embed=embed)
                self.embed_id[ctx.channel.id] = message.id
            else:
                message = await self.bot.get_channel(ctx.channel.id).fetch_message(self.embed_id[ctx.channel.id])
                if message:
                    await message.edit(embed=embed)

        elif text_channel:
            if text_channel.id not in self.embed_id:
                message = await text_channel.send(embed=embed)
                self.embed_id[text_channel.id] = message.id
            else:
                message = await self.bot.get_channel(text_channel.id).fetch_message(self.embed_id[text_channel.id])
                if message:
                    await message.edit(embed=embed)

    @commands.command()
    async def pause(self, ctx):
        """ Pause the player Track """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await self.send_msg(ctx, 'Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await self.send_msg(ctx, "You're not in my voice channel!")

        await player.set_pause(pause=True)
        await self.send_msg(ctx, 'Track paused')

    @commands.command()
    async def resume(self, ctx):
        """ Resume the player Track  """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await self.send_msg(ctx, 'Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await self.send_msg(ctx, "You're not in my voice channel!")

        await player.set_pause(pause=False)
        await self.send_msg(ctx, 'Track paused')

    @commands.command(alias=['skip', 'n'])
    async def next(self, ctx):
        """ Next Track """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await self.send_msg(ctx, 'Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await self.send_msg(ctx, "You're not in my voice channel!")
        await player.play()

    @commands.command(aliases=['stop'])
    async def disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await self.send_msg(ctx, 'Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await self.send_msg(ctx, "You're not in my voice channel!")

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.voice_client.disconnect(force=True)
        await self.send_msg(ctx, '**Disconnected**')
