import discord
import lavalink
from OltreBot.util.colors import *
import datetime


class MusicEmbed:
    @staticmethod
    def playlist(self, author: discord.client, track: lavalink.AudioTrack):
        self.log.info(f"Track embed asked by {yellow(author.name)}")
        embed = discord.Embed()
        return embed

    @staticmethod
    def empty(self, author: discord.client) -> discord.Embed:
        self.log.info(f"Creating empty embed asked by {yellow(author.name)}")
        embed = discord.Embed(title=f'No Current Track',
                              author=self.bot.user.name,
                              url='',
                              colour=discord.Colour(0xE11B1B))

        embed.set_thumbnail(url=self.bot.user.avatar_url)
        return embed

    @staticmethod
    def track(self, author: discord.client, track: lavalink.AudioTrack) -> discord.Embed:
        self.log.info(f"Creating track embed asked by {yellow(track.requester.name)}")

        embed = discord.Embed(title=f'Now Playing',
                              author=self.bot.user.name,
                              url=track.uri,
                              colour=discord.Colour(0xE11B1B))

        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.set_image(url=track.thumbnail)
        # embed.add_field(name='Artist', value=track.author, inline=True)
        embed.add_field(name='Title', value=track.title, inline=True)
        embed.add_field(name='Duration', value=str(datetime.timedelta(milliseconds=track.duration)), inline=True)
        embed.set_footer(text=f'Requested by: {track.requester.name}', icon_url=track.requester.avatar_url)

        return embed
