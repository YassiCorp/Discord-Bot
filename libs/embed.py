from datetime import datetime
from enum import Enum
from typing import Union
from config import config
import discord

from emojis import emoji

def Icon() -> str:
    today = datetime.today()
    day, month = today.day, today.month

    # Dictionnaire pour correspondance mois/jour avec des icônes
    special_icons = {
        (30, 6): "anniversary_icon",
        (12, 10): "halloween_icon",
        (11, None): "nnn_icon",  # tout novembre
        (None, 12): "santa_icon"  # tout décembre
    }

    # Vérification pour les dates précises
    if (day, month) in special_icons:
        logo = emoji.get(special_icons[(day, month)])
    elif (None, month) in special_icons:
        logo = emoji.get(special_icons[(None, month)])
    else:
        logo = emoji.get("star_icon")

    return logo

class IconType(Enum):
    none = ""
    dynamic_icon = Icon()


class ModernEmbed(discord.Embed):
    def __init__(self, icon: Union[str, IconType] = IconType.dynamic_icon, title: str = "", description: str = "", color: Union[int, discord.Color] = config.EMBED.COLOR):
        self.icon = icon.value
        self.title = title
        self.description = description

        super().__init__(description=self.get_text(), color=color)

    def _set_description(self):
        self.set_description(self.get_text())

    def get_text(self):
        text = ""
        if self.title:
            text = f"### {self.icon} {self.title}"
        if self.description:
            text += f"\n\n{self.description}"

        return text

    def set_icon(self, icon: Union[str, IconType]):
        self.icon = icon.value
        self._set_description()

    def set_title(self, title: str):
        self.title = title
        self._set_description()
        return self

    def set_description(self, description: str):
        self.description = description
        self._set_description()
        return self

class IconTypeError(Enum):
    error = emoji.get("achtung_icon")

class ErrorEmbed(ModernEmbed):
    def __init__(self, description: str, title: str = None, code_style: bool = False, icon: Union[str, IconTypeError] = IconTypeError.error, color: Union[int, discord.Color] = config.EMBED.COLOR):
        self.icon = icon
        self.title = f"Erreur {f'| {title}' if title else ''}"
        if code_style:
            self.description = f"```PYTHON\n {description} \n```"
        else:
            self.description = f"> {description}"

        super().__init__(title=self.title, description=self.description, icon=self.icon, color=color)

class IconTypeLoading(Enum):
    discord_loading = emoji.get("discord_loading")

class LoadingEmbed(discord.Embed):
    def __init__(self, icon: Union[str, IconTypeLoading] = IconTypeLoading.discord_loading, title: str = "Loading...", description: str = "", color: Union[int, discord.Color] = config.EMBED.COLOR):
        self.icon = icon.value
        self.title = title
        self.description = description

        super().__init__(description=self.get_text(), color=color)

    def _set_description(self):
        self.set_description(self.get_text())

    def get_text(self):
        text = f"## {self.icon} {self.title}\n\n{'>>> ' + self.description if self.description else ''}"
        return text

    def set_icon(self, icon: Union[str, IconType]):
        self.icon = icon.value
        self._set_description()

    def set_title(self, title: str):
        self.title = title
        self._set_description()
        return self

    def set_description(self, description: str):
        self.description = description
        self._set_description()
        return self


# Advanced Loading Embed
class LoadingPercent:
    def __init__(self, ctx: discord.ApplicationContext, title: str, prefix: str, max_value: int,
                 ephemeral: bool = False, bar_length: int = 6):
        self.ctx = ctx
        self.title = title
        self.prefix = prefix
        self.max_value = max_value
        self.ephemeral = ephemeral
        self.msg = None

        # The number of emojis used in the loading bar (dynamic)
        self.bar_length = bar_length

    def get_progress_emoji(self, value: int) -> str:
        """Génère une barre de chargement en émojis basée sur la progression."""
        emoji1_empty = emoji.loading_none_1
        emoji2_empty = emoji.loading_none_2
        emoji3_empty = emoji.loading_none_3

        emoji1_fill = emoji.loading_fill_1
        emoji2_fill = emoji.loading_fill_2
        emoji3_fill = emoji.loading_fill_3

        total_slots = self.bar_length
        progress = round((value * total_slots) / self.max_value)
        progress = min(progress, total_slots)

        if progress >= 1:
            start_emoji = emoji1_fill
        else:
            start_emoji = emoji1_empty

        if progress == total_slots:
            end_emoji = emoji3_fill
        else:
            end_emoji = emoji3_empty

        middle_slots = total_slots - 2
        middle_progress = max(progress - 2, 0)
        middle_empty = middle_slots - middle_progress

        middle_emojis = (
                emoji2_fill * middle_progress + emoji2_empty * middle_empty
        )

        loading_bar = start_emoji + middle_emojis + end_emoji
        return loading_bar

    def to_embed(self, value: int, prefix: str = None) -> discord.Embed:
        """Create an embed representing the current loading state."""
        if prefix is None:
            prefix = self.prefix

        emojis = self.get_progress_emoji(value)
        embed = ModernEmbed(
            title=f"Loading | {self.title}",
            description=f"> {prefix} {emojis} **{value}/{self.max_value}**",
        )
        return embed

    async def send(self):
        """Send the initial message with loading progress."""
        embed = self.to_embed(value=0)
        self.msg = await self.ctx.respond(embed=embed, ephemeral=self.ephemeral)

    async def edit(self, value: int, prefix: str = None):
        """Edit the loading progress message."""
        if self.msg is None:
            raise ValueError("Message not sent yet. Call 'send' before editing.")

        embed = self.to_embed(value=value, prefix=prefix)
        await self.msg.edit(embed=embed)

    async def get_msg(self) -> discord.Message:
        """Return the sent message."""
        return self.msg