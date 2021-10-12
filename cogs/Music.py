import discord
from discord.ext.commands import Cog
from discord.ext import commands
from youtube_search import YoutubeSearch
from tabulate import tabulate
import asyncio
import youtube_dl
import pandas as pd

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
    def __init__(self, source, *, data, volume=0.5):
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

    @Cog.listener()
    async def on_ready(self):
        print('Music logged in as {0} ({0.id})'.format(self.bot.user))
        print('------')

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""
        member = ctx.author
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send(f'Now playing: {query}. Chosen by {member}')

    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))
        print('Now playing: {}'.format(player.title))

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""
        member = ctx.author
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send(f'Now playing: {player.title}. Chosen by {member}')
        print(f'Now playing: {player.title}. Chosen by {member}')

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))
        ("Changed volume to {}%".format(volume))

    @commands.command()
    async def search(self, ctx, *args):
        """Search for youtube urls"""
        try:
            pre_data = []
            while len(pre_data) == 0:
                pre_data = YoutubeSearch(f'search {"".join(args)}', max_results=5).to_dict()
            data = pd.DataFrame(pre_data)
            data = data.drop(columns=['id', 'channel', 'long_desc', 'publish_time', 'thumbnails', 'duration', 'views'])
            print(data)
            await ctx.send(Success("```" + f'\n\n{tabulate(data, headers="keys", tablefmt="rst")}' + "```"))
            print(f"Searched: {''.join(args)}")

        except Exception as e:
            await ctx.send(Error(f"Exception: {e}"))

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
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

    @commands.command()
    async def gaetano(self, ctx):
        """ ? """
        member = ctx.author
        await ctx.send(f'Si hai proprio ragione {member.name}, Gaetano puzza ! xD ')


def setup(bot):
    bot.add_cog(Music(bot))
