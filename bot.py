import nextcord
import aiohttp
import random
import platform
import os

from nextcord import Interaction
from nextcord.ext import tasks, commands
from rich.panel import Panel
from rich.text import Text

import emojis
import exceptions
from config import config
from libs import logger
from libs.embed import ErrorEmbed
from libs.logger import get_rich_rendered_object

log = logger.ConsoleLogger(log_name="bot", log_color="blue")

class BOT(commands.Bot):
    def __init__(self):
        self.config = config
        super().__init__(intents=nextcord.Intents.all(), help_command=None)
        self.emoji = emojis.emoji

    #  ____________________________________
    # |  ________________________________  |
    # | | Main Code:                     | |
    # | |  → "The main code for the bot" | |
    # | |________________________________| |
    # |____________________________________|
    async def on_ready(self) -> None:
        #await self.sync_commands(force=False, guild_ids=[904344208528257105])

        guilds = [self.get_guild(guild) for guild in config.BOT.EMOJI_GUILD]
        log.info("Synchronisation des emojis...")
        await self.emoji.update_from_guilds(guilds)
        log.success(f"Emojis synchronisés avec succès. Il y en a {len(self.emoji.get_all())} !")

        log.success(f"Bot lancé avec succès !")
        info = (f"✨ » Connecté en tant que [blue]{self.user.name}[/]\n"
                f"👾 » Nextcord API version: [blue]{nextcord.__version__}[/]\n"
                f"🐍 » Version Python: [blue]{platform.python_version()}[/]\n"
                f"🖥️ » Lancé sur: {platform.system()} [blue]{platform.release()}[/] ({os.name})")
        log.info(Text.from_ansi(get_rich_rendered_object(Panel(info, title="🔎 Informations", expand=False)).replace("\n", "\n             "))) # Code pour afficher les informations
        self.status_task.start()
        log.info("Lancement de la tâche Status...")
        if self.config.UPTIME_PUSH.ACTIVATE:
            self.uptime_task.start()
            log.info("Lancement de la tâche Uptime Push...")


    @tasks.loop(minutes=1.0)  # <--- Tâche : changement automatique du statut.
    async def status_task(self) -> None:
        await self.change_presence(
            activity=nextcord.Activity(type=nextcord.ActivityType.listening, name=random.choice(self.config.BOT.STATUS))  # Remplacement de 'discord.Activity' par 'nextcord.Activity'
        )

    @status_task.before_loop
    async def before_status_task(self) -> None:
        """
        Avant de démarrer la tâche de changement de statut, on s'assure que le bot est prêt
        """
        await self.wait_until_ready()
        log.success("Tâche Status démarrée !")

    @tasks.loop(minutes=1.0)  # <--- Tâche : push uptime automatique.
    async def uptime_task(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.config.UPTIME_PUSH.URL):
                pass

    @uptime_task.before_loop
    async def before_uptime_task(self) -> None:  # Correction du nom de la méthode
        """
        Avant de démarrer la tâche de push uptime, on s'assure que le bot est prêt
        """
        await self.wait_until_ready()
        log.success("Tâche Uptime démarrée !")

    async def on_message(self, message: nextcord.Message) -> None:
        """
        Le code dans cet événement est exécuté chaque fois que quelqu'un envoie un message, avec ou sans le préfixe

        :param message: Le message qui a été envoyé.
        """
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_application_command_completion(self, interaction: Interaction) -> None:
        """
        Le code dans cet événement est exécuté chaque fois qu'une commande normale a été *exécutée avec succès*.

        :param interaction: L'interaction de la commande qui a été exécutée.
        """
        full_command_name = interaction.application_command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if interaction.guild is not None:
            log.info(
                f"Commande {executed_command} exécutée dans {interaction.guild.name} (ID: {interaction.guild.id}) par {interaction.user} (ID: {interaction.user.id})"
            )
        else:
            log.info(
                f"Commande {executed_command} exécutée par {interaction.user} (ID: {interaction.user.id}) en DM"
            )

    


    async def load_cog(self, path: str) -> int:
        errorInt = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    extension = file[:-3]
                    name = path.replace("/", ".").replace("\\", ".")[:-3]
                    try:
                        self.load_extension(f"{name}")
                    except Exception as e:
                        log.error(f"{e}")
                        errorInt += 1
                    else:
                        log.info(f"Extension '{extension}' chargée")
        return errorInt

    async def load_cogs(self) -> None:
        errorInt = 0

        log.warning("⟳ Chargement des modules")
        with log.status("[bold green]Chargement des modules de guilde..."):
            errorInt += await self.load_cog("cogs")

        if errorInt == 0:
            log.success("✔ Chargement des modules terminé avec succès")
        else:
            log.warning(f"‼ Chargement des modules terminé avec [bold underline white]{errorInt} erreur(s)[/]")
