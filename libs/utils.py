import itertools
from difflib import get_close_matches, SequenceMatcher
from typing import List

from config import config
from emojis import emoji
import nextcord, re

EMBED_COLOR = config.EMBED.COLOR

def emoji_latency(latency: float):
    if round(latency) >= 400:
        emoji_latency = emoji.get('the_connection_is_bad')
    elif round(latency) >= 170:
        emoji_latency = emoji.get('the_connection_is_good')
    else:
        emoji_latency = emoji.get('the_connection_is_excellent')

    return emoji_latency


def numberToEmoji(nb: int):
    number_emojis = {
        '0': emoji.get('pixel_number_zero'),
        '1': emoji.get('pixel_number_one'),
        '2': emoji.get('pixel_number_two'),
        '3': emoji.get('pixel_number_three'),
        '4': emoji.get('pixel_number_four'),
        '5': emoji.get('pixel_number_five'),
        '6': emoji.get('pixel_number_six'),
        '7': emoji.get('pixel_number_seven'),
        '8': emoji.get('pixel_number_eight'),
        '9': emoji.get('pixel_number_nine'),
    }

    # Convertir le nombre en chaîne de caractères
    nb_str = str(nb)
    result = ''

    for digit in nb_str:
        result += number_emojis.get(digit, emoji.get('pixel_symbol_space'))

    return result


class ClassicUrlButton(nextcord.ui.View):
    def __init__(self, label: str, url: str, style: nextcord.ui.Button.style = nextcord.ButtonStyle.gray, emoji: str = None):
        super().__init__()
        self.add_item(nextcord.ui.Button(label=label, emoji=emoji, url=url, style=style))

class DoubleUrlButton(nextcord.ui.View):
    def __init__(self, label1: str, url1: str, label2: str, url2: str, emoji1: str = None, emoji2: str = None):
        super().__init__()
        self.add_item(nextcord.ui.Button(label=label1, emoji=emoji1, url=url1))
        self.add_item(nextcord.ui.Button(label=label2, emoji=emoji2, url=url2))

class TripleUrlButton(nextcord.ui.View):
    def __init__(self, label1: str, url1: str, label2: str, url2: str, label3: str, url3: str, emoji1: str = None, emoji2: str = None, emoji3: str = None):
        super().__init__()
        self.add_item(nextcord.ui.Button(label=label1, emoji=emoji1, url=url1))
        self.add_item(nextcord.ui.Button(label=label2, emoji=emoji2, url=url2))
        self.add_item(nextcord.ui.Button(label=label3, emoji=emoji3, url=url3))

async def can_dm_user(user: nextcord.User) -> bool:
    try:
        await user.send()
    except nextcord.Forbidden:
        return False
    except nextcord.HTTPException:
        return False
    else:
        return True


def mediawiki_to_discord(text: str):
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

async def autocomplete(
    input_list: List[str],
    query: str,
    strict: bool = False,
    cutoff: float = 0.6,
    max_results: int = 25
) -> List[str]:
    """
    Fonction asynchrone pour l'autocomplétion dans Nextcord.

    Args:
        input_list (List[str]): La liste des options possibles.
        query (str): Le mot tapé par l'utilisateur.
        strict (bool): Si `True`, correspondance stricte (le début du mot doit correspondre).
                       Si `False`, utilise une correspondance approximative (par défaut: `False`).
        cutoff (float): Seuil de similitude (0.0 à 1.0) pour la recherche approximative.
                        Applicable uniquement si `strict` est `False`.
        max_results (int): Nombre maximum de résultats à retourner.

    Returns:
        List[str]: Une liste de suggestions correspondant à la recherche.
                   Peut être vide si aucune correspondance n'est trouvée.
    """
    # Normalisation des entrées pour une comparaison insensible à la casse
    query_lower = query.lower()
    input_list_lower = [item.lower() for item in input_list]

    if not query:
        return input_list[:max_results]

    if strict:
        # Mode strict : Retourne les éléments qui commencent par le query
        result = [item for item in input_list if item.lower().startswith(query_lower)]
    else:
        # Mode amélioré : Calcul de la similitude entre le query et le début de chaque élément
        similarity_scores = []
        for original_item, lower_item in zip(input_list, input_list_lower):
            length = min(len(query_lower), len(lower_item))
            sm = SequenceMatcher(None, query_lower, lower_item[:length])
            similarity = sm.ratio()
            if similarity >= cutoff:
                similarity_scores.append((similarity, original_item))

        # Trie des éléments par ordre décroissant de similitude
        similarity_scores.sort(reverse=True, key=lambda x: x[0])
        result = [item for _, item in similarity_scores][:max_results]

    return result

def find_option_value(options_list: list, option_name: str, default_value):
    for opt in options_list:
        if opt.get('name') == option_name:
            return opt.get('value')
        elif 'options' in opt:
            result = find_option_value(opt['options'], option_name, default_value)
            if result is not None:
                return result
    return default_value