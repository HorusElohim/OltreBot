import discord
import time
import ytm
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union, Dict
from .base_music import BaseMusic

YTM = ytm.YouTubeMusic()


class OltreMusic(BaseMusic):
    embed_id: Union[Dict, None] = None

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        pass

    @commands.command(aliases=['r'])
    async def radio(self, ctx: Context, *, query: str):
        """ Searches and plays a radio playlist from a given query. """
        pass

    @commands.command(aliases=['c'])
    async def clear(self, ctx: Context):
        """ Clear queue Tracks """
        pass

    @commands.command(alias=['skip', 'n'])
    async def next(self, ctx: Context):
        """ Next Track """
        pass

    @commands.command()
    async def pause(self, ctx: Context):
        """ Pause the player Track """
        pass

    @commands.command()
    async def resume(self, ctx: Context):
        """ Resume the player Track  """
        pass
