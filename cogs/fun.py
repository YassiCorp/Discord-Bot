import aiofiles, aiohttp, asyncio
import io, os, re, PIL
import discord
import random

from PIL import Image, ImageDraw
from discord import HTTPException, NotFound
from discord.ext import commands

from colormath2.color_objects import sRGBColor, LabColor
from colormath2.color_conversions import convert_color
from colormath2.color_diff import delta_e_cie1976

from config import config
from emojis import emoji
from libs.embed import ModernEmbed, LoadingEmbed, ErrorEmbed
from libs.message import send_with_delete_button, send_timeout_msg
from libs.path import PATH_IMAGE_GIGACHAD, PATH_CACHE_IMG
from libs.utils import ClassicUrlButton

guilds = config.BOT.GUILDS


class CoinFlip_Choice(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.message = f"{emoji.discord_support} · Tu n'es pas l'utilisateur demandé."
        self.user = user
        self.value = None

    @discord.ui.button(label="Face", style=discord.ButtonStyle.blurple)
    async def face(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.user.id:
            await interaction.response.defer()
            self.value = "Face"
            self.stop()
        else:
            await interaction.response.send_message(self.message, ephemeral=True)

    @discord.ui.button(label="Pile", style=discord.ButtonStyle.blurple)
    async def pile(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.user.id:
            await interaction.response.defer()
            self.value = "Pile"
            self.stop()
        else:
            await interaction.response.send_message(self.message, ephemeral=True)

class Fun(commands.Cog, name="fun"):
    def __init__(self, bot):
        self.bot = bot

    #  ______________________________________________
    # |  __________________________________________  |
    # | | CoinFlip:   Game n°2                     | |
    # | |  → "CoinFlip fait tourner une piece ;)"  | |
    # | |__________________________________________| |
    # |______________________________________________|
    @discord.slash_command(
        name="coinflip",
        description="Faire un lancer de pièce. (Bah c bon j'ai compris, j'avais pas d'idée de cmd)",
        guild_ids=guilds,
    )
    async def coinflip(self, ctx: discord.ApplicationContext) -> None:
        buttons = CoinFlip_Choice(user=ctx.user)
        embed = ModernEmbed(title=f"Coin Flip",
                            description=f"> {emoji.discord_mention} {ctx.user.mention}, Quel est votre pari ? {emoji.sans}",
                            color=0x9C84EF)
        msg = await ctx.respond(embed=embed, view=buttons)
        await buttons.wait()

        if buttons.value is None:
            await send_timeout_msg(ctx=msg, title="Coin Flip", user=ctx.user)
            return

        result = random.choice(["Face", "Pile"])

        # Animation

        urls = ["https://cdn.discordapp.com/attachments/937796349884248104/1044680461596766378/5291f56897d748b1ca0a10c90023588d.gif", "https://cdn.discordapp.com/attachments/937796349884248104/1044681526958374992/d090ed930df18a003a77e74b580390536627a882r1-500-200_hq.gif", "https://cdn.discordapp.com/attachments/937796349884248104/1044681526404731001/tumblr_p9vwb6XoLx1w9y0e9o3_500.gif"]

        embed = ModernEmbed(title=f"Coin Flip",
                            description=f"> {emoji.discord_mention} {ctx.user.mention}, Lancement de la piece...",
                            color=0x9C84EF)

        embed.set_image(url=random.choice(urls))

        try:
            await msg.edit(embed=embed, view=None, content=None)
        except (HTTPException, NotFound):
            msg = await ctx.respond(embed=embed, content=None)

        await asyncio.sleep(3)

        # Result

        if buttons.value == result:
            embed = ModernEmbed(title=f"Coin Flip",
                                description=f"\n> {emoji.minecraft_accept} Bravo ! Vous avez choisi `{buttons.value}` et j'ai lancé la pièce sur `{result}`.",
                                color=0x9C84EF)
        else:
            embed = ModernEmbed(title=f"Coin Flip",
                                description=f"\n> {emoji.minecraft_deny} Woops! Vous avez choisi `{buttons.value}` et j'ai lancé la pièce sur `{result}`, meilleure chance la prochaine fois !",
                                color=0xE02B2B)

        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/937796349884248104/1044690025067053086/img-cdn.magiceden.gif")

        try:
            await msg.edit(embed=embed, view=None, content=ctx.user.mention)
        except (HTTPException, NotFound):
            await ctx.respond(embed=embed, content=ctx.user.mention)

    #  ______________________________________
    # |  __________________________________  |
    # | | GigaChad:   Game n°4             | |
    # | |  → "gigachad une photo montage"  | |
    # | |__________________________________| |
    # |______________________________________|
    async def GigaChad_Canvas(self, image_url: str):
        filename = image_url.split("/")[-1]
        filename = filename.split("?")[0]
        path = f"{PATH_CACHE_IMG}/{filename}".replace(".gif", ".png").replace(".jpg", ".png")
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as request:
                if request.status == 200:
                    data = await request.read()

                    f = await aiofiles.open(path, mode='wb')
                    await f.write(data)
                    await f.close()

                    im1_gigachad = Image.open(PATH_IMAGE_GIGACHAD)
                    im2_user = Image.open(path).convert("RGBA")

                    wpercent = (405 / float(im2_user.size[0]))
                    hsize = int((float(im2_user.size[1]) * float(wpercent)))
                    im2_user = im2_user.resize((405, hsize), PIL.Image.Resampling.LANCZOS)

                    # Créer un masque circulaire
                    mask = Image.new('L', (405, hsize), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.ellipse((0, 0, 405, hsize), fill=255)

                    # Appliquer le masque à l'image
                    im2_user.putalpha(mask)

                    final_image = im1_gigachad.copy()
                    final_image.paste(im2_user, (375, 70), im2_user)
                    final_image.save(path, "PNG", quality=60)

                    return [True, path]

                else:
                    description = f"**{emoji.achtung_icon} Mhh J'arrive pas a installer la photo...**\n\n> {emoji.discord_cross} La photo de profil ne veut pas s'installer..."
                    return [False, description]

    async def send_giga_chad_msg(self,
            ctx: discord.ApplicationContext,
            user: discord.User,
            bot: discord.Client,
            message: str = "",
    ):
        msg = await ctx.respond(embed=LoadingEmbed())

        # Vérifier si l'utilisateur est MEE6 (ID utilisateur : 159985870458322944)
        if user.id == 159985870458322944:
            gifs = [
                "https://media.tenor.com/87zIsIaxPxoAAAAC/kill-mee6.gif",
                "https://media1.tenor.com/m/EUHnekNVRGAAAAAd/discord-murder.gif",
                "https://media1.tenor.com/m/8WJLs6488ocAAAAC/mee6-solicitation-anxiety.gif",
            ]

            embed = ModernEmbed(
                title="Giga Nul",
                description=f"> Mhhhh, je ... Attends quoi, mais sérieux\n"
                            f"> Qui aime {user.mention}, ce **giga nul**.\n\n"
                            f"**{emoji.discord_info} • Voilà ce qu'il mérite :**"
            )
            embed.set_image(url=random.choice(gifs))

            await msg.edit(embed=embed)
            return

        # Générer l'image GigaChad
        success, result = await self.GigaChad_Canvas(user.display_avatar.url)

        if success:
            if user.id == bot.user.id:
                text = "> Mhhhh, je m'auto-incline \n> ***(Pas très français tout ça)***"
            else:
                text = f"> Mhhhh, je m'incline {user.mention}"

            embed = ModernEmbed(
                title=f"Giga Chad",
                description=f"{text}\n"
                            f"{message}\n"
                            f"**{emoji.discord_info} • L'image :**"
            )

            file = discord.File(result, filename="GigaChad_MHHHHHHHH.png")
            embed.set_image(url="attachment://GigaChad_MHHHHHHHH.png")

            await msg.edit(embed=embed, file=file)
            file.close()

            # Supprimer le fichier image après l'envoi
            if os.path.exists(result):
                os.remove(result)

            await send_with_delete_button(interaction=msg, embed=embed, user=ctx.user)

        else:
            # En cas d'échec de la génération de l'image
            embed = ErrorEmbed(title="~~GigaChad~~ GigaBug", description=result)
            await msg.edit(embed=embed)


    @discord.slash_command(
        name="gigachad",
        description="Transforme quelqu'un en GigaChad O-O !",
        guild_ids=guilds,
    )
    async def gigachad(self, ctx: discord.ApplicationContext, utilisateur: discord.User = discord.Option(discord.User, description="Qui mérite un GigaChad !", required=False, default=None)) -> None:
        if utilisateur is None:
            await self.send_giga_chad_msg(ctx, ctx.user, self.bot)
        else:
            await self.send_giga_chad_msg(ctx, utilisateur, self.bot)

    #
    #
    #

    # Fonction pour générer un code hexadécimal aléatoire
    def generate_random_hex(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    # Fonction pour créer une image avec la couleur hex et la retourner sous forme binaire
    def create_color_image(self, hex_code):
        img_size = (600, 300)
        image = Image.new("RGB", img_size, hex_code)

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # Fonction pour calculer la proximité entre deux codes hexadécimaux en utilisant Delta E
    def calculate_color_similarity(self, hex1, hex2):
        # Convertir les couleurs hex en objets sRGBColor
        color1_rgb = sRGBColor(int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16), is_upscaled=True)
        color2_rgb = sRGBColor(int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16), is_upscaled=True)

        # Convertir les couleurs en espace de couleur Lab
        color1_lab = convert_color(color1_rgb, LabColor)
        color2_lab = convert_color(color2_rgb, LabColor)

        # Calculer la différence Delta E entre les deux couleurs
        delta_e = delta_e_cie1976(color1_lab, color2_lab)

        # Convertir Delta E en pourcentage de similarité
        similarity = max(0, 100 - delta_e)
        return round(similarity, 2)

    # Commande Discord pour générer une couleur
    @discord.slash_command(
        name="guess_color",
        description="Tu guess le code hex la couleur a l'image (Un jeu cree par un nerd, pour les nerds)",
        guild_ids=guilds,
    )
    async def guess_color(self, ctx: discord.ApplicationContext):
        # Générer un code couleur aléatoire
        hex_code = self.generate_random_hex()
        image_buffer = self.create_color_image(hex_code)

        embed = ModernEmbed(title="Guess The Color",
                            description="> Tentez de deviner le code hex de cette couleur !"
                                        f"\n- Exemple: **`{self.generate_random_hex()}`** "
                                        f"\n\n-# {emoji.cursor} Veuillez taper le code hex sur ce channel !",
                            color=discord.Color(int(hex_code.lstrip('#'), 16)))
        embed.set_image(url="attachment://color_image.png")

        view = ClassicUrlButton(url="https://htmlcolorcodes.com/", emoji=emoji.icon_world, label="Sélecteur de codes Hex")

        # Envoyer l'image de couleur et le code hex original
        await ctx.respond(embed=embed, file=discord.File(fp=image_buffer, filename="color_image.png"), view=view)

        # Fonction pour attendre la réponse de l'utilisateur avec un hex code valide
        def check(m):
            # Valider si le message correspond au format hex
            return m.author == ctx.author and m.channel == ctx.channel and (re.fullmatch(r"#([A-Fa-f0-9]{6})", m.content) is not None)

        try:
            # Attendre une réponse de l'utilisateur
            guess = await self.bot.wait_for('message', check=check, timeout=60*3)
            guessed_hex = guess.content

            # Calculer la similarité
            similarity = self.calculate_color_similarity(hex_code, guessed_hex)

            # Envoyer le pourcentage de similarité
            await guess.reply(f"Votre estimation `{guessed_hex}` est à {similarity}% proche de la couleur `{hex_code}`.")

        except TimeoutError:
            await send_timeout_msg(ctx=ctx, title="Guess The Color", user=ctx.user)


def setup(bot):
    bot.add_cog(Fun(bot))
