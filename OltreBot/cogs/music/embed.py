import discord
import lavalink
from OltreBot.util.colors import *
from typing import List
import datetime


class MusicEmbed:
    @staticmethod
    def playlist(self, author: discord.client, playlist_name: str, tracks: List[lavalink.AudioTrack],
                 execute_time: float) -> discord.Embed:
        self.log.info(f"Track <playlist> asked by {yellow(author.name)}")

        data = []
        for idx, track in enumerate(tracks):
            if isinstance(track, dict):
                t = lavalink.AudioTrack(track, requester=author, recommended=True)
            else:
                t = track
            data.append(f"`{idx + 1}` ** {t.title} **\t {str(datetime.timedelta(milliseconds=t.duration))}")

        embed = discord.Embed(title=playlist_name + f" {len(tracks)}", color=discord.Color.green(),
                              description="\n".join(data), timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f'Youtube Music playlist in {execute_time:.1f} ms', icon_url=self.bot.user.avatar_url)
        return embed

    @staticmethod
    def queue(self, tracks: List[lavalink.AudioTrack]) -> discord.Embed:
        self.log.info(f"Track <queue> update")
        data = []
        first = True
        thumbnail = ''
        for idx, track in enumerate(tracks):
            if isinstance(track, dict):
                t = lavalink.AudioTrack(track, requester=self.bot.user, recommended=True)
            else:
                t = track

            if first:
                data.append(f"`{idx + 1}` ** {t.title} **\t {str(datetime.timedelta(milliseconds=t.duration))}")
                thumbnail = t.thumbnail
                first = False
            else:
                data.append(f"`{idx + 1}` {t.title} \t {str(datetime.timedelta(milliseconds=t.duration))}")

        embed = discord.Embed(title='Current Queue' + f" {len(tracks)}", color=discord.Color.green(),
                              description="\n".join(data), timestamp=datetime.datetime.utcnow(), thumbnail=thumbnail)
        embed.set_image(url=thumbnail)
        embed.set_footer(text=f'', icon_url=self.bot.user.avatar_url)
        return embed

    @staticmethod
    def empty(self, author: discord.client) -> discord.Embed:
        self.log.info(f"Creating <empty> embed asked by {yellow(author.name)}")
        embed = discord.Embed(title=f'No Current Track',
                              author=self.bot.user.name,
                              url='',
                              colour=discord.Colour(0xE11B1B),
                              timestamp=datetime.datetime.utcnow())

        embed.set_thumbnail(url=self.bot.user.avatar_url)
        return embed

    @staticmethod
    def bot_started(self) -> discord.Embed:
        self.log.info(f"Creating <bot_started>")
        embed = discord.Embed(title=f'OltreBot has started',
                              author=self.bot.user.name,
                              url='',
                              description="Welcome to the new OltreBot queue system.\n Now I'll send updates only in this channel showing you the current queue.\nEnjoy 😉",
                              colour=discord.Colour(0xE11B1B),
                              timestamp=datetime.datetime.utcnow())

        embed.set_thumbnail(url=self.bot.user.avatar_url)
        return embed

    @staticmethod
    def track(self, author: discord.client, track: lavalink.AudioTrack) -> discord.Embed:
        self.log.debug(f'TrackType: {type(track)}')
        self.log.info(f"Creating <track> embed asked by {yellow(track.requester.name)}")

        embed = discord.Embed(title=f'Now Playing',
                              author=author.name,
                              url=track.uri,
                              colour=discord.Colour(0x9003fc),
                              timestamp=datetime.datetime.utcnow())

        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_image(url=track.thumbnail)
        embed.add_field(name='Artist', value=track.author, inline=True)
        embed.add_field(name='Title', value=track.title, inline=True)
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=track.duration)), inline=True)
        embed.set_footer(text=f'Requested by: {track.requester.name}', icon_url=track.requester.avatar_url)

        return embed

    @staticmethod
    def search(self, author: discord.client, track: lavalink.AudioTrack, execute_time: float) -> discord.Embed:
        self.log.info(f"Creating <search> track embed asked by {yellow(author.name)}")
        # Green embed
        embed = discord.Embed(color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name='Title', value=track.title, inline=True)
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=track.duration)), inline=True)
        embed.set_footer(text=f'Youtube search in {execute_time:.1f} ms', icon_url=self.bot.user.avatar_url)
        return embed

    @staticmethod
    def failed(self, author: discord.client, message: str, execute_time: float) -> discord.Embed:
        self.log.info(f"Creating <failed> track embed asked by {yellow(author.name)}")
        embed = discord.Embed(color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name='Result', value=message, inline=True)
        embed.set_footer(text=f'Failed in {execute_time:.1f} ms', icon_url=self.bot.user.avatar_url)
        return embed

    @staticmethod
    def success(self, author: discord.client, message: str, execute_time: float) -> discord.Embed:
        self.log.info(f"Creating <success> track embed asked by {yellow(author.name)}")
        embed = discord.Embed(color=discord.Color.green(), title=message, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f'Success in {execute_time:.1f} ms', icon_url=self.bot.user.avatar_url)
        return embed
