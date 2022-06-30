from discord import TextChannel
from discord_components import Button


def create_btn(label: str, custom_id: str, emoji=''):
    return Button(label=label, custom_id=custom_id, emoji=emoji)


class MusicComponent:
    @staticmethod
    def construct():
        cmp = [
            [create_btn('Pause', 'pause_btn'),
             create_btn('Play', 'play_btn'),
             create_btn('Stop', 'next_btn'),
             create_btn('Stop', 'stop_btn'),
             ]
        ]

    @staticmethod
    async def interaction_control(self, execute_fx):
        interaction = await self.bot.wait_for('button_click', check=execute_fx)

