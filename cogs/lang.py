import nextcord
from nextcord import Interaction
from nextcord.ext import commands

from databases.language import LanguageDB
from config import config

guilds = config.BOT.GUILDS

class language(commands.Cog):
    def __init__(self, bot):
        self.bot: nextcord.Client = bot
        self.db = LanguageDB()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: nextcord.Guild):
        self.db.set_default_language_guild(guild.id, "fr")

    @nextcord.slash_command(
        name="language",
        description="Changer la langue du bot !",
        guild_ids=guilds,
    )
    async def language(self, ctx: Interaction):
        self.db.set_default_language_user(ctx.user.id, "fr")



def setup(bot):
    bot.add_cog(language(bot))
