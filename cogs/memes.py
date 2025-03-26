import nextcord
from PIL import Image, ImageDraw
from nextcord.ext import commands
from nextcord import SlashOption, Interaction

from libs.embed import ModernEmbed, LoadingEmbed, ErrorEmbed
from libs.message import send_with_delete_button, send_timeout_msg
from libs.paginator import Page, Paginator
from libs.redis_server import redisServer
from libs.utils import ClassicUrlButton, autocomplete, find_option_value
from config import config
from emojis import emoji

import io
import json
import random
import aiohttp
import nextcord

CACHE_DURATION = 3600

guilds = config.BOT.GUILDS
redis_cache = redisServer


class linesTemplateMemeModal(nextcord.ui.Modal):
    def __init__(self, lines: int, exemple_text: list):
        super().__init__(timeout=2 * 60, title="Créer un meme avec amour")
        self.result = None

        placeholders = ["YassiCorp Bot est trop beau !",
                        "MEE6 la soumise qui aime etre insulte",
                        "No Python ?",
                        "Yassi est le boss !"]

        # Directement ajouter les items sans passer par une liste intermédiaire
        for i in range(lines):
            # Si l'indice dépasse la longueur de `exemple_texte`, on utilise le placeholder par défaut
            placeholder = exemple_text[i] if i < len(exemple_text) else random.choice(placeholders)

            input_text = nextcord.ui.TextInput(
                label=f"Ligne n{i+1}",
                style=nextcord.TextInputStyle.short,
                placeholder=f"Exemple: {placeholder}",
                required=(i == 0)  # Le premier champ est obligatoire
            )
            self.add_item(input_text)

    async def callback(self, interaction: nextcord.Interaction):
        # Récupérer les valeurs des items directement avec une compréhension de liste
        values = []
        for item in self.children:
            value = item.value or ""
            values.append(value)

        self.result = values
        await interaction.response.defer()
        self.stop()


async def get_id_by_name(name_to_find: str):
    ids, names = await get_template_list()

    X = 0
    for name in names:
        id = ids[X]

        if name == name_to_find:
            return id  # Renvoie l'ID correspondant au nom

        X += 1

    return None  # Si aucun nom ne correspond, renvoie None


async def get_template_list():
    """Appelle l'API et récupère les templates si le cache a expiré."""

    # Vérifie si les données en cache existent et sont toujours valides
    cached_templates = redis_cache.get("memes.templates")

    if cached_templates:
        templates = json.loads(cached_templates)
        return templates

    # Si le cache est expiré ou vide, appelle l'API
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.memegen.link/templates") as request:
            if request.status != 200:  # Vérifie si l'API répond
                return "error", "error"

            response = await request.json(encoding="utf-8")

    # Traite la réponse
    ids = []
    names = []

    for template in response:
        id = template.get("id")
        name = template.get("name")

        if id is not None:
            ids.append(id)
        if name is not None:
            names.append(name)

    # Met à jour le cache Redis avec les nouvelles données et le timestamp actuel
    templates = (ids, names)
    await redis_cache.set("memes.templates", json.dumps(templates), ex=CACHE_DURATION)

    return ids, names

async def autocomplete_get_polices(ctx, interaction: Interaction, query: str):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.memegen.link/fonts") as request:
            response = await request.json(encoding="utf-8")

    if request.status != 200:  # Api ne repond pas
        return "error"

    ids = []
    for font in response:
        ids.append(font.get("id"))

    return await autocomplete(ids, query=query)

def add_cutout_effect(img):
    """Ajoute une bulle de dialogue avec une découpe en ellipse en haut et un triangle en bas pointant vers le haut."""
    img = img.convert("RGBA")
    width, height = img.size

    mask = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(mask)

    # Découpe en ellipse en haut (inchangée)
    bubble_height = int(height * 0.1)
    bubble_x0 = -25
    bubble_y0 = -15
    bubble_x1 = width + 25 * 2
    draw.rectangle([(0, 0), (width, height)], fill=255)
    draw.ellipse([bubble_x0, bubble_y0, bubble_x1, bubble_y0 + bubble_height], fill=0)

    # Triangle en bas pointant vers le haut
    triangle_height = int(height * 0.1)
    triangle_width = int(width * 0.2)

    triangle_base_left_x = width // 2 - triangle_width // 2
    triangle_base_left_y = height
    triangle_base_right_x = width // 2 + triangle_width // 2
    triangle_base_right_y = height
    triangle_tip_x = width // 2
    triangle_tip_y = height - triangle_height

    draw.polygon([
        (triangle_base_left_x, triangle_base_left_y),    # Coin gauche de la base (en bas)
        (triangle_base_right_x, triangle_base_right_y),  # Coin droit de la base (en bas)
        (triangle_tip_x, triangle_tip_y)                 # Pointe du triangle (vers le haut)
    ], fill=0)

    img.putalpha(mask)
    return img


