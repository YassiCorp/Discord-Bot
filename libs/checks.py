from typing import TypeVar, Callable

from nextcord import Interaction
from nextcord.ext.application_checks import check

from exceptions import *
from config import config

T = TypeVar("T")

def is_owner() -> Callable[[T], T]:
    """
    This is a custom check to see if the user executing the command is an owner of the bot.
    """

    async def predicate(interaction: Interaction) -> bool:
        if not interaction.user.id in config.get("BOT_OWNER"):
            raise UserNotOwner
        return True

    return check(predicate)

