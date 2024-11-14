from typing import TypeVar, Callable

import discord
from discord import Interaction
from discord.ext.commands import check, Context

from exceptions import *
from config import config

T = TypeVar("T")

def is_owner() -> Callable[[T], T]:
    """
    This is a custom check to see if the user executing the command is an owner of the bot.
    """

    async def predicate(interaction: Context) -> bool:
        if not interaction.author.id in config.get("BOT_OWNER"):
            raise UserNotOwner
        return True

    return check(predicate)

