from .Online import Online
from .Welcome import Welcome
from .music import OltreMusic
from OltreBot.util.logger import get_logger

OnlineLogger = get_logger('Online', sub_folder='cog')
MusicLogger = get_logger('Music', sub_folder='cog')
WelcomeLogger = get_logger('Welcome', sub_folder='cog')

def setup(bot):
    bot.add_cog(Online(bot, OnlineLogger))
    bot.add_cog(Welcome(bot, WelcomeLogger))
    bot.add_cog(OltreMusic(bot, MusicLogger))
