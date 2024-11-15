import os
import yaml

path = "emojis/emojis.yaml"

class EmojiLoader:
    def __init__(self, path=path):
        self.path = path
        self.create_emoji_classes()

    def open_file(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, 'r') as file:
            emojis = yaml.safe_load(file) or {}
        return emojis

    def create_emoji_classes(self):
        emojis = self.open_file()
        for category, values in emojis.items():
            setattr(self, category, values)

    def get_all(self):
        return self.open_file()

    def get(self, emoji_name: str):
        emojis = self.open_file()
        return emojis.get(emoji_name, "**EMOJI_INVALID**")

    async def update_from_guilds(self, guilds: list):
        emoji_dict = {}
        for guild in guilds:
            for emoji in guild.emojis:
                emoji_name = emoji.name
                emoji_tag = str(emoji)
                emoji_dict[emoji_name] = emoji_tag

        with open(self.path, 'w') as file:
            yaml.dump(emoji_dict, file)

emoji = EmojiLoader()