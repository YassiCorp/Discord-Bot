import asyncio, time, os
from rich.panel import Panel
from rich.text import Text

from libs import logger
from bot import BOT
from config import config

log = logger.ConsoleLogger(log_name="main", log_color="blue")

logo = r"""
    .....   ██╗   ██╗ █████╗ ███████╗███████╗██╗ ██████╗ ██████╗ ██████╗ ██████╗     ██████╗  ██████╗ ████████╗   .....
    .....   ╚██╗ ██╔╝██╔══██╗██╔════╝██╔════╝██║██╔════╝██╔═══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝   .....
    .....    ╚████╔╝ ███████║███████╗███████╗██║██║     ██║   ██║██████╔╝██████╔╝    ██████╔╝██║   ██║   ██║      .....
    .....     ╚██╔╝  ██╔══██║╚════██║╚════██║██║██║     ██║   ██║██╔══██╗██╔═══╝     ██╔══██╗██║   ██║   ██║      .....
    .....      ██║   ██║  ██║███████║███████║██║╚██████╗╚██████╔╝██║  ██║██║         ██████╔╝╚██████╔╝   ██║      .....
    .....      ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝         ╚═════╝  ╚═════╝    ╚═╝      .....
    """

bot = BOT()

log.clear_console()
log.print(Panel(Text(logo, justify="center"), subtitle=f"🛰️ YassiCorp Industries | 🪀 V1.0 | [link=https://www.github.com]🌐 Github[/]", expand=True))
log.debug("🚀 Script Started !")

template_files = [file for file in os.listdir("config") if file.endswith("template")]
if template_files:
    log.warn(f"You have [bold underline yellow]{len(template_files)} config template file(s)[/] (.template). If you are sure you have already set up all the config files, you can delete them.")


start = time.perf_counter()
asyncio.run(bot.load_cogs())  # <--- Start Cogs Task.
finish = time.perf_counter()
log.info(f"It took [bold underline white]{(finish - start):.2f} second(s)[/] to load the modules.")
bot.run(config.BOT.TOKEN, reconnect=True)