from .Online import Online
from .Welcome import Welcome
from .Music import Music


def setup(bot):
    bot.add_cog(Online(bot))
    bot.add_cog(Welcome(bot))
    bot.add_cog(Music(bot))
