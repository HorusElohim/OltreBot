import re
import discord
import lavalink
from discord.ext import commands
from discord.ext.commands import Cog, Context
from OltreBot.util import get_logger
from OltreBot.util.colors import *
from .lavalink_voice_client import LavalinkVoiceClient
from .embed import MusicEmbed

LOGGER = get_logger('Music', sub_folder='cog')

url_rx = re.compile(r'https?://(?:www\.)?.+')


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = LOGGER

    # On Ready
    @Cog.listener()
    async def on_ready(self):

        if not hasattr(self.bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            self.bot.lavalink = lavalink.Client(self.bot.user.id)
            self.bot.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu',
                                       'default-node')  # Host, Port, Password, Region, Name

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voicechannel.

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
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

        # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise commands.CommandInvokeError('Join a voicechannel first.')

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
                await text_channel.send(f'No more tracks to play. Exiting bye bye ... ')
            await guild.voice_client.disconnect(force=True)

        if isinstance(event, lavalink.events.TrackEndEvent):
            self.log.debug(f"Lavalink.Event TrackEndEvent")
            player: lavalink.DefaultPlayer = event.player
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            for text_channel in guild.text_channels:
                await text_channel.send(f'Track: {event.track.title} terminated.')

        if isinstance(event, lavalink.events.TrackStartEvent):
            # When a new track start
            self.log.debug(f"Lavalink.Event TrackStartEvent")
            player: lavalink.DefaultPlayer = event.player
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            if player.current is not None:
                embed = self.get_track_embed(self.bot.user, player.current)
                for text_channel in guild.text_channels:
                    await text_channel.send(embed=embed)

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
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!')

        embed = discord.Embed(color=discord.Color.blurple())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results['loadType'] == 'SEARCH_RESULT':
            track = results['tracks'][0]
            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            embed.title = 'Search completed!'
            track = lavalink.models.AudioTrack(track, ctx.author, recommended=True)
            embed.description = f'Track: {track.title}'
            player.add(requester=ctx.author.id, track=track)

        if results['loadType'] == 'PLAYLIST_LOADED':
            description = []
            tracks = results['tracks']

            embed.title = 'Playlist Enqueued!'
            description.append(f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks')

            for idx, track in enumerate(tracks):
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=ctx.author, track=track)
                description.append(f'{idx}: {track["info"]["author"]} {track["info"]["title"]}')

            embed.description = '\n'.join(description)

        elif results['loadType'] == 'TRACK_LOADED':
            track = results['tracks'][0]
            embed.title = 'Track loaded!'
            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lavalink.models.AudioTrack(track, ctx.author, recommended=True)
            embed.description = f'Track: {track.title}'
            player.add(requester=ctx.author, track=track)

        elif results['loadType'] == 'NO_MATCHES':
            embed.title = f'No Match found'

        elif results['loadType'] == 'LOAD_FAILED':
            embed.title = f'Load failed.'

        await ctx.send(embed=embed)

        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()

    @commands.command()
    async def stop(self, ctx):
        """ Pause the player from the voice channel and clears its queue. """
        self.log_user_call_command(ctx, 'stop')

        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send("You're not in my voicechannel!")

        await player.stop()
        await ctx.send(' Player stopped')

    @commands.command()
    async def current(self, ctx):
        """ Get current Track info. """
        player = self.get_player(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send("You're not in my voicechannel!")

        if player.current:
            track = player.current
            embed = self.get_track_embed(ctx.author, track)
        else:
            embed = self.get_track_embed(ctx.author)

        await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx):
        """ Get current Track info. """
        player = self.get_player(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send("You're not in my voicechannel!")

        embed = discord.Embed()
        embed.title = 'Current Queue'
        desc = []
        for idx, track in enumerate(player.queue):
            desc.append(f'{idx}: {track.title}')
        embed.description = '\n'.join(desc)
            
        await ctx.send(embed=embed)

    @commands.command()
    async def clear(self, ctx):
        """ Clear queue Tracks """
        player = self.get_player(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send("You're not in my voicechannel!")

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

    @commands.command()
    async def pause(self, ctx):
        """ Pause the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send("You're not in my voicechannel!")

        await player.set_pause()
        await ctx.send('Track paused')

    @commands.command()
    async def next(self, ctx):
        """ Next Track """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send("You're not in my voicechannel!")

        await ctx.send('Next Track')
        await player.play()

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send('Not connected.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send("You're not in my voicechannel!")

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.voice_client.disconnect(force=True)
        await ctx.send('*⃣ | Disconnected.')
