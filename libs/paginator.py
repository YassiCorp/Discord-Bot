import random

import nextcord
from nextcord.ext import commands
from typing import List, Optional, Union

from emojis import emoji
from libs.message import merge_views


class Page:
    """Représente une page avec du contenu textuel, des embeds et une vue personnalisée."""
    def __init__(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[nextcord.Embed]] = None,
        view: Optional[nextcord.ui.View] = None
    ):
        self.content = content
        self.embeds = embeds or []
        self.view = view  # Vue personnalisée pour cette page

class GoToPageModal(nextcord.ui.Modal):
    """Modal pour entrer un numéro de page."""
    def __init__(self, max_pages: int, paginator: "Paginator"):
        super().__init__(title="Aller à une page spécifique")
        self.max_pages = max_pages
        self.paginator = paginator

        self.page_input = nextcord.ui.TextInput(
            label=f"Choisissez un numéro de page (1-{max_pages})",
            placeholder=f"Exemple: {random.randint(1, max_pages)}",
            required=True,
            style=nextcord.TextInputStyle.short
        )
        self.add_item(self.page_input)

    async def callback(self, interaction: nextcord.Interaction):
        if not self.page_input.value.isdigit():
            await interaction.response.send_message(
                "Veuillez entrer un numéro valide.", ephemeral=True
            )
            return

        page_number = int(self.page_input.value)
        if page_number < 1 or page_number > self.max_pages:
            await interaction.response.send_message(
                f"Numéro de page invalide. Choisissez un numéro entre 1 et {self.max_pages}.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        self.paginator.current_page = page_number - 1
        await self.paginator.update_message()

class Paginator(nextcord.ui.View):
    """Système de pagination personnalisable."""
    def __init__(
        self,
        pages: List[Page],
        timeout: int = 180,
        author_check: Optional[int] = None,
        show_disabled: bool = True,
        disable_on_timeout: bool = True,
        loop_pages: bool = False,
        custom_buttons: Optional[List[nextcord.ui.Button]] = None,
    ):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.author_check = author_check
        self.show_disabled = show_disabled
        self.disable_on_timeout = disable_on_timeout
        self.loop_pages = loop_pages
        self.current_page = 0
        self.message: Optional[nextcord.Message] = None
        self.custom_buttons = custom_buttons

        self.reset_views()

    def reset_views(self):
        self.clear_items()
        # Ajouter des boutons personnalisés ou les boutons par défaut
        self.custom_buttons = self.custom_buttons or self.default_buttons()
        for button in self.custom_buttons:
            if isinstance(button, PaginatorButton) and button.action == "page_indicator":
                button.label = f"Page {self.current_page + 1}/{len(self.pages)}"
            self.add_item(button)

    def default_buttons(self) -> List[nextcord.ui.Button]:
        """Crée un ensemble de boutons par défaut pour la navigation."""
        return [
            PaginatorButton("first", emoji=emoji.get("pixel_symbol_quote_left"), style=nextcord.ButtonStyle.blurple),
            PaginatorButton("prev", emoji=emoji.get("pixel_hand_point_left"), style=nextcord.ButtonStyle.blurple),
            PaginatorButton("page_indicator", style=nextcord.ButtonStyle.gray),
            PaginatorButton("next", emoji=emoji.get("pixel_hand_point_right"), style=nextcord.ButtonStyle.blurple),
            PaginatorButton("last", emoji=emoji.get("pixel_symbol_quote_right"), style=nextcord.ButtonStyle.blurple),
        ]

    async def handle_button_action(self, action: str, interaction: nextcord.Interaction):
        """Gère les actions des boutons de navigation."""
        if not self.author_check and interaction.user.id != self.author_check:
            await interaction.response.send_message("Vous ne pouvez pas interagir avec cette pagination.", ephemeral=True)
            return

        if action == "first":
            self.current_page = 0
        elif action == "prev":
            if self.current_page > 0:
                self.current_page -= 1
            elif self.loop_pages:
                self.current_page = len(self.pages) - 1
        elif action == "next":
            if self.current_page < len(self.pages) - 1:
                self.current_page += 1
            elif self.loop_pages:
                self.current_page = 0
        elif action == "last":
            self.current_page = len(self.pages) - 1
        elif action == "go_to" or "page_indicator":
            await self.prompt_go_to_page(interaction)
            return

        # Mettre à jour le message
        await self.update_message()
        await interaction.response.defer()

    async def update_message(self):
        """Mise à jour du message affiché avec la page actuelle."""
        if self.message:
            current = self.pages[self.current_page]

            # Mise à jour des boutons de navigation
            for button in self.custom_buttons:
                if isinstance(button, PaginatorButton):
                    if button.action == "page_indicator":
                        button.label = f"Page {self.current_page + 1}/{len(self.pages)}"

                    if button.action == "first" or (button.action == "prev" and not self.loop_pages):
                        button.disabled = True if self.current_page == 0 else False

                    if button.action == "last" or (button.action == "next" and not self.loop_pages):
                        button.disabled = True if self.current_page == len(self.pages)-1 else False

            # Récupération de la vue personnalisée de la page actuelle
            if current.view:
                self.reset_views()
                await merge_views(self, current.view)

            await self.message.edit(content=current.content, embeds=current.embeds, view=self)

    async def prompt_go_to_page(self, interaction: nextcord.Interaction):
        """Affiche un modal pour aller à une page spécifique."""
        modal = GoToPageModal(max_pages=len(self.pages), paginator=self)
        await interaction.response.send_modal(modal)

    async def send(self, destination: Union[nextcord.TextChannel, nextcord.DMChannel, nextcord.Message, nextcord.Interaction, commands.Context]):
        """
        Envoie la pagination à un Channel, Message, Interaction ou Context.
        """
        first_page = self.pages[0]

        if isinstance(destination, commands.Context):
            self.message = await destination.send(content=first_page.content, embeds=first_page.embeds, view=first_page.view or self)
        elif isinstance(destination, nextcord.Interaction):
            self.message = await destination.response.send_message(content=first_page.content, embeds=first_page.embeds, view=first_page.view or self)
        elif isinstance(destination, nextcord.TextChannel) or isinstance(destination, nextcord.DMChannel):
            self.message = await destination.send(content=first_page.content, embeds=first_page.embeds, view=first_page.view or self)
        elif isinstance(destination, nextcord.Message):
            self.message = await destination.channel.send(content=first_page.content, embeds=first_page.embeds, view=first_page.view or self)
        else:
            raise TypeError("Destination non supportée. Utilisez Context, Interaction, Message ou Channel.")

        # Met à jour l'état initial de la pagination
        await self.update_message()

class PaginatorButton(nextcord.ui.Button):
    """Représente un bouton de navigation pour le paginator."""
    def __init__(self, action: str, **kwargs):
        super().__init__(**kwargs)
        self.action = action  # Action: "first", "prev", "next", "last", "go_to", "page_indicator"

    async def callback(self, interaction: nextcord.Interaction):
        if self.view and isinstance(self.view, Paginator):
            await self.view.handle_button_action(self.action, interaction)