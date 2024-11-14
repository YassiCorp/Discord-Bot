import re
from datetime import datetime
import discord
from discord.ext.pages import Paginator

from config import config
from emojis import emoji

EMBED_COLOR = config.EMBED.COLOR

def emoji_latency(latency: float):
    if round(latency) >= 400:
        emoji_latency = emoji.the_connection_is_bad
    elif round(latency) >= 170:
        emoji_latency = emoji.the_connection_is_good
    else:
        emoji_latency = emoji.the_connection_is_excellent

    return emoji_latency


def numberToEmoji(nb: int):
    number_emojis = {
        '0': emoji.pixel_number_zero,
        '1': emoji.pixel_number_one,
        '2': emoji.pixel_number_two,
        '3': emoji.pixel_number_three,
        '4': emoji.pixel_number_four,
        '5': emoji.pixel_number_five,
        '6': emoji.pixel_number_six,
        '7': emoji.pixel_number_seven,
        '8': emoji.pixel_number_eight,
        '9': emoji.pixel_number_nine,
    }

    # Convertir le nombre en chaîne de caractères
    nb_str = str(nb)
    result = ''

    for digit in nb_str:
        result += number_emojis.get(digit, emoji.pixel_symbol_space)

    return result


class ClassicUrlButton(discord.ui.View):
    def __init__(self, label: str, url: str, style: discord.ui.Button.style = discord.ButtonStyle.gray, emoji: str = None):
        super().__init__()
        self.add_item(discord.ui.Button(label=label, emoji=emoji, url=url, style=style))

class DoubleUrlButton(discord.ui.View):
    def __init__(self, label1: str, url1: str, label2: str, url2: str, emoji1: str = None, emoji2: str = None):
        super().__init__()
        self.add_item(discord.ui.Button(label=label1, emoji=emoji1, url=url1))
        self.add_item(discord.ui.Button(label=label2, emoji=emoji2, url=url2))

class TripleUrlButton(discord.ui.View):
    def __init__(self, label1: str, url1: str, label2: str, url2: str, label3: str, url3: str, emoji1: str = None, emoji2: str = None, emoji3: str = None):
        super().__init__()
        self.add_item(discord.ui.Button(label=label1, emoji=emoji1, url=url1))
        self.add_item(discord.ui.Button(label=label2, emoji=emoji2, url=url2))
        self.add_item(discord.ui.Button(label=label3, emoji=emoji3, url=url3))

async def can_dm_user(user: discord.User) -> bool:
    try:
        await user.send()
    except discord.Forbidden:
        return False
    except discord.HTTPException:
        return False
    else:
        return True


def mediawiki_to_discord(text):
    # Convert bold
    text = re.sub(r"'''(.*?)'''", r"**\1**", text)

    # Convert italics
    text = re.sub(r"''(.*?)''", r"*\1*", text)

    # Convert lists
    text = re.sub(r"^\*\s*", r"- ", text, flags=re.MULTILINE)  # unordered list
    text = re.sub(r"^#\s*", r"1. ", text, flags=re.MULTILINE)  # ordered list

    # Convert headings (assuming 1-6 levels of headings)
    text = re.sub(r"^={6}\s*(.*?)\s*={6}$", r"-# \1", text, flags=re.MULTILINE)
    text = re.sub(r"^={5}\s*(.*?)\s*={5}$", r"-# \1", text, flags=re.MULTILINE)
    text = re.sub(r"^={4}\s*(.*?)\s*={4}$", r"\1", text, flags=re.MULTILINE)
    text = re.sub(r"^={3}\s*(.*?)\s*={3}$", r"### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^={2}\s*(.*?)\s*={2}$", r"## \1", text, flags=re.MULTILINE)
    text = re.sub(r"^={1}\s*(.*?)\s*={1}$", r"# \1", text, flags=re.MULTILINE)

    # Convert links [[Link|Description]] to [Description](Link)
    text = re.sub(r"\[\[(.*?)(\|.*?)?\]\]", lambda m: f"[{m.group(2)[1:] if m.group(2) else m.group(1)}]({m.group(1)})",
                  text)

    # Convert blockquotes
    text = re.sub(r"^>\s*", r"> ", text, flags=re.MULTILINE)

    return text

class CustomPaginator(Paginator):
    async def edit(
        self,
        message: discord.Message,
        suppress: bool | None = None,
        allowed_mentions: discord.AllowedMentions | None = None,
        delete_after: float | None = None,
        user: discord.User | discord.Member | None = None,
    ) -> discord.Message | None:
        """Edits an existing message to replace it with the paginator contents.

        Overrides the original edit method to handle WebhookMessage objects.
        """
        if not isinstance(message, (discord.Message, discord.WebhookMessage)):
            raise TypeError(f"expected Message or WebhookMessage not {message.__class__!r}")

        self.update_buttons()

        page = self.pages[self.current_page]
        page_content = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        self.user = user or self.user

        edit_kwargs = {
            "content": page_content.content,
            "embeds": page_content.embeds,
            "attachments": [],
            "view": self,
            "suppress": suppress,
            "allowed_mentions": allowed_mentions,
        }

        # N'inclure 'delete_after' que si le message est un 'discord.Message'
        if delete_after is not None and isinstance(message, discord.Message):
            edit_kwargs["delete_after"] = delete_after

        try:
            self.message = await message.edit(**edit_kwargs)
        except (discord.NotFound, discord.Forbidden):
            pass

        return self.message
