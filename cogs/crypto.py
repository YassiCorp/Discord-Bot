from binance.spot import Spot
from discord.ext import commands

from emojis import emoji
from libs.embed import LoadingEmbed, ModernEmbed

import discord

client = Spot()

async def SendCryptoInfo(ctx: discord.ApplicationContext, name: str, id: str):
    msg = await ctx.respond(embed=LoadingEmbed())

    price = round(float(client.avg_price(id)['price']), 3)

    embed = ModernEmbed(
            title=f"**Cryptomonnaie  | {name}**\n",
            description=f"> {emoji.hutao_stonks} {ctx.user.mention} la cryptomonnaie **`{name}`** a un prix de **{price} $** {emoji.rbg_lego_stud}")

    await msg.edit(embed=embed)

class Crypto(commands.Cog, name="crypto"):
    def __init__(self, bot):
        self.bot: discord.Client = bot

    crypto = discord.SlashCommandGroup("crypto", "Crypto commands")

    @crypto.command(
        name="bitcoin",
        description="Crypto | Cryptomonnaie BitCoin (BTC)",
    )
    async def bitcoin(self, ctx: discord.ApplicationContext) -> None:
        await SendCryptoInfo(ctx=ctx, name="BitCoin", id="BTCBUSD")

    @crypto.command(
        name="ethereum",
        description="Crypto | Cryptomonnaie Ethereum (ETH)",
    )
    async def ethereum(self, ctx: discord.ApplicationContext) -> None:
        await SendCryptoInfo(ctx=ctx, name="Ethereum", id="ETHBUSD")

    @crypto.command(
        name="doge",
        description="Crypto | Cryptomonnaie Dogecoin (DOGE)",
    )
    async def doge(self, ctx: discord.ApplicationContext) -> None:
        await SendCryptoInfo(ctx=ctx, name="Dogecoin", id="DOGEBUSD")

    @crypto.command(
        name="bat",
        description="Crypto | Cryptomonnaie Basic Attention Token (BAT)",
    )
    async def bat(self, ctx: discord.ApplicationContext) -> None:
        await SendCryptoInfo(ctx=ctx, name="Basic Attention Token", id="BATBUSD")

    @crypto.command(
        name="shushi",
        description="Crypto | Cryptomonnaie Sushi (SUSHI)",
    )
    async def shushi(self, ctx: discord.ApplicationContext) -> None:
        await SendCryptoInfo(ctx=ctx, name="Sushi", id="SUSHIBUSD")




def setup(bot):
    bot.add_cog(Crypto(bot))
