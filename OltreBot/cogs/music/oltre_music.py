import re
import ytm
from discord.ext import commands
from discord.ext.commands import Cog, Context
from .base_music import BaseMusic
from typing import Union, Dict, List
from .embed import MusicEmbed
from OltreBot.util.colors import *
import lavalink

YTM = ytm.YouTubeMusic()

url_rx = re.compile(r'https?://(?:www\.)?.+')


class OltreMusic(BaseMusic):
    queue_msg_id: Union[Dict, None] = None

    # On Ready
    @Cog.listener()
    async def on_ready(self):
        # Call BaseMusic read function
        await super().on_ready()

        if not hasattr(self.bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            self.bot.lavalink = lavalink.Client(self.bot.user.id)
            # Host, Port, Password, Region, Name
            self.bot.lavalink.add_node('127.0.0.1', 2333, 'oltrebot-secret-password', 'eu', 'default-node')

        lavalink.add_event_hook(self.event_hook)

    def handle_play_search(self, author: Context.author, player: lavalink.DefaultPlayer, tracks: dict):
        """ Handle a search track """
        track = lavalink.models.AudioTrack(tracks[0], author, recommended=True)
        embed = MusicEmbed.search(self, author, track, self.end_measure('play'))
        player.add(requester=author.id, track=track)
        return embed, track

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        self.log_user_call_command(ctx.author, 'play', query)
        # Start timer
        self.start_measure('play')
        player = self.get_player(ctx.guild.id)
        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')
        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        results = await player.node.get_tracks(query)

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        try:
            message = ""
            tracks = []

            if not results or not results['tracks']:
                self.log.debug(f"(play) {red('Nothing Found')}")
                await ctx.send(embed=MusicEmbed.failed(self, ctx.author, "Nothing Found", self.end_measure('play')))

            elif results['loadType'] == 'NO_MATCHES':
                self.log.debug(f"(play) {red('NO_MATCHES')}")
                await ctx.send(embed=MusicEmbed.failed(self, ctx.author, "No Match found", self.end_measure('play')))

            elif results['loadType'] == 'LOAD_FAILED':
                self.log.debug(f"(play) {red('LOAD_FAILED')}")
                await ctx.send(embed=MusicEmbed.failed(self, ctx.author, "Load failed", self.end_measure('play')))

            elif results['loadType'] == 'SEARCH_RESULT':
                self.log.debug(f"(play) {green('SEARCH_RESULT')}")
                track = lavalink.models.AudioTrack(results['tracks'][0], ctx.author, recommended=True)
                tracks.append(track)
                message = f"Search result: {track.title}"

            elif results['loadType'] == 'PLAYLIST_LOADED':
                self.log.debug(f"(play) {green('PLAYLIST_LOADED')}")
                for idx, track in enumerate(results['tracks']):
                    # Add all the tracks from the playlist to the queue.
                    tracks.append(lavalink.models.AudioTrack(track, ctx.author, recommended=True))
                message = f'Playlist result ({len(tracks)}): {results["playlistInfo"]["name"]}'

            elif results['loadType'] == 'TRACK_LOADED':
                self.log.debug(f"(play) {green('TRACK_LOADED')}")
                track = lavalink.models.AudioTrack(results['tracks'][0], ctx.author, recommended=True)
                tracks.append(track)
                message = f"Track result: {track.title}"

            self.log.debug(f"Play message: {blue(message)}. Track len({len(tracks)})")
            # Add Tracks to Player
            for t in tracks:
                player.add(track=t, requester=ctx.author)

            # We don't want to call .play() if the player is playing as that will effectively skip
            # the current track.
            if not player.is_playing:
                await player.play()

            await self.update_queue_message_from_new_tracks(ctx.guild.id)

            embed = MusicEmbed.success(self, ctx.author, message, self.end_measure('play'))
            await ctx.send(embed=embed)

        except Exception as ex:
            self.log.error(f'<Exception> {ex}')
            await ctx.send(embed=MusicEmbed.failed(self, ctx.author, "Something Fail", self.end_measure('play')))

    @commands.command(aliases=['r'])
    async def radio(self, ctx: Context, *, query: str):
        """ Searches and plays a radio playlist from a given query. """
        self.log_user_call_command(ctx.author, 'radio', query)
        # Start timer
        self.start_measure('radio')
        # Retrieve final link
        try:
            songs = YTM.search_songs(query)
            song_id = songs['items'][0]['id']
            radio_id = songs['items'][0]['radio']['playlist_id']
            final_url = f"https://music.youtube.com/watch?v={song_id}&list={radio_id}"
            # Get Player
            await self.play(ctx, query=final_url)
        except Exception as e:
            self.log.error(f'<Exception> {e}')
            embed = MusicEmbed.failed(self, ctx.author, "Failed Radio", self.end_measure('radio'))
            await ctx.send(embed=embed)

    @commands.command(aliases=['c'])
    async def clear(self, ctx: Context):
        """ Clear queue Tracks """
        self.log_user_call_command(ctx.author, 'clear')
        self.start_measure('clear')
        if await self.safe_ready_proceed(ctx):
            player = self.get_player(ctx.guild.id)
            player.queue.clear()
            await ctx.send(embed=MusicEmbed.success(self, ctx.author, 'Clear', self.end_measure('clear')))

    @commands.command(alias=['skip', 'n'])
    async def next(self, ctx: Context):
        """ Next Track """
        self.log_user_call_command(ctx.author, 'next')
        self.start_measure('next')
        if await self.safe_ready_proceed(ctx):
            player = self.get_player(ctx.guild.id)
            await player.play()
            await ctx.send(embed=MusicEmbed.success(self, ctx.author, 'Next', self.end_measure('next')))

    @commands.command()
    async def pause(self, ctx: Context):
        """ Pause the player Track """
        self.log_user_call_command(ctx.author, 'pause')
        self.start_measure('pause')
        if await self.safe_ready_proceed(ctx):
            player = self.get_player(ctx.guild.id)
            await player.set_pause(pause=True)
            await ctx.send(embed=MusicEmbed.success(self, ctx.author, 'Pause', self.end_measure('pause')))

    @commands.command()
    async def resume(self, ctx: Context):
        """ Resume the player Track  """
        self.log_user_call_command(ctx.author, 'resume')
        self.start_measure('resume')
        if await self.safe_ready_proceed(ctx):
            player = self.get_player(ctx.guild.id)
            await player.set_pause(pause=False)
            await ctx.send(embed=MusicEmbed.success(self, ctx.author, 'Resume', self.end_measure('resume')))

    @commands.command(alias=['ca'])
    async def clean_all(self, ctx: Context):
        """ Remove all history log in oltre-music text channel """
        self.log_user_call_command(ctx.author, 'clean_all')
        # Purging channel
        await self.delete_all_message(ctx.channel)

    async def event_hook(self, event):
        if isinstance(event, lavalink.events.NodeConnectedEvent):
            self.log.debug(f"{magenta('<NodeConnectedEvent>')}")

        if isinstance(event, lavalink.events.NodeDisconnectedEvent):
            self.log.debug(f"{magenta('<NodeDisconnectedEvent>')}")

        if isinstance(event, lavalink.events.NodeChangedEvent):
            self.log.debug(f"{magenta('<NodeChangedEvent>')}")

        if isinstance(event, lavalink.events.QueueEndEvent):
            self.log.debug(f"{magenta('<QueueEndEvent>')}")
            # When this event_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            self.log.debug(f"Lavalink.Event QueueEndEvent")
            await self.update_queue_message_from_event(event)
            guild_id = int(event.player.guild_id)
            guild = self.bot.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)

        if isinstance(event, lavalink.events.TrackEndEvent):
            self.log.debug(f"{magenta('<TrackEndEvent>')}")

        if isinstance(event, lavalink.events.TrackStartEvent):
            self.log.debug(f"{magenta('<TrackStartEvent>')}")
            # Update OltreBot message
            await self.update_queue_message_from_event(event)

    async def update_queue_message_from_event(self, event):
        guild_id = event.player.guild_id
        queue: list = self.get_queue_tracks(guild_id)
        if event.player.current not in queue:
            queue.insert(0, event.player.current)
        await self.modify_oltrebot_message(guild_id, MusicEmbed.queue(self, queue))

    async def update_queue_message_from_new_tracks(self, guild_id: str):
        await self.modify_oltrebot_message(guild_id, MusicEmbed.queue(self, self.get_queue_tracks(guild_id)))
