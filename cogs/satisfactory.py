import asyncio
import aiohttp
import nextcord
import orjson
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from lxml import etree
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from config import config
from emojis import emoji
from libs.embed import ModernEmbed, LoadingEmbed, ErrorEmbed
from libs.message import send_with_delete_button
from libs.paginator import Page, Paginator
from libs.redis_server import redisServer
from libs.utils import ClassicUrlButton, mediawiki_to_discord, find_option_value, autocomplete
from mediawiki import MediaWiki

SATISFACTORY_CALCULATOR_BASEURL = "https://satisfactory-calculator.com"
SATISFACTORY_WIKI_BASEURL = "https://satisfactory.wiki.gg/api.php"

CACHE_DURATION = 3600
GUILDS = config.BOT.GUILDS

class SatisfactoryCog(commands.Cog, name="satisfactory"):
    def __init__(self, bot):
        self.bot: nextcord.Client = bot
        self.mc_wiki = MediaWiki(url=SATISFACTORY_WIKI_BASEURL)
        self.redis_cache = redisServer
        
    async def fetch(self, session: ClientSession, url: str) -> str:
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            print(f"Erreur lors de la récupération de {url} : {e}")
            return ""

    async def scrape(self, funcParse, urls: list):
        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            tasks = [asyncio.create_task(self.fetch(session, url)) for url in urls]
            html_contents = await asyncio.gather(*tasks)
            results = [funcParse(html) for html in html_contents]
            return results[0]

    def parseList(self, html: str):
        if not html:
            return []

        # Définir les sélecteurs CSS
        ELEMENT_SELECTOR = (
            ".APPLICATION_ENV_production.h-100 "
            "body.d-flex.flex-column.h-100 "
            "main.py-3.flex-fill "
            "div.container-fluid "
            "div.row "
            "div.col-6.col-sm-4.col-md-3.d-flex.flex-column"
        )

        # Sélecteurs relatifs pour l'image, le texte et l'URL à l'intérieur de chaque élément ciblé
        IMAGE_SELECTOR = "div.card-body a img"
        TEXT_SELECTOR = "div.card-body h6.m-0 a strong"
        URL_SELECTOR = "div.card-body a"

        soup = BeautifulSoup(html, 'lxml')  # Ou utilisez 'html.parser' si nécessaire
        # Trouver tous les éléments correspondant au sélecteur principal
        elements = soup.select(ELEMENT_SELECTOR)
        extracted_data = []

        for elem in elements:
            # Extraire l'URL de l'image
            img_tag = elem.select_one(IMAGE_SELECTOR)
            img_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else 'Image non trouvée'

            # Extraire le texte
            text_tag = elem.select_one(TEXT_SELECTOR)
            text = text_tag.get_text(strip=True) if text_tag else 'Texte non trouvé'

            # Extraire l'URL
            url_tag = elem.select_one(URL_SELECTOR)
            url = url_tag['href'] if url_tag and url_tag.has_attr('href') else 'URL non trouvée'

            extracted_data.append({
                'image_url': img_url,
                'name': text,
                'url': SATISFACTORY_CALCULATOR_BASEURL + f"{url}"
            })

        return extracted_data

    def parseObjectInfo(self, html: str):
        if not html:
            return {}
        parser = etree.HTMLParser()
        tree = etree.fromstring(html, parser)

        # Définir les XPaths
        DESCRIPTION_XPATH = "/html/body/main/div[2]/div[2]/div/div/div/div[1]/div/blockquote/em/p/text()"
        CATEGORY_XPATH = "/html/body/main/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div[1]/ul[1]/li/span[2]/strong/text()"
        LIST_XPATH = "/html/body/main/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div[1]//ul[contains(@class, 'list-group-flush')]"
        IMAGE_XPATH = "/html/body/main/div[2]/div[2]/div/div/img/@src"

        # Initialiser les champs avec des valeurs par défaut
        extracted_data = {
            'description': "Description non trouvée.",
            'image_url': None,
            'category': None,
            'slots': None,
            'stack_size': None,
            'crafting_time': None,
            'resource_sink_points': None,
            'pieces_made': None,
            'power_used': None,
            'width': None,
            'length': None,
            'height': None,
            'output': None,
            'input': None,
            'p_values': [],
            'a_hrefs': []
        }

        # Extraire la description
        description_result = tree.xpath(DESCRIPTION_XPATH)
        if description_result:
            extracted_data['description'] = description_result[0].strip()

        # Extraire la catégorie
        category_result = tree.xpath(CATEGORY_XPATH)
        if category_result:
            extracted_data['category'] = category_result[0].strip()


        # Définir une correspondance entre les labels et les champs (en minuscules)
        label_to_field = {
            'slots': 'slots',
            'stack size': 'stack_size',
            'crafting time': 'crafting_time',
            'pieces made': 'pieces_made',
            'resource sink points': 'resource_sink_points',
            'power used': 'power_used',
            'width': 'width',
            'length': 'length',
            'height': 'height',
            'output': 'output',
            'input': 'input'
            # 'category': 'category',  # Optionnel, déjà extrait
        }

        # Extraire tous les <ul> contenant les champs dynamiques
        list_results = tree.xpath(LIST_XPATH)
        if list_results:
            for ul in list_results:
                li_elements = ul.xpath(".//li")
                for li in li_elements:
                    # Extraire le label et la valeur
                    label_texts = li.xpath(".//span[1]//text()")
                    value_texts = li.xpath(".//span[@class='float-right']/strong/text()")
                    if label_texts and value_texts:
                        # Joindre tous les textes du label
                        label_clean = ''.join(label_texts).strip().rstrip(':').lower()
                        value_clean = ''.join(value_texts).strip()
                        # Débogage : afficher le label et la valeur extraits
                        # print(f"Label: '{label_clean}', Value: '{value_clean}'")
                        # Mapper le label au champ
                        if label_clean in label_to_field:
                            field_name = label_to_field[label_clean]
                            extracted_data[field_name] = value_clean

        # Gestion des cas où 'input' est absent et 'output' est à une position différente
        if not extracted_data['input'] and not extracted_data['output']:
            # Essayer d'extraire 'output' à partir d'une autre position
            output_alternate_result = tree.xpath(
                "/html/body/main/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div[1]/ul[4]/li[1]/span[2]/strong/text()")
            if output_alternate_result:
                extracted_data['output'] = output_alternate_result[0].strip()

        # Extraire les valeurs <p> et les URLs des <a> dans la liste spécifiée
        LIST_DETAILS_XPATH = "/html/body/main/div[2]/div[2]/div/div/div/div[2]/div[1]/div/div[2]/div/div[2]/ul"
        list_details = tree.xpath(LIST_DETAILS_XPATH)
        if list_details:
            list_element = list_details[0]
            # Extraire toutes les balises <p>
            p_tags = list_element.xpath(".//p/text()")
            extracted_data['p_values'] = [p.strip() for p in p_tags if p.strip()]

            # Extraire toutes les balises <a> et leurs href
            a_tags = list_element.xpath(".//a[@href]")
            extracted_data['a_hrefs'] = [{'text': a.text.strip(), 'href': SATISFACTORY_CALCULATOR_BASEURL + a.get('href')} for a in a_tags if
                                         a.text and a.get('href')]

        # Extraire l'image supplémentaire
        image_result = tree.xpath(IMAGE_XPATH)
        if image_result:
            extracted_data['image_url'] = image_result[0].strip()

        return extracted_data

    def getURL(self, type: str, lang: str = "en"):
        return [f"{SATISFACTORY_CALCULATOR_BASEURL}/{lang}/{type}"]

    async def getList(self, type: str, lang="en"):
        url = self.getURL(type=type, lang=lang)
        cached_extracted_data = self.redis_cache.get(f"satisfactory.{lang}.{type}")
        if cached_extracted_data:
            extracted_data = orjson.loads(cached_extracted_data)
            return extracted_data

        extracted_data = await self.scrape(self.parseList, urls=url)
        self.redis_cache.set(f"satisfactory.{lang}.{type}", value=orjson.dumps(extracted_data), ex=CACHE_DURATION)
        return extracted_data

    async def getListNames(self, type: str, lang="en"):
        cached_names = self.redis_cache.get(f"satisfactory.{lang}.{type}.names")
        if cached_names:
            names = orjson.loads(cached_names)
            return names

        extracted_data = await self.getList(type=type, lang=lang)
        names = [item['name'] for item in extracted_data if 'name' in item]
        self.redis_cache.set(f"satisfactory.{lang}.{type}.names", value=orjson.dumps(names), ex=CACHE_DURATION)
        return names

    async def getObjectLink(self, type: str, query: str, lang="en"):
        extracted_data = await self.getList(type=type, lang=lang)
        urls = [item['url'] for item in extracted_data if item['name'] == query]
        return urls or None

    async def getObjectEmbed(self, type: str, query: str, lang="en"):
        url = await self.getObjectLink(query=query, type=type, lang=lang)
        data = await self.scrape(self.parseObjectInfo, urls=url)

        description = data.get('description')
        image_url = data.get('image_url')
        category = data.get('category')
        slots = data.get('slots')
        stack_size = data.get('stack_size')
        crafting_time = data.get('crafting_time')
        resource_sink_points = data.get('resource_sink_points')
        pieces_made = data.get('pieces_made')
        power_used = data.get('power_used')
        width = data.get('width')
        length = data.get('length')
        height = data.get('height')
        output = data.get('output')
        input = data.get('input')
        p_values = data.get('p_values', None)
        a_hrefs = data.get('a_hrefs', None)

        embed = ModernEmbed(title="Satisfactory Buildings")

        description = (f"# [{query}]({url[0]})"
                       f"\n\n## __Description:__"
                       f"\n> {description}")

        if p_values:
            description += f"\n## __Ingredients:__"
            for p, a in zip(p_values, a_hrefs):
                description += f"\n- **{p}** [{a.get('text')}]({a.get('href')})"


        if category:
            embed.add_field(name=f"{emoji.get('boxarchivesolid')} Catégorie",
                            value=category)
        if slots:
            embed.add_field(name=f"{emoji.get('boxarchivesolid')} Emplacements",
                            value=slots)
        if stack_size:
            embed.add_field(name=f"{emoji.get('boxesstackedsolid')} Stack",
                            value=stack_size)
        if crafting_time:
            embed.add_field(name=f"{emoji.get('stopwatchsolid')} Temps de fabrication ",
                            value=crafting_time)
        if pieces_made:
            embed.add_field(name=f"{emoji.get('dollysolid')} Pièces fabriquées",
                            value=pieces_made)
        if resource_sink_points:
            embed.add_field(name=f"{emoji.get('moneybillsolid')} Resource Sink Points",
                            value=resource_sink_points)
        if power_used:
            embed.add_field(name=f"{emoji.get('boltsolid')} Puissance utilisée",
                            value=power_used)
        if width:
            embed.add_field(name=f"{emoji.get('rulerhorizontalsolid')} Largeur",
                            value=width)
        if length:
            embed.add_field(name=f"{emoji.get('rulersolid')} Longueur",
                            value=length)
        if height:
            embed.add_field(name=f"{emoji.get('rulerverticalsolid')} Hauteur",
                            value=height)
        if input:
            embed.add_field(name=f"{emoji.get('plugsolid')} Entrée",
                            value=input)
        if output:
            embed.add_field(name=f"{emoji.get('plugsolid')} Sortie",
                            value=output)

        if embed.fields: # Ajouter le petit titre avant les fields
            description += f"\n## __Information:__"

        if image_url:
            embed.set_thumbnail(url=image_url)

        embed.set_description(description)
        return embed

    async def getObjectAutocomplete(self, type: str, interaction: Interaction, query: str):
        current_query = query.lower()
        options = interaction.data.get('options', [])
        lang = find_option_value(options, 'lang', 'en')

        # Obtenir la liste des noms de bâtiments
        buildings = await self.getListNames(type=type, lang=lang)

        list_autocomplete = await autocomplete(input_list=buildings, query=current_query)
        await interaction.response.send_autocomplete(list_autocomplete)

    async def generic_command(self, ctx: Interaction, name: str, lang: str, object_type: str):
        msg = await ctx.send(embed=LoadingEmbed())
        # Ajouter un check pour voir si l'objet existe
        if name.lower() in list(map(lambda x: x.lower(), await self.getListNames(object_type, lang="en"))):
            embed = await self.getObjectEmbed(query=name, type=object_type, lang=lang)
        else:
            embed = ErrorEmbed(title="Satisfactory - Nom invalide", description=f"{emoji.get('sans')} Vous avez saisi un nom invalide veuillez reverifier le nom")
        await msg.edit(embed=embed)

    async def generic_autocomplete(self, interaction: Interaction, query: str, object_type: str):
        await self.getObjectAutocomplete(type=object_type, interaction=interaction, query=query)


    @nextcord.slash_command(
        name="satisfactory",
        description="Toute les commandes en rapport avec Satisfactory...",
        guild_ids=GUILDS
    )
    async def satisfactory(self, ctx: Interaction) -> None:
        pass

    @satisfactory.subcommand(
        name="tools",
        description="Satisfactory | La liste d'outils de Satisfactory",
    )
    async def tools(self, ctx: Interaction) -> None:
        _title = "Satisfactory Tools"

        embed0 = ModernEmbed(title=_title,
                            description="> Dans ce menu vous auriez la liste des outils de Satisfactory que je juges pratique pour vos futurs projets d'ingenieur",
        )

        embed1 = ModernEmbed(title=_title,
                             description="")

    @satisfactory.subcommand(
        name="wiki",
        description="Satisfactory | Chercher dans le wiki",
    )
    async def wiki(self, ctx: Interaction,
                      search: str = SlashOption(required=True, description="L'objet ou items dans satisfactory que tu veux chercher"),
                      results: int = SlashOption(description="Combien de résultats tu veux, le clients est roi (le max est 10)", min_value=1, max_value=10, default=3)
                      ) -> None:

        msg = await ctx.send(embed=LoadingEmbed())

        listResults = self.mc_wiki.search(search, results=results)
        listPages = [self.mc_wiki.page(r) for r in listResults] # create a list of the results

        if not listPages:
            embed = ErrorEmbed(title="Satisfactory Wiki",
                               description=f"{emoji.get('sans')} Aucun résultat n'a été trouvé pour la recherche suivante : `{search}`.")

            await msg.edit(embed=embed)
            return

        mypages = []
        for page in listPages:
            embed = ModernEmbed(title=f"Satisfactory Wiki | **`{search}`**",
                                description=f"# __{page.title}__"
                                            f"\n\n {mediawiki_to_discord(page.summarize(chars=695))}")

            if page.images:
                embed.set_thumbnail(url=page.images[0])

            class view(nextcord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(
                        nextcord.ui.Button(label="Lien", emoji=emoji.get("icon_world"), row=1, url=page.url))

            mypages.append(Page(embeds=[embed], view=view()))

        paginator = Paginator(
            pages=mypages,
            author_check=True,
            loop_pages=True,
            show_disabled=True,
            timeout=60 * 5,  # 5 minutes
        )
        await paginator.send(msg.channel)

    @satisfactory.subcommand(
        name="buildings",
        description=f"Satisfactory | La liste d'outils de Satisfactory pour buildings",
    )
    async def buildings(self, interaction: Interaction,
                      name: str = SlashOption(
                          description="Le nom du building !",
                          autocomplete=True,
                          required=True),
                      lang: str = SlashOption(
                          description="La langue",
                          default="en",
                          choices=["en", "fr"],
                          required=False)) -> None:
        await self.generic_command(interaction, name, lang, "buildings")
    @buildings.on_autocomplete("name")
    async def buildings_autocomplete(self, interaction: Interaction, query: str):
        await self.generic_autocomplete(interaction, query, "buildings")

    @satisfactory.subcommand(
        name="architecture",
        description=f"Satisfactory | La liste d'outils de Satisfactory pour architecture",
    )
    async def architecture(self, interaction: Interaction,
                        name: str = SlashOption(
                            description="Le nom du architecture !",
                            autocomplete=True,
                            required=True),
                        lang: str = SlashOption(
                            description="La langue",
                            default="en",
                            choices=["en", "fr"],
                            required=False)) -> None:
        await self.generic_command(interaction, name, lang, "architecture")
    @architecture.on_autocomplete("name")
    async def architecture_autocomplete(self, interaction: Interaction, query: str):
        await self.generic_autocomplete(interaction, query, "architecture")

    @satisfactory.subcommand(
        name="structures",
        description=f"Satisfactory | La liste d'outils de Satisfactory pour structures",
    )
    async def structures(self, interaction: Interaction,
                        name: str = SlashOption(
                            description="Le nom du structures !",
                            autocomplete=True,
                            required=True),
                        lang: str = SlashOption(
                            description="La langue",
                            default="en",
                            choices=["en", "fr"],
                            required=False)) -> None:
        await self.generic_command(interaction, name, lang, "structures")

    @structures.on_autocomplete("name")
    async def structures_autocomplete(self, interaction: Interaction, query: str):
        await self.generic_autocomplete(interaction, query, "structures")

    @satisfactory.subcommand(
        name="items",
        description=f"Satisfactory | La liste d'outils de Satisfactory pour items",
    )
    async def items(self, interaction: Interaction,
                        name: str = SlashOption(
                            description="Le nom du items !",
                            autocomplete=True,
                            required=True),
                        lang: str = SlashOption(
                            description="La langue",
                            default="en",
                            choices=["en", "fr"],
                            required=False)) -> None:
        await self.generic_command(interaction, name, lang, "items")

    @items.on_autocomplete("name")
    async def items_autocomplete(self, interaction: Interaction, query: str):
        await self.generic_autocomplete(interaction, query, "items")

    @satisfactory.subcommand(
        name="tools",
        description=f"Satisfactory | La liste d'outils de Satisfactory pour tools",
    )
    async def tools(self, interaction: Interaction,
                        name: str = SlashOption(
                            description="Le nom du building !",
                            autocomplete=True,
                            required=True),
                        lang: str = SlashOption(
                            description="La langue",
                            default="en",
                            choices=["en", "fr"],
                            required=False)) -> None:
        await self.generic_command(interaction, name, lang, "tools")

    @tools.on_autocomplete("name")
    async def tools_autocomplete(self, interaction: Interaction, query: str):
        await self.generic_autocomplete(interaction, query, "tools")



def setup(bot):
    bot.add_cog(SatisfactoryCog(bot))