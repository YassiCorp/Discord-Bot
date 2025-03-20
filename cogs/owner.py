import nextcord
from nextcord import Interaction
from nextcord.ext import commands
from libs.embed import ModernEmbed, ErrorEmbed


class Owner(commands.Cog, name="owner"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @nextcord.slash_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @commands.is_owner()
    async def shutdown(self, ctx: Interaction) -> None:
        """
        Shuts down the bot.

        :param ctx: The hybrid command Context.
        """
        embed = ModernEmbed(description="Shutting down. Bye! :wave:")
        await ctx.send(embed=embed)
        await self.bot.close()


def setup(bot) -> None:
    bot.add_cog(Owner(bot))
