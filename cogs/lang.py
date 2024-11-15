from discord.ext import commands
from databases.language import LanguageDB
from config import config
import discord

guilds = config.BOT.GUILDS

class language(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = LanguageDB()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self.db.set_default_language_guild(guild.id, "fr")

    @discord.slash_command(
        name="language",
        description="Changer la langue du bot !",
        guild_ids=guilds,
    )
    async def language(self, ctx: discord.ApplicationContext):
        self.db.set_default_language_user(ctx.author.id, "fr")



def setup(bot):
    bot.add_cog(language(bot))
