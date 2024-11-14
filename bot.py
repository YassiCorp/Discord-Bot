import discord, aiohttp, random, platform, os
from discord import Interaction
from discord.ext import tasks, commands
from discord.ext.commands import Context
from rich.panel import Panel
from rich.text import Text

import emojis
from config import config
from libs import logger
from libs.embed import ErrorEmbed
from libs.logger import get_rich_rendered_object

log = logger.ConsoleLogger(log_name="bot", log_color="blue")

class BOT(commands.Bot):
    def __init__(self):
        self.config = config
        super().__init__(intents=discord.Intents.all())
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
        log.info("Synchronisation of the emojis...")
        await self.emoji.update_from_guilds(guilds)
        self.emoji.create_emoji_classes()
        log.success(f"Emojis sync successfully. They are {len(self.emoji.get_all())} emojis !")

        log.success(f"Bot launched successfully !")
        info = (f"✨ » Connected as [blue]{self.user.name}[/]\n"
                f"👾 » discord API version: [blue]{discord.__version__}[/]\n"
                f"🐍 » Python version: [blue]{platform.python_version()}[/]\n"
                f"🖥️ » Launched in: {platform.system()} [blue]{platform.release()}[/] ({os.name})")
        log.info(Text.from_ansi(get_rich_rendered_object(Panel(info, title="🔎 Informations", expand=False)).replace("\n", "\n             "))) # shit code made with ass to render a rich panel just for your eyes
        self.status_task.start(), log.info(f"Launching Task Status...")
        if self.config.UPTIME_PUSH.ACTIVATE:
            self.uptime_task.start(), log.info(f"Launching Uptime Push...")


    @tasks.loop(minutes=1.0)  # <--- Task: automatic status changer.
    async def status_task(self) -> None:
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=random.choice(self.config.BOT.STATUS)))

    @status_task.before_loop
    async def before_status_task(self) -> None:
        """
        Before starting the status changing task, we make sure the bot is ready
        """
        await self.wait_until_ready()
        log.success("Task Status UP !")

    @tasks.loop(minutes=1.0)  # <--- Task: automatic uptime push.
    async def uptime_task(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.config.UPTIME_PUSH.URL):
                pass

    @uptime_task.before_loop
    async def before_status_task(self) -> None:
        """
        Before starting the uptime task, we make sure the bot is ready
        """
        await self.wait_until_ready()
        log.success("Uptime Task UP !")

    async def on_message(self, message: discord.Message) -> None:
        """
        The code in this event is executed every time someone sends a message, with or without the prefix

        :param message: The message that was sent.
        """
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_application_command_completion(self, interaction: discord.ApplicationContext) -> None:
        """
        The code in this event is executed every time a normal command has been *successfully* executed.

        :param interaction: The interaction of the command that has been executed.
        """
        full_command_name = interaction.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        if interaction.guild is not None:
            log.info(
                f"Executed {executed_command} command in {interaction.guild.name} (ID: {interaction.guild.id}) by {interaction.user} (ID: {interaction.user.id})"
            )
        else:
            log.info(
                f"Executed {executed_command} command by {interaction.user} (ID: {interaction.user.id}) in DMs"
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
                        log.info(f"Loaded extension '{extension}'")
        return errorInt

    async def load_cogs(self) -> None:
        errorInt = 0

        log.warning("⟳ Loading modules")
        with log.status("[bold green]Working on guild modules..."):
            errorInt += await self.load_cog("cogs")

        if errorInt == 0:
            log.success("✔ Module loading completed successfully")
        else:
            log.warning(f"‼ Module loading completed with [bold underline white]{errorInt} error(s)[/]")