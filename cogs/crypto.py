from binance.spot import Spot
from nextcord import Interaction, slash_command
from nextcord.ext import commands

from emojis import emoji

import nextcord

from libs.embed import LoadingEmbed, ModernEmbed

client = Spot()

async def SendCryptoInfo(ctx: Interaction, name: str, id: str):
    msg = await ctx.send(embed=LoadingEmbed())

    price = round(float(client.avg_price(id)['price']), 3)

    embed = ModernEmbed(
            title=f"**Cryptomonnaie  | {name}**\n",
            description=f"> {emoji.get('hutao_stonks')} {ctx.user.mention} la cryptomonnaie **`{name}`** a un prix de **{price} $** {emoji.get('rbg_lego_stud')}")

    await msg.edit(embed=embed)

class Crypto(commands.Cog, name="crypto", description=""):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @nextcord.slash_command(
        name="crypto",
    )
    async def crypto(self, ctx: Interaction) -> None:
        pass

    @crypto.subcommand(
        name="bitcoin",
        description="Crypto | Cryptomonnaie BitCoin (BTC)",
    )
    async def bitcoin(self, ctx: Interaction) -> None:
        await SendCryptoInfo(ctx=ctx, name="BitCoin", id="BTCBUSD")

    @crypto.subcommand(
        name="ethereum",
        description="Crypto | Cryptomonnaie Ethereum (ETH)",
    )
    async def ethereum(self, ctx: Interaction) -> None:
        await SendCryptoInfo(ctx=ctx, name="Ethereum", id="ETHBUSD")

    @crypto.subcommand(
        name="doge",
        description="Crypto | Cryptomonnaie Dogecoin (DOGE)",
    )
    async def doge(self, ctx: Interaction) -> None:
        await SendCryptoInfo(ctx=ctx, name="Dogecoin", id="DOGEBUSD")

    @crypto.subcommand(
        name="bat",
        description="Crypto | Cryptomonnaie Basic Attention Token (BAT)",
    )
    async def bat(self, ctx: Interaction) -> None:
        await SendCryptoInfo(ctx=ctx, name="Basic Attention Token", id="BATBUSD")

    @crypto.subcommand(
        name="shushi",
        description="Crypto | Cryptomonnaie Sushi (SUSHI)",
    )
    async def shushi(self, ctx: Interaction) -> None:
        await SendCryptoInfo(ctx=ctx, name="Sushi", id="SUSHIBUSD")




def setup(bot):
    bot.add_cog(Crypto(bot))
