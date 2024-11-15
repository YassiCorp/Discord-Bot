import json
import platform
import random
from datetime import datetime

from discord.ext.pages import Page
from mediawiki import MediaWiki

from config import config
import discord
from discord.ext import commands, pages

from emojis import emoji
from libs import utils
from libs.embed import ModernEmbed, ErrorEmbed
from libs.message import default_page_buttons
from libs.redis_server import redisServer
from libs.utils import TripleUrlButton, DoubleUrlButton, mediawiki_to_discord

guilds = config.BOT.GUILDS

class FeedbackForm(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(title="Feeedback", timeout=60*3)

        self.feedback = discord.ui.InputText(label="What do you think about this bot?",
                                             style=discord.InputTextStyle.long,
                                             placeholder="Type your answer here...",
                                             required=True, max_length=256)

        self.add_item(self.feedback)

    async def callback(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.answer = str(self.feedback.value)
        self.stop()

class General(commands.Cog, name="general"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.wiki = MediaWiki(lang="fr")
        self.redis_cache = redisServer

    # Message ctx menu command
    @discord.message_command()
    async def remove_spoilers(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        """
        Removes the spoilers from the message. This command requires the MESSAGE_CONTENT intent to work properly.

        :param interaction: The application command interaction.
        :param message: The message that is being interacted with.
        """
        spoiler_attachment = None
        for attachment in message.attachments:
            if attachment.is_spoiler():
                spoiler_attachment = attachment
                break
        embed = discord.Embed(
            title="Message without spoilers",
            description=message.content.replace("||", ""),
            color=0xBEBEFE,
        )
        if spoiler_attachment is not None:
            embed.set_image(url=spoiler_attachment.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.slash_command(
        name="help", description="List all commands the bot has loaded."
    )
    async def help(self, ctx: discord.ApplicationContext) -> None:
        prefix = ">"
        embed = ModernEmbed(
            title="Help", description="List of available commands:"
        )
        for i in self.bot.cogs:
            if i == "owner" and not (await self.bot.is_owner(ctx.author)):
                continue
            cog = self.bot.get_cog(i.lower())
            commands = cog.get_commands()
            data = []
            for command in commands:
                description = command.description.partition("\n")[0]
                data.append(f"{prefix}{command.name} - {description}")
            help_text = "\n".join(data)
            embed.add_field(
                name=i.capitalize(), value=f"```{help_text}```", inline=False
            )
        await ctx.respond(embed=embed)

    @discord.slash_command(
        name="botinfo",
        description="Get some useful (or not) information about the bot.",
    )
    async def botinfo(self, ctx: discord.ApplicationContext) -> None:
        """
        Get some useful (or not) information about the bot.

        :param ctx: The hybrid command ctx.
        """
        embed = ModernEmbed(
            title=f"Bot Info / About Me\n",
            description=f"> {emoji.chika_thumbsup} Enfin quelqu'un qui s'intéresse a moi ^^\n"
                        f"\n> Voici Mes Informations {emoji.discord_mention} {ctx.user.mention} (je suis créé par <@626833155281911849> avec amour)\n"
                        f"\n**{emoji.square_owner_ship} • Ma carrière:**")

        embed.add_field(name=r"C:\Créé par>_",
                        value=f"{emoji.discord_mention} <@626833155281911849> | YassiGame")

        embed.add_field(name=r"C:\Bot Version>_",
                        value=f"{emoji.discord_support} {config.BOT.VERSION}")

        embed.add_field(name=r"C:\Language de prog>_",
                        value=f"{emoji.discord_heart} Python {emoji.Python}")

        embed.add_field(name=r"C:\Phython Vers>_",
                        value=f"{emoji.discord_pencil} V{platform.python_version()}")

        embed.add_field(name=r"C:\Py-Cord API>_",
                        value=f"{emoji.discord_logo} V{discord.__version__}")

        embed.add_field(name=r"C:\Créé le>_",
                        value=f"{emoji.discord_activity} 30/12/2020")

        embed.add_field(name=r"C:\Langue principale>_",
                        value=f"{emoji.discord_compass} Français 🇫🇷")

        embed.add_field(name=r"C:\Humour>_",
                        value=f"{emoji.discord_lock} Éclaté sa mère")

        embed.add_field(name=r"C:\Lien d'invite>_",
                        value=f"{emoji.discord_bot} JAMAIS")

        await ctx.respond(embed=embed)

    @discord.slash_command(
        name="serverinfo",
        description="Get some useful (or not) information about the server.",
    )
    async def serverinfo(self, ctx: discord.ApplicationContext) -> None:
        """
        Get some useful (or not) information about the server.

        :param ctx: The hybrid command ctx.
        """
        roles = [role.name for role in ctx.guild.roles]
        num_roles = len(roles)
        if num_roles > 50:
            roles = roles[:50]
            roles.append(f">>>> Displaying [50/{num_roles}] Roles")
        roles = ", ".join(roles)

        embed = ModernEmbed(
            title="**Server Name:**", description=f"{ctx.guild}"
        )
        if ctx.guild.icon is not None:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.add_field(name="Server ID", value=str(ctx.guild.id))
        embed.add_field(name="Member Count", value=str(ctx.guild.member_count))
        embed.add_field(
            name="Text/Voice Channels", value=f"{len(ctx.guild.channels)}"
        )
        embed.add_field(name=f"Roles ({len(ctx.guild.roles)})", value=roles)
        embed.set_footer(text=f"Created at: {ctx.guild.created_at}")
        await ctx.respond(embed=embed)

    @discord.slash_command(
        name="ping",
        description="Check if the bot is alive."
    )
    async def ping(self, ctx: discord.ApplicationContext) -> None:
        """
        Vérifie si le bot est en ligne.

        :param ctx: Le contexte de la commande.
        """
        ping = round(self.bot.latency * 1000)

        gifs = [
            "https://media.tenor.com/0zPtv37IWy8AAAAS/cats-ping-pong.gif",
            "https://media1.tenor.com/m/7TXsIVm7G6QAAAAC/ping-pong.gif",
            "https://media.tenor.com/OtI0T4RCUM0AAAAd/pingpong-table-tennis.gif",
            "https://media1.tenor.com/m/oOVpa7dE5osAAAAC/table-tennis-ping-pong.gif",
            "https://media.tenor.com/g44lccSjD6sAAAAS/jesse-and.gif"
        ]

        user_id = ctx.user.id

        # Récupérer les données de l'utilisateur depuis Redis
        data = self.redis_cache.get(f"ping_user:{user_id}")
        if data is None:
            # Si aucune donnée n'existe, initialiser le compteur à 1
            user_data = {'count': 1}
        else:
            user_data = json.loads(data)
            user_data['count'] += 1

        # Enregistrer les données mises à jour dans Redis avec une expiration de 60 secondes
        self.redis_cache.set(
            f"ping_user:{user_id}",
            json.dumps(user_data),
            ex=60*2  # Le compteur sera réinitialisé après 60 secondes d'inactivité
        )

        condition = user_data['count'] >= 5
        ping_funfacts = [
            "Wow, tu essayes de battre le record du monde de ping ?",
            "Ping surchargé détecté ! Veuillez patienter pendant que nous refroidissons les serveurs.",
            "*Ping.... Pong*. Tu connais la vanne ??? *ah...* c'est naze ?!",
            "Le ping a besoin d'une pause, tout comme toi !",
            "Arrête de m'appeler, je t'avais dit que c'était fini entre nous !",
            "Tu as vu le gif des chats cute qui jouent au ping pong ?"
        ]

        embed = ModernEmbed(
            title="Ping ~~Pong~~",
            description=(
                f"> {emoji.discord_mention} {ctx.user.mention} mon ping est de **{ping}ms** {utils.emoji_latency(ping)}"
                f"\n\n{f'-# {random.choice(ping_funfacts)}' if condition else ''}"
            ),
        )
        embed.set_thumbnail(url=random.choice(gifs))
        await ctx.respond(embed=embed)

    @discord.slash_command(
        name="socials",
        description="Avoir les réseaux sociaux de la YassiCorp...",
    )
    async def socials(self, ctx: discord.ApplicationContext) -> None:

        embed = ModernEmbed(
            title=f"Socials | {emoji.yassicorp_icon} YassiCorp",
            description=f"\n> {emoji.discord_mention} {ctx.user.mention} voila les réseaux sociaux de la **YassiCorp** (Un serveur communitaire de <@626833155281911849>) {emoji.chika_thumbsup}")

        await ctx.respond(embed=embed, view=TripleUrlButton(label1="Twitter", url1="https://twitter.com/YassiCorp",
                                                         emoji1=emoji.twitter_pixel_logo, label2="Reddit",
                                                         url2="https://www.reddit.com/r/YassiCrop",
                                                         emoji2=emoji.reddit_pixel_logo, label3="YouTube",
                                                         url3="https://www.youtube.com/channel/UCuD8K-XYRKaxYnpcwGrcO9Q",
                                                         emoji3=emoji.youtube_pixel_logo))

    @discord.slash_command(
        name="todolist",
        description="Avoir la liste de feature qui seront ajoutés prochainement..."
    )
    async def todolist(self, ctx: discord.ApplicationContext) -> None:

        embed = ModernEmbed(
            title=f"To Do List | Trello",
            description=f"\n> {emoji.discord_mention} {ctx.user.mention} voila ma page To Do List sur **Trello**, maintenant tu pourras suivre toute les nouvelles features qui vont etre ajoutés {emoji.chika_thumbsup}")

        await ctx.respond(embed=embed, view=DoubleUrlButton(label1=f"Main To Do List",
                                                         url1="https://trello.com/b/f6EMQGCn/%F0%9F%94%AE-yassicorp-bot-tasks",
                                                         emoji1=emoji.discord_heart, label2="Bugs To Do List",
                                                         url2="https://trello.com/b/rrFFQuOC/%F0%9F%8E%AF-yassicorp-bot-bugs",
                                                         emoji2=emoji.discord_cross))

    @discord.slash_command(
        name="feedback", description="Submit a feedback for the owners of the bot"
    )
    async def feedback(self, interaction: discord.ApplicationContext) -> None:

        feedback_form = FeedbackForm()
        await interaction.response.send_modal(feedback_form)

        await feedback_form.wait()
        interaction = feedback_form.interaction
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Thank you for your feedback, the owners have been notified about it.",
                color=0xBEBEFE,
            )
        )

        app_owner = (await self.bot.application_info()).owner
        await app_owner.send(
            embed=discord.Embed(
                title="New Feedback",
                description=f"{interaction.user} (<@{interaction.user.id}>) has submitted a new feedback:\n```\n{feedback_form.answer}\n```",
                color=0xBEBEFE,
            )
        )

    @discord.command(
        name="wikipedia",
        description="Faire une recherche wikipedia",
        guild_ids=guilds
    )
    async def wikipedia(self, ctx: discord.ApplicationContext,
                      search: str = discord.Option(required=True, description="Ce que tu veux rechercher (certes je suis un génie, mais je ne suis pas Akinator)"),
                      results: int = discord.Option(int, description="Combien de résultats tu veux, le maximum est 10 (on est radin mais à moitié)", min_value=1, max_value=10, default=3)
                      ) -> None:

        await ctx.defer()

        listResults = self.wiki.search(search, results=results)
        listPages = [self.wiki.page(r) for r in listResults] # create a list of the results

        if not listPages:
            embed = ErrorEmbed(title="Wikipedia",
                               description=f"{emoji.sans} Aucun résultat n'a été trouvé pour la recherche suivante : `{search}`.")

            await ctx.respond(embed=embed)
            return

        mypages = []
        for page in listPages:
            embed = ModernEmbed(title=f"Wikipedia | **`{search}`**",
                                description=f"# __{page.title}__"
                                            f"\n\n {mediawiki_to_discord(page.summarize(chars=695))}")

            if page.images:
                embed.set_thumbnail(url=page.images[0])

            view = discord.ui.View(
                discord.ui.Button(label="Lien", emoji=emoji.get("icon_world"), row=1, url=page.url),
            )

            mypages.append(Page(embeds=[embed], custom_view=view))

        paginator = pages.Paginator(
            pages=mypages,
            author_check=True,
            show_disabled=True,
            show_indicator=True,
            use_default_buttons=False,
            custom_buttons=default_page_buttons,
            loop_pages=True,
            timeout=60*5, # 5 minutes
        )
        await paginator.respond(interaction=ctx.interaction)


def setup(bot) -> None:
    bot.add_cog(General(bot))
