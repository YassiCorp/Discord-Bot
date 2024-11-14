
import discord
from discord.ext import commands
from libs.embed import ModernEmbed, ErrorEmbed


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @discord.slash_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @commands.is_owner()
    async def shutdown(self, ctx: discord.ApplicationContext) -> None:
        """
        Shuts down the bot.

        :param ctx: The hybrid command Context.
        """
        embed = ModernEmbed(description="Shutting down. Bye! :wave:")
        await ctx.respond(embed=embed)
        await self.bot.close()


def setup(bot) -> None:
    bot.add_cog(Owner(bot))
