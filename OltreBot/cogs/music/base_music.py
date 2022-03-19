import lavalink
from discord.ext import commands
from discord.ext.commands import Cog, Context
from .lavalink_voice_client import LavalinkVoiceClient
from ..Base import BaseCog


class BaseMusic(BaseCog):

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

    async def cog_before_invoke(self, ctx: Context):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voice channel.

        return guild_check

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
        try:
            return self.bot.lavalink.player_manager.create(guild_id, endpoint=guild_region)
        except lavalink.NodeError:
            self.log.error("Create Player with no player connected")

    def log_user_call_command(self, ctx: Context, cmd_name: str, *args):
        self.log.info(f"Command: <{magenta(cmd_name)}| {cyan(' '.join(args))}> asked by {yellow(ctx.author.name)}")

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
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

    async def track_hook(self, event):
        pass

    @commands.command(aliases=['stop'])
    async def disconnect(self, ctx: Context):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.get_player(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await self.send_ctx_msg(ctx, 'Not connected', self.color.YELLOW)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await self.send_ctx_msg(ctx, "You're not in my voice channel!", self.color.YELLOW)

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.voice_client.disconnect(force=True)
        await self.send_ctx_msg(ctx, '**Disconnected**')
