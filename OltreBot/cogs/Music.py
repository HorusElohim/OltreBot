import discord
from discord.ext.commands import Cog, Context
from discord.ext import commands, tasks
from youtube_search import YoutubeSearch
from discord import Embed, Colour
import asyncio
import youtube_dl
import pandas as pd
from colorama import Fore
from OltreBot.util import get_logger
from OltreBot.util.colors import *
from typing import Union

LOGGER = get_logger('Music', sub_folder='cog')

# To-DO
# Continue code refactoring and cleaning
# Playlist internal
# Auto-Disconnect when no more music


__version__ = '0.0.1'

# Discord Labels
Success = lambda x: f"**`SUCCESS`** {x}"
Error = lambda y: f"**`ERROR`** {y}"

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=1.0):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class YoutubeTrack:
    def __init__(self, logger, user_input):
        self.log = logger
        self.is_playlist = False
        self.error = False
        self.user_input = user_input
        self.url = self.extract_url()
        # Need search the user input and retrieve all info
        if self.url is None:
            self.log.debug(f"YoutubeTrack::{black('need_search first')}")
            db_info = self.get_youtube_dbinfo(self.user_input)
            self.id = db_info.id[0]
            self.url = f'https://www.youtube.com{db_info.url_suffix[0]}'
        # User input contain the id and no need to retrieve the url
        else:
            self.log.debug(f"YoutubeTrack::{black('contains youtube id')}")
            self.id = self.extract_id()
            db_info = self.get_youtube_dbinfo(self.id)

        self.title = db_info.title[0]
        self.views = db_info.views[0]
        self.pub_time = db_info.publish_time[0]
        self.thumbnail = db_info.thumbnails[0][0]
        self.duration = db_info.duration[0]

    def extract_url(self) -> Union[str, None]:
        if 'youtube' in self.user_input:
            if 'http' not in self.user_input:
                self.user_input = f'https://{self.user_input}'
            return self.user_input

        elif '/watch?v=' in self.user_input:
            return f'https://www.youtube.com{self.user_input}'
        else:
            return None

    def extract_id(self) -> str:
        # Retrieve ID
        id_track = self.url.split('watch?v=')[-1]
        # Check if is a playlist
        if '=' in id_track:
            id_track = id_track.split('=')[0]
            self.is_playlist = True
        return id_track

    def get_youtube_dbinfo(self, target) -> pd.DataFrame:
        search_info = []
        self.log.info(f'Searching on youtube: {black(target)}')
        try:
            search_info = pd.DataFrame(YoutubeSearch(target, max_results=1).to_dict())
        except Exception as e:
            self.log.error(f"Exception on search on youtube: {red(e)}")
            self.error = True
            return pd.DataFrame()
        self.log.info(f'Search completed with {black(len(search_info))} result')
        return search_info


class MusicEmbed:
    @staticmethod
    def youtube_search(self, author: discord.client, search_target: str, search_result: pd.DataFrame):
        self.log.info(f"Creating search embed for {search_target} asked by {yellow(author.name)}")
        embed = Embed(title=f'Search Results',
                      author=self.bot.user.name,
                      description='here the result from youtube. If you want to play a song use the url below',
                      colour=Colour(0x329FE8))
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        for index, row in search_result.iterrows():
            embed.add_field(name='________________________________', value=f'result {index + 1}\n', inline=False)
            embed.add_field(name='Title', value=row.title, inline=True)
            embed.add_field(name='Duration', value=row.duration, inline=True)
            embed.add_field(name='Url', value=row.url_suffix, inline=True)

        embed.set_footer(text=f'Requested by: {author.name}', icon_url=author.avatar_url)
        return embed

    @staticmethod
    def youtube_playing(self, author: discord.client, yt_track: YoutubeTrack):
        self.log.info(f"Creating now playing embed asked by {yellow(author.name)}")

        if yt_track.error:
            return Embed(title=f'Error on user input:  {yt_track.user_input}')

        embed = Embed(title=f'Now Playing {yt_track.title}',
                      author=self.bot.user.name,
                      url=yt_track.url,
                      colour=Colour(0xE11B1B))

        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_image(url=yt_track.thumbnail)
        embed.add_field(name='Duration', value=yt_track.duration, inline=True)
        embed.add_field(name='Views', value=yt_track.views, inline=True)
        embed.add_field(name='Publish Time', value=yt_track.pub_time, inline=True)
        embed.set_footer(text=f'Requested by: {author.name}', icon_url=author.avatar_url)
        return embed