class Meme(commands.Cog, name="meme"):
    def __init__(self, bot):
        self.bot = bot

        self.ERROR_NOTFOUND = ErrorEmbed(
            title=f"Meme",
            description=f"> L'id / le nom de la template est incorrecte !")

        self.ERROR_API = ErrorEmbed(
            title=f"Meme",
            description=f"L'api meme ne repond pas !"
                        f"\n\n> -# **Veuillez ressayer plus tard**")

    @nextcord.slash_command(
        name="meme",
        description="Des meme par ici... Par la...", 
        guild_ids=guilds
    )
    async def meme(self, ctx: Interaction):
        pass    

    @meme.subcommand(
        name="random",
        description="Un petit mème random pour débuter la journée !"
    )
    async def meme_random(self, ctx: Interaction,
                          subreddit=SlashOption(
                              description="Choisis un subreddit dans lequel tu veux que le mème soit pris !",
                              default=None)) -> None:

        default_subreddits = ["memes",
                              "dankmemes",
                              "me_irl",
                              "MemeFrancais"]

        if subreddit:
            url = f"https://meme-api.com/gimme/{subreddit}/1"
        else:
            url = f"https://meme-api.com/gimme/{random.choice(default_subreddits)}/1"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as request:
                    response = await request.json(encoding="utf-8")
        except:  # Api ne repond pas
            embed = self.ERROR_API
            await send_with_delete_button(ctx, user=ctx.user, embed=embed)
            return

        response = response.get("memes")[0]

        subreddit = response.get("subreddit")
        postLink = response.get("postLink")
        title = response.get("title")
        author = response.get("author")
        url = response.get("url")
        spoiler = response.get("spoiler")

        url = f"||{url}||" if spoiler else url

        embed = ModernEmbed(title="Meme Random", description=f"## {title}")
        embed.set_footer(text=f"{author} - r/{subreddit}")
        embed.set_image(url=url)

        view = ClassicUrlButton(url=postLink, emoji=emoji.get('reddit_icon'), label="Lien vers le post")

        await ctx.send(embed=embed, view=view)

    @meme.subcommand(
        name="template",
        description="Fait une recherche d'une template !"
    )
    async def meme_template(self, ctx: Interaction,
                          template: str = SlashOption(
                              description="Le nom / id de la template !",
                              autocomplete=True,
                              default=None),
                          template_fetch: str = SlashOption(
                              description="Choisir la template par son nom ou par son ID ?",
                              choices=['Par ID', 'Par Nom'],
                              default='Par Nom')
                          ) -> None:

        if template: # IF TEMPLATE
            if template_fetch == "Par Nom":
                template = await get_id_by_name(str(template))

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.memegen.link/templates/{template}") as request:
                    response = await request.json(encoding="utf-8")

            if request.status == 404:  # Api ne trouve pas
                embed = self.ERROR_NOTFOUND

                await send_with_delete_button(ctx, user=ctx.user, embed=embed)
                return
            elif request.status != 200:  # Api ne repond pas
                embed = self.ERROR_API

                await send_with_delete_button(ctx, user=ctx.user, embed=embed)
                return

            id = response.get("id")
            name = response.get("name")
            lines = response.get("lines")
            overlays = response.get("overlays")
            exemple_text = "\n".join(response.get("example").get("text"))
            exemple_url = response.get("example").get("url")

            embed = ModernEmbed(title=f"Meme Template",
                                description=f"## {name}"
                                            f"\n{emoji.get('discord_search')} Template id: **`{id}`**"
                                            f"\n> **›** Lines: `{lines}`"
                                            f"\n> **›** Overlays: `{overlays}`"
                                            f"\n\n**{emoji.get('discord_pencil')} • Exemple:**"
                                            f"\n```{exemple_text}```")

            embed.set_image(url=exemple_url)

            await ctx.send(embed=embed)

        else: # IF NO TEMPLATE

            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.memegen.link/templates") as request:
                    response = await request.json(encoding="utf-8")

            if request.status != 200:  # Api ne repond pas
                embed = self.ERROR_API

                await send_with_delete_button(ctx, user=ctx.user, embed=embed)
                return

            mypages = []
            X = 0
            for template in response:
                X += 1

                id = template.get("id")
                name = template.get("name")
                lines = template.get("lines")
                overlays = template.get("overlays")
                exemple_text = "\n".join(template.get("example").get("text"))
                exemple_url = template.get("example").get("url")

                embed = ModernEmbed(title=f"Meme Template `{X}`",
                                    description=f"## {name}"
                                                f"\n{emoji.get('discord_search')} Template id: **`{id}`**"
                                                f"\n> **›** Lines: `{lines}`"
                                                f"\n> **›** Overlays: `{overlays}`"
                                                f"\n\n**{emoji.get('discord_pencil')} • Exemple:**"
                                                f"\n```{exemple_text}```")

                embed.set_image(url=exemple_url)

                mypages.append(Page(embeds=[embed]))

            paginator = Paginator(
                pages=mypages,
                author_check=True,
                show_disabled=True,
                loop_pages=True,
                timeout=60 * 10,  # 10 minutes
            )

            await paginator.send(ctx)

    @meme.subcommand(
        name="create",
        description="Sois creatif avec ton propre meme !"
    )
    async def meme_create(self, ctx: Interaction,
                          template: str = SlashOption(
                              description="Le nom / id de la template !",
                              autocomplete=True,
                              required=True),
                          text: str = SlashOption(
                              name="texte",
                              description=r"Utilise '\n' pour créer une nouvelle ligne. PS : Laisse vide pour obtenir un menu super chouette.",
                              default=None),
                          template_fetch: str = SlashOption(
                              description="Choisir la template par son nom ou par son ID ?",
                              choices=['Par ID', 'Par Nom'],
                              default='Par Nom'),
                          police: str = SlashOption(
                              description="Choisis la police de ton choix ! (pas ceux qui sont racistes)",
                              autocomplete_callback=autocomplete_get_polices,
                              autocomplete=True,
                              default=None)
                          ) -> None:

        if template_fetch == "Par Nom":
            template = await get_id_by_name(str(template))

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.memegen.link/templates/{template}") as request:
                response = await request.json(encoding="utf-8")

        if request.status == 404:  # Api ne trouve pas
            embed = self.ERROR_NOTFOUND

            await send_with_delete_button(ctx, user=ctx.user, embed=embed)
            return
        elif request.status != 200:  # Api ne repond pas
            embed = self.ERROR_API

            await send_with_delete_button(ctx, user=ctx.user, embed=embed)
            return

        if not text:
            lines = response.get("lines")
            exemple_text = response.get("example").get("text")

            modal = linesTemplateMemeModal(lines=lines, exemple_text=exemple_text)
            await ctx.response.send_modal(modal)

            msg = await ctx.send(embed=LoadingEmbed())

            await modal.wait()
            if not modal.result:
                await send_timeout_msg(msg, title="Meme Create", user=ctx.user)
                return

            text = modal.result

        else:
            msg = await ctx.send(embed=LoadingEmbed())
            text = str(text).split(r"\n")

        data = {
            "style": [
                "string"
            ],
            "text": text,
            "layout": "string",
            "font": str(police) if police else "string",
            "extension": "string",
            "redirect": True
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.memegen.link/templates/{template}", json=data) as response:
                url = str(response.url)

        embed = ModernEmbed(title=f"Meme Create {emoji.get('beta1')}{emoji.get('beta2')}{emoji.get('beta3')}",
                            description=f"> {emoji.get('discord_mention')} Meme créé avec amour par {ctx.user.mention}")

        embed.set_author(name=ctx.user.display_name, icon_url=ctx.user.display_avatar.url)
        embed.set_image(url=url)

        await msg.edit(embed=embed)

    @meme_template.on_autocomplete("template")
    @meme_create.on_autocomplete("template")
    async def autocomplete_get_templates(self, interaction: Interaction, query: str):
        """
        Fonction d'autocomplétion pour les templates.

        Args:
            interaction: L'interaction déclenchée par l'utilisateur.
            query: L'entrée de l'utilisateur (ce qu'il a tapé).

        Returns:
            Une liste filtrée correspondant à l'autocomplétion (IDs ou noms).
        """
        ids, names = await get_template_list()

        options = interaction.data.get('options', [])
        template_fetch = find_option_value(options, 'template_fetch', 'Par Nom')

        if template_fetch == "Par ID":
            list_autocomplete = await autocomplete(input_list=ids, query=query)
        else:
            list_autocomplete = await autocomplete(input_list=names, query=query)

        await interaction.response.send_autocomplete(list_autocomplete)

    @meme.subcommand(
        name="image",
        description="Rajoute des effects drole a ton image !"
    )
    async def meme_image(self, ctx: Interaction,
                         effect: str = SlashOption(
                            description="Choisir l'effet'",
                            choices=['bulle'],
                            required=True),
                         image: nextcord.Attachment = SlashOption(
                            description="L'image a modifier",
                            required=True),
                         ) -> None:

        # Téléchargement de l'image depuis l'attachment
        img_data = await image.read()  # Lire le fichier image
        img = Image.open(io.BytesIO(img_data))  # Charger l'image dans PIL

        # Appliquer l'effet "bulle" si sélectionné
        if effect == "bulle":
            img = add_cutout_effect(img)  # Appliquer l'effet bulle à l'image

        # Sauvegarde l'image modifiée dans un buffer
        buffer = io.BytesIO()
        img.save(buffer, "PNG")
        buffer.seek(0)  # Revenir au début du buffer pour l'envoyer

        # Envoyer l'image modifiée à nextcord
        await ctx.send(file=nextcord.File(fp=buffer, filename="image_modifiee.png"))


def setup(bot):
    bot.add_cog(Meme(bot))
