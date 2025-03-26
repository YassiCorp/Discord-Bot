from datetime import timedelta, datetime

import humanfriendly
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
from config import config
from databases.moderation import ModerationDB

guilds = config.BOT.GUILDS

def parse_human_input(human_input: str):
    duration: timedelta = humanfriendly.parse_timespan(human_input)
    return datetime.now() + duration

class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot: nextcord.Client = bot
        self.db = ModerationDB()

    @nextcord.slash_command(
        name="ban",
        description="Vous me le bannez lui ?!",
        guild_ids=guilds
    )
    async def ban(self, ctx: Interaction, user: nextcord.Member = SlashOption(required=True), duration: str = SlashOption(default=None), reason: str = SlashOption(default=None)) -> None:
        if duration:
            duration = parse_human_input(duration)
        self.db.add_ban(guild_id=ctx.guild_id, user_id=user.id, duration=duration, reason=reason)



def setup(bot):
    bot.add_cog(Moderation(bot))