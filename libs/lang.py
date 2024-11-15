
from databases.language import db_lib
from emojis import emoji as emojis
from libs.embed import Icon
from libs.path import PATH_LANGUAGE
import discord, os, yaml, re

db_lib = db_lib.LanguageDB()
def getLanguagePath(lang_id: str) -> str:
    dictVar: dict = {}
    for file in os.listdir(PATH_LANGUAGE):
        if file.endswith(".yaml"):
            path = f"{PATH_LANGUAGE}/{file}"

            with open(path, 'r') as file:
                yaml_file = yaml.safe_load(file)

            file.close()
            _lang_id = yaml_file['config']['id']
            dictVar[_lang_id] = path

    return dictVar[lang_id]

def getDefaultLanguage(guild: discord.Guild = None, user: discord.User = None) -> str:
    if user is not None:
        if db_lib.has_default_language_user(user_id=user.id):
            return db_lib.get_default_language_user(user_id=user.id)

    elif guild is not None:
        if db_lib.has_default_language_guild(guild_id=guild.id):
            return db_lib.get_default_language_guild(guild_id=guild.id)

    return "fr"

class language():
    def __init__(self, lang_id: str = "fr", user: discord.User = None, guild: discord.Guild = None):
        self.user = user
        self.guild = guild
        self.lang_id = lang_id

    def getText(self, prompt: str) -> str:
        # Get Yaml File
        path = getLanguagePath(lang_id=self.lang_id)
        prompt: list = prompt.split(".")
        with open(path, 'r', encoding="utf-8") as file:
            yaml_file = yaml.safe_load(file)
            variable: str = yaml_file["translations"]

        # Get the traduction node
        for x in prompt:
            if x.isnumeric():
                x = int(x)
            variable = variable[x]

        # Edit variables
        if self.user is not None:
            variable = variable.replace("{user}", str(self.user))
            variable = variable.replace("{user_id}", str(self.user.id))
            variable = variable.replace("{user_name}", self.user.display_name)
            variable = variable.replace("{user_mention}", self.user.mention)

        if self.guild is not None:
            variable = variable.replace("{guild_id}", str(self.guild.id))
            variable = variable.replace("{guild_name}", self.guild.name)
            variable = variable.replace("{guild_description}", self.guild.description)

        for emoji in re.findall(r'{emoji.\w*}', variable):
            emoji_name = emoji.split('.')[1].replace('}', '')
            variable = variable.replace(emoji, emojis.get(emoji_name))

        variable = variable.replace("{icon}", f"{Icon()}")
        variable = variable.replace("{nl}", "\n")

        return variable