class DSClient:
    def __init__(self, log, ctx: Context):
        self.log = log
        self.ctx = ctx
        self.inactive_counter = 0
        self.to_delete = False

    async def send(self, msg):
        await self.ctx.send(msg)

    def update_status(self):
        if not self.ctx.voice_client.is_playing():
            self.inactive_counter += 1
            self.log.info(f'DSClient<{cyan(self.get_id())}> is playing <{red("False")}> ({red(self.inactive_counter)})')

    async def manage_activity(self):
        if not self.to_delete:
            self.update_status()
            if self.inactive_counter > 2:
                self.log.info(f'DSClient<{cyan(self.get_id())}> automatic disconnection')
                await self.send("Oltre Bot is not playing anything for too long... Bye Bye")
                await self.ctx.voice_client.disconnect()
                self.to_delete = True

    def get_id(self):
        return self.ctx.voice_client.channel.id


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = LOGGER
        self.ds_clients: {str: DSClient} = {}
        self.manage_callback.start()
        self.log.info(f'manage_callback has started...')

    @Cog.listener()
    async def on_ready(self):
        self.log.info(f'Music logged in with bot: {self.bot.user}')

    def is_new_client(self, ds_id):
        return ds_id not in self.ds_clients

    def add_ds_client(self, ctx: Context):
        self.ds_clients.update({ctx.voice_client.channel.id: DSClient(self.log, ctx)})

    def manage_ds_client(self, ctx: Context):
        if self.is_new_client(ctx.voice_client.channel.id):
            self.add_ds_client(ctx)

    def remove_ds_client(self, ds_id):
        del self.ds_clients[ds_id]

    @tasks.loop(seconds=5)
    async def manage_callback(self):
        try:
            to_delete = []

            if len(self.ds_clients) > 0:
                for ds_id, ds_client in self.ds_clients.items():
                    # Manage activity of the DSClient - Disconnect if needed
                    await ds_client.manage_activity()
                    if ds_client.to_delete:
                        to_delete.append(ds_id)

                for id_delete in to_delete:
                    self.log.info(f'Removing id of channel: {red(id_delete)}')
                    self.remove_ds_client(id_delete)

        except Exception as e:
            self.log.info(f'Timer callback - Exception: {e}')

    @commands.command()
    async def join(self, ctx: Context, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def pause(self, ctx: Context, *args):
        """Plays the best match on youtube of what you search """
        member = ctx.author
        try:
            ctx.voice_client.pause()
        except Exception as e:
            await ctx.send(Error(f"Exception: {e}"))

    @commands.command()
    async def resume(self, ctx: Context, *args):
        """Plays the best match on youtube of what you search """
        member = ctx.author
        try:
            ctx.voice_client.resume()
        except Exception as e:
            await ctx.send(Error(f"Exception: {e}"))

    @commands.command()
    async def play(self, ctx: Context, *args):
        """Plays the best match on youtube of what you search """
        member = ctx.author
        user_input = " ".join(args)
        channel_id = ctx.voice_client.channel.id
        self.log.info(
            f"play request from user {yellow(member.name)}. Request<{green(user_input)}> Channel<{blue(channel_id)}>")

        try:
            async with ctx.typing():
                yt_track = YoutubeTrack(self.log, user_input)

            ctx.voice_client.play(await YTDLSource.from_url(yt_track.url, loop=self.bot.loop, stream=True),
                                  after=lambda e: self.log.info('Player error: %s' % e) if e else None)

            self.manage_ds_client(ctx)

            await ctx.send(embed=MusicEmbed.youtube_playing(self, member, yt_track))

        except Exception as e:
            await ctx.send(Error(f"Exception: {e}"))

    @commands.command()
    async def play_local(self, ctx: Context, *, query):
        """Plays a file from the local filesystem"""
        member = ctx.author
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: self.log.info('Player error: %s' % e) if e else None)

        await ctx.send(f'Now playing: {query}. Chosen by {member}')

    @commands.command()
    async def volume(self, ctx: Context, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))
        self.log.info("Changed volume to {}%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(bot):
    bot.add_cog(Music(bot))
