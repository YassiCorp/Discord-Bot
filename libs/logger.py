from datetime import datetime

from rich import pretty, traceback
from rich.console import Console
from rich.theme import Theme
from libs.path import PATH_LOGS

import os

pretty.install()
traceback.install()

DEBUG = True

class ConsoleLogger(Console):
    def __init__(self, log_name: str, log_color: str, **kwargs):
        super().__init__(**kwargs, theme=Theme({
            "info": "#a7a0a6",
            "warning": "#ff9c00",
            "error": "bold red",
            "critical": "bold #c0392b",
            "debug": "#e3876a",
            "success": "green"
        }))

        pretty.install(console=self)
        traceback.install(console=self)

        self.log_name = log_name
        self.log_color = log_color
    def clear_console(self):
        """
            Efface la console en fonction du système d'exploitation. 🫨
        """
        os.system('cls' if os.name == 'nt' else 'clear')

    def log_to_console(self, message, level="info"):
        """
        Prints the log message to the console with appropriate formatting. 🖥️
        """
        log_name = f"[{self.log_color}]{self.log_name.upper()}[/{self.log_color}]"

        # Adding timestamp to the message
        formatted_message = f"[{log_name}] [{level.upper()}] {message}"

        # Formatting based on the log level
        self.log(formatted_message, style=level)

    def log_to_file(self, message, level="info"):
        """
        Saves the log message to a log file with level and timestamp. 📝
        """
        log_file = f"{PATH_LOGS}/log_{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file, "a", encoding="utf-8") as file:
            timestamp = datetime.now().strftime("[%x - %X]")
            file.write(f"{timestamp} [{level.upper()}] [{self.log_name.upper()}] {message}\n")

    def info(self, message):
        """Logs an information message. ℹ️"""
        self.log_to_console(message, "info")
        self.log_to_file(message, "info")

    def warning(self, message):
        """Logs a warning message. ⚠️"""
        self.log_to_console(message, "warning")
        self.log_to_file(message, "warning")

    def warn(self, message):
        """Logs a warning message. ⚠️"""
        self.warning(message)

    def error(self, message):
        """Logs an error message. ❌"""
        self.log_to_console(message, "error")
        self.log_to_file(message, "error")

    def critical(self, message):
        """Logs a critical message. ‼️"""
        self.log_to_console(message, "critical")
        self.log_to_file(message, "critical")

    def success(self, message):
        """Logs a succes message. ✔️"""
        self.log_to_console(message, "success")
        self.log_to_file(message, "success")

    def debug(self, message):
        """Logs a debug message. 🐞"""
        if DEBUG:
            self.log_to_console(message, "debug")
        self.log_to_file(message, "debug")

def get_rich_rendered_object(x) -> str:
    """Take any component from rich and render it as text. 🛰️"""
    console = Console()
    with console.capture() as capture:
        console.print(x)
    str_output = capture.get()
    return str_output