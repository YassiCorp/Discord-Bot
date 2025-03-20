import os
import orjson

path = "emojis/emojis.json"

class EmojiLoader:
    def __init__(self, path=path):
        self.path = path

    def open_file(self) -> dict:
        """Load emojis from a JSON file using orjson."""
        if not os.path.exists(self.path):
            return {}
        with open(self.path, 'rb') as file:  # Reading in binary mode for orjson
            try:
                emojis = orjson.loads(file.read())
            except orjson.JSONDecodeError:
                emojis = {}
        return emojis

    def get_all(self):
        """Retrieve all emojis from the JSON file."""
        return self.open_file()

    def get(self, emoji_name: str):
        """Retrieve a specific emoji by name."""
        emojis = self.open_file()
        return emojis.get(emoji_name, "**EMOJI_INVALID**")

    async def update_from_guilds(self, guilds: list):
        """Update emojis from a list of guilds and save to the JSON file."""
        emoji_dict = {}
        for guild in guilds:
            for emoji in guild.emojis:
                emoji_name = emoji.name
                emoji_tag = str(emoji)
                emoji_dict[emoji_name] = emoji_tag

        # Write updated emojis to the JSON file
        with open(self.path, 'wb') as file:  # Writing in binary mode for orjson
            file.write(orjson.dumps(emoji_dict, option=orjson.OPT_INDENT_2))

emoji = EmojiLoader()