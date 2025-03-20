from typing import Optional, Union, List, Tuple
from nextcord import (
    Interaction,
    Member,
    Embed,
    File,
    Message,
    HTTPException,
    NotFound,
    ButtonStyle,
)
from nextcord.ext import commands
import nextcord
from nextcord.ui import View

from emojis import emoji
from libs import logger
from libs.embed import ModernEmbed, ErrorEmbed

log = logger.ConsoleLogger(log_name="libs/message", log_color="pink")

# Texte d'erreur global
error_text = f"{emoji.get('discord_support')} · Tu n'es pas l'utilisateur qui a exécuté cette commande."

# Classe de vue pour le bouton de suppression de message
class DeleteMessageView(View):
    def __init__(self, user: Member, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.user = user

    @nextcord.ui.button(
        label="Supprimer",
        emoji=f"{emoji.get('discord_trashcan')}",
        style=ButtonStyle.secondary,
        custom_id="delete",
    )
    async def delete_button(self, button: nextcord.ui.Button, interaction: Interaction):
        try:
            await interaction.message.delete()
        except (HTTPException, NotFound):
            pass
        await interaction.response.defer()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id == self.user.id or interaction.user.guild_permissions.manage_messages:
            return True
        else:
            await interaction.response.send_message(error_text, ephemeral=True)
            return False

# Fonction utilitaire pour envoyer un message avec un bouton de suppression
async def send_with_delete_button(
    interaction: Union[commands.Context, Message, Interaction],
    user: Member,
    content: Optional[str] = None,
    embed: Optional[Embed] = None,
    file: Optional[File] = None,
    view: Optional[View] = None,
    timeout: int = 180,
):
    del_view = DeleteMessageView(user=user, timeout=timeout)

    if view:
        view = await merge_views(view, del_view)
    else:
        view = del_view

    if isinstance(interaction, Interaction):
        if interaction.response.is_done():
            if file:
                message = await interaction.followup.send(
                    content=content,
                    embed=embed,
                    file=file,
                    view=view,
                    wait=True
                )
            else:
                message = await interaction.followup.send(
                    content=content,
                    embed=embed,
                    view=view,
                    wait=True
                )
        else:
            if file:
                message = await interaction.send(
                    content=content,
                    embed=embed,
                    file=file,
                    view=view,
                )
            else:
                message = await interaction.send(
                    content=content,
                    embed=embed,
                    view=view,
                )
    else:
        message = await interaction.edit(
            content=content,
            embed=embed,
            view=view,
        )

    await del_view.wait()

    try:
        await message.edit(view=None)
    except (HTTPException, NotFound):
        pass

# Fonction utilitaire pour envoyer un message de timeout
async def send_timeout_msg(ctx: Union[commands.Context, Message, Interaction], title: str, user: nextcord.User, ephemeral: bool = False):
    embed = ModernEmbed(
        title=f"{title} - {emoji.get('animated_clock')} Timeout",
        description=f"\n> {emoji.get('discord_mention')} {user.mention} Temps écoulé ! Vous avez pris trop de temps à répondre :/",
    )

    if isinstance(ctx, Interaction):
        if ctx.response.is_done():
            await ctx.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await ctx.send(embed=embed, ephemeral=ephemeral)
    elif isinstance(ctx, Message):
        await ctx.edit(embed=embed, view=None)
    else:
        await ctx.send(embed=embed)


async def merge_views(base_view: nextcord.ui.View, additional_view: nextcord.ui.View) -> None:
    """
    Adds components from `additional_view` to `base_view` without exceeding Discord's limit.
    This modifies `base_view` directly.

    Parameters:
        base_view (nextcord.ui.View): The view to which components are added.
        additional_view (nextcord.ui.View): The view providing additional components.
    """
    if not isinstance(base_view, nextcord.ui.View) or not isinstance(additional_view, nextcord.ui.View):
        raise TypeError("Both base_view and additional_view must be instances of nextcord.ui.View")

    # Iterate through components in additional_view
    for component in additional_view.children:
        if len(base_view.children) >= 25:  # Discord's limit
            log.warn("Warning: Cannot add more components. Discord's limit of 25 reached.")
            break
        base_view.add_item(component)