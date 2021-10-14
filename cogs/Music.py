import discord
from discord.ext.commands import Cog
from discord.ext import commands
from youtube_search import YoutubeSearch
from tabulate import tabulate
from discord import Embed, Colour
import asyncio
import youtube_dl
import pandas as pd
from util import get_logger

LOGGER = get_logger('Oltre.Music')

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
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
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


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = LOGGER

    @Cog.listener()
    async def on_ready(self):
        self.log.info(f'Music logged in with bot: {self.bot.user}')

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    def search_on_youtube(self, music, res=1):
        search_info = []
        self.log.info(f'Search on youtube: {music}')
        search_info = pd.DataFrame(YoutubeSearch(music, max_results=res).to_dict())
        self.log.info(f'Search completed with {len(search_info)} result')
        return search_info

    def construct_search_embed(self, author: discord.client, search_target: str, search_result: pd.DataFrame):
        self.log.info(f"Creating search embed for {search_target} asked by {author.name}")
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

    def construct_now_playing_embed(self, author: discord.client, url: str):
        self.log.info(f"Creating now playing embed asked by {author.name}")

        id_track = url.split('watch?v=')[-1]
        self.log.info(f"Extracting id: {id_track}")

        search_result = self.search_on_youtube(id_track)
        if len(search_result) > 0:
            embed = Embed(title=f'Now Playing {search_result.title[0]}',
                          author=self.bot.user.name,
                          url=url,
                          colour=Colour(0xE11B1B))
            self.log.debug(f"Thumbnails: {search_result.thumbnails[0][0]}")
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            embed.set_image(url=search_result.thumbnails[0][0])
            embed.add_field(name='Duration', value=search_result.duration[0], inline=True)
            embed.add_field(name='Views', value=search_result.views[0], inline=True)
            embed.add_field(name='Publish Time', value=search_result.publish_time[0], inline=True)
            embed.set_footer(text=f'Requested by: {author.name}', icon_url=author.avatar_url)
            return embed
        return Embed(title='Error encountered')

    @commands.command()
    async def play(self, ctx, *args):
        """Plays the best match on youtube of what you search """
        member = ctx.author
        try:
            input_data = " ".join(args)

            async with ctx.typing():
                need_search = True
                if 'https' in input_data:
                    need_search = False
                    url = input_data
                elif '/watch' in input_data:
                    need_search = False
                    url = f'https://www.youtube.com{input_data}'

                if need_search:
                    search_result = self.search_on_youtube(input_data)
                    url = f'https://www.youtube.com{search_result.url_suffix[0]}'
                    await ctx.send(embed=self.construct_search_embed(member, input_data, search_result))

                self.log.debug(f"Url to request:  {url}")
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=lambda e: self.log.info('Player error: %s' % e) if e else None)
                await ctx.send(embed=self.construct_now_playing_embed(member, url))

        except Exception as e:
            await ctx.send(Error(f"Exception: {e}"))

    @commands.command()
    async def play_local(self, ctx, *, query):
        """Plays a file from the local filesystem"""
        member = ctx.author
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: self.log.info('Player error: %s' % e) if e else None)

        await ctx.send(f'Now playing: {query}. Chosen by {member}')

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't pre-download)"""
        member = ctx.author
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: self.log.info('Player error: %s' % e) if e else None)
        await ctx.send(embed=self.construct_now_playing_embed(member, url))

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))
        self.log.info("Changed volume to {}%".format(volume))

    @commands.command()
    async def search(self, ctx, *args):
        """Search for youtube urls"""
        member = ctx.author
        try:
            input_data = " ".join(args)
            search_result = self.search_on_youtube(input_data, 5)
            await ctx.send(embed=self.construct_search_embed(member, input_data, search_result))

        except Exception as e:
            await ctx.send(Error(f"Exception: {e}"))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @play.before_invoke
    @stream.before_invoke
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
