import base64
import io
import time

import aiohttp
import nextcord
from nextcord import SlashOption, Interaction
from nextcord.ext import commands

from config import config
from emojis import emoji
from libs.embed import ModernEmbed, LoadingEmbed, ErrorEmbed
from libs.message import send_with_delete_button
from libs.paginator import Page, Paginator
from libs.path import PATH_VIDEOS
from libs.utils import DoubleUrlButton, mediawiki_to_discord
from mediawiki import MediaWiki

guilds = config.BOT.GUILDS

class Minecraft(commands.Cog, name="minecraft"):
    def __init__(self, bot):
        self.bot: nextcord.Client = bot
        self.mc_wiki = MediaWiki(url='https://en.minecraft.wiki/api.php')

    @nextcord.slash_command(
        name="minecraft",
        description="Toute les commandes en rapport avec Minecraft...",
        guild_ids=guilds
    )
    async def minecraft(self, ctx: Interaction) -> None:
        pass
    
    # Some cool commands
    @minecraft.subcommand(
        name="skin",
        description="Minecraft | Avoir le visuel du skin d'un joueur...",
    )
    async def skin(self, ctx: Interaction, username: str = SlashOption(description="Met une uuid ou un username d'un compte prémium", required=True)) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://mc-heads.net/head/{username}") as request:
                image1 = request.url

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://mc-heads.net/player/{username}/120") as request:
                image2 = request.url

        if username == "YassiGame" or username == "95f664f3-86e8-4caf-acc9-2c97e84262ef":
            text = f"**YassiGame**... ça me dit un truc !"
        else:
            text = f"{ctx.user.mention}, voici le skin de **{username}**."

        embed1 = ModernEmbed(
            title=f"Skin Minceraft",
            description=f"> {text}\n\n**{emoji.get('discord_info')} • Le Skin:**")

        embed1.set_thumbnail(url=image1)
        embed1.set_image(url=image2)

        view = DoubleUrlButton(label1=f"Télécharger le skin",
                               url1=f"https://mc-heads.net/download/{username}",
                               emoji1=emoji.get("square_download_update"),
                               label2="Ouvrir sur NameMC",
                               url2=f"https://namemc.com/profile/{username}",
                               emoji2=emoji.get("icon_world"))

        await ctx.send(embeds=[embed1], view=view)

    @minecraft.subcommand(
        name="server",
        description="Minecraft | Te donnera quelques infos sur un serveur en utilisant son ip !",
    )
    async def server(self, ctx: Interaction, ip: str = SlashOption(description="Met une ip de ton serveur préféré...", required=True), hideip: bool = SlashOption(description="Veux-tu cacher l'ip du serveur ?", choices={"Oui": True, "Non": False}, required=False, default=False)) -> None:

        msg = await ctx.send(embed=LoadingEmbed())
        new_ip = "censurée" if hideip else ip

        async with aiohttp.ClientSession() as session:
            start_time = time.perf_counter()
            async with session.get(f"https://api.mcsrvstat.us/3/{ip}") as request:
                server = await request.json(encoding="utf-8")
            end_time = time.perf_counter()

        if request.status != 200: # Api ne repond pas
            embed = ErrorEmbed(
                title=f"Serveur Minceraft",
                description=f"L'api mcsrvstat ne repond pas !"
                            f"\n\n> -# **Veuillez ressayer plus tard**")

            await send_with_delete_button(msg, user=ctx.user, embed=embed)
            return

        online: bool = server.get("online")
        ping = (end_time - start_time) * 1000  # Convertir en millisecondes

        if online: # Serveur online
            icon = server.get("icon")
            motd = server.get("motd").get("clean")
            players_online = server["players"]["online"]
            players_max = server["players"]["max"]
            version_name = server.get("software")
            version_code = server.get("version")

            if motd:
                motd = "\n".join(line.lstrip() for line in motd)
                description = f"\n```{motd}```"
            else:
                description = "\n**```Pas de MOTD...```**"

            embed = ModernEmbed(
                title=f"Serveur Minceraft",
                description=f"> Voici les informations pour le serveur"
                            f"\n> avec l'ip `{new_ip}`\n"
                            f"\n**{emoji.get('discord_info')} • MOTD:**"
                            f"{description}")

            embed.add_field(name=f"{emoji.get('discord_search')} • Joueurs:", value=f"{players_online}/{players_max} joueur(s)")
            embed.add_field(name=f"{emoji.get('discord_category')} • Version:", value=f"{version_code} {f'| {version_name}' if version_name else ''}")
            embed.add_field(name=f"{emoji.get('discord_connection')} • Ping:", value=f"{ping:.2f} ms")

            if icon is not None:
                file = nextcord.File(io.BytesIO(base64.b64decode(icon.split("base64,")[-1])), filename="server_icon.png")
                embed.set_thumbnail(url="attachment://server_icon.png")
                await send_with_delete_button(msg, user=ctx.user, embed=embed, file=file)
            else:
                await send_with_delete_button(msg, user=ctx.user, embed=embed)

        else: # Serveur offline
            embed = ErrorEmbed(
                title=f"Serveur Minceraft",
                description=f"Le serveur minecraft avec l'ip `{new_ip}`"
                            f"\n>  n'as pas donnée de réponse."
                            f"\n\n> -# **Veuillez vérifier l'ip ou ressayez plus tard**")

            await send_with_delete_button(msg, user=ctx.user, embed=embed)

    @minecraft.subcommand(
        name="gravity",
        description="Minecraft | Pourquoi la gravité n'existe pas sur minecraft ?",
    )
    async def gravity(self, ctx: Interaction) -> None:
        file = nextcord.File(f"{PATH_VIDEOS}/Meme_MC_Gravity.mp4", filename="Meme_MC_Gravity.mp4")
        msg = await ctx.send(embed=LoadingEmbed())
        await msg.edit(content=f"> {ctx.user.mention} Voila pourquoi:", file=file, embed=None)

    @minecraft.subcommand(
        name="wiki",
        description="Minecraft | Chercher dans le wiki",
    )
    async def wiki(self, ctx: Interaction,
                      search: str = SlashOption(description="L'objet ou items dans minecraft que tu veux chercher", required=True),
                      results: int = SlashOption(description="Combien de résultats tu veux, le clients est roi (le max est 10)", min_value=1, max_value=10, default=3)
                      ) -> None:

        msg = await ctx.send(embed=LoadingEmbed())

        listResults = self.mc_wiki.search(search, results=results)
        listPages = [self.mc_wiki.page(r) for r in listResults] # create a list of the results

        if not listPages:
            embed = ErrorEmbed(title="Minecraft Wiki",
                               description=f"{emoji.get('sans')} Aucun résultat n'a été trouvé pour la recherche suivante : `{search}`.")

            await msg.edit(embed=embed)
            return

        mypages = []
        for page in listPages:
            embed = ModernEmbed(title=f"Minecraft Wiki | **`{search}`**",
                                description=f"# __{page.title}__"
                                            f"\n\n {mediawiki_to_discord(page.summarize(chars=695))}")

            if page.images:
                embed.set_thumbnail(url=page.images[0])

            class view(nextcord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(nextcord.ui.Button(label="Lien", emoji=emoji.get("icon_world"), row=1, url=page.url))

            mypages.append(Page(embeds=[embed], view=view()))

        paginator = Paginator(
            pages=mypages,
            author_check=True,
            loop_pages=True,
            show_disabled=True,
            timeout=60 * 5,  # 5 minutes
        )
        await paginator.send(msg.channel)


def setup(bot):
    bot.add_cog(Minecraft(bot))