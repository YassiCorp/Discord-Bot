from discord import Interaction, Member, Embed, File, Message, HTTPException, NotFound, MISSING
from discord.ext import commands, pages
from typing import Optional, Union
import discord

from emojis import emoji
from libs.embed import ModernEmbed, ErrorEmbed

error_text = f"{emoji.discord_support} · Tu n'es pas l'utilisateur qui a exécuté cette commande."

default_page_buttons = [
            pages.PaginatorButton("first", emoji=emoji.get("pixel_symbol_quote_left"), style=discord.ButtonStyle.blurple),
            pages.PaginatorButton("prev", emoji=emoji.get("pixel_hand_point_left"), style=discord.ButtonStyle.blurple),
            pages.PaginatorButton(
                "page_indicator", style=discord.ButtonStyle.gray, disabled=True
            ),
            pages.PaginatorButton("next", emoji=emoji.get("pixel_hand_point_right"), style=discord.ButtonStyle.blurple),
            pages.PaginatorButton("last", emoji=emoji.get("pixel_symbol_quote_right"), style=discord.ButtonStyle.blurple),
        ]

class buttonGoto(discord.ui.View):
    def __init__(self, max_pages: int, page: discord.ext.pages.pagination.Paginator):
        super().__init__()
        self.max_pages = max_pages
        self.page = page

    @discord.ui.button(label="Aller a la page", emoji=emoji.discord_guide)
    async def button_callback(self, button, interaction):
        await interaction.response.send_modal(buttonGoto_Modal(max_pages=self.max_pages, page=self.page))

class buttonGoto_Modal(discord.ui.Modal):
    def __init__(self, max_pages: int, page: discord.ext.pages.pagination.Paginator):
        super().__init__(timeout=5*60, title="Choisis le numero de la page")
        self.max_pages = max_pages
        self.page = page

        self.input_text = discord.ui.InputText(
            label="Choisis la page que tu veux consulter",
            style=discord.InputTextStyle.short,
            placeholder=f"[Chiffres] (min: 1, max: {max_pages})",
            required=True,
        )
        self.add_item(self.input_text)

    async def callback(self, interaction: Interaction):
        if not self.input_text.value.isdigit() or not 1 <= int(self.input_text.value) <= self.max_pages:
            embed = ErrorEmbed(title="Goto Page",
                               description="La page indique n'existe pas !"
                                           f"\n\n> Veuillez entrer une valeur entre **`1`** et **`{self.max_pages}`**")

            await interaction.respond(embed=embed, ephemeral=True)
            return

        await self.page.goto_page(page_number=int(self.input_text.value)-1)
        await interaction.response.defer()

class DeleteMessageView(discord.ui.View):
    def __init__(self, user: Member, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.user = user
        self.message: Optional[Message] = None

    @discord.ui.button(
        label="Supprimer",
        emoji=f"{emoji.discord_trashcan}",
        style=discord.ButtonStyle.secondary,
        custom_id="delete"
    )
    async def delete_button(self, button: discord.ui.Button, interaction: Interaction):
        try:
            await self.message.delete()
        except (HTTPException, NotFound):
            pass

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id == self.user.id or interaction.user.guild_permissions.manage_messages:
            return True
        else:
            await interaction.response.send_message(error_text, ephemeral=True)
            return False

async def send_with_delete_button(
    interaction: Union[discord.ApplicationContext, discord.Message],
    user: Member,
    content: Optional[str] = None,
    embed: Optional[Embed] = None,
    file: Optional[File] = MISSING,
    timeout: int = 180
):
    view = DeleteMessageView(user=user, timeout=timeout)

    if isinstance(interaction, discord.ApplicationContext):
        if interaction.response.is_done():
            message = await interaction.followup.send(
                content=content,
                embed=embed,
                file=file,
                view=view,
                wait=True
            )
        else:
            message = await interaction.respond(
                content=content,
                embed=embed,
                file=file,
                view=view
            )
    else:
        message = await interaction.edit(
            content=content,
            embed=embed,
            file=file,
            view=view
        )

    view.message = message  # Associer le message à la vue
    await view.wait()

    try:
        await message.edit(view=None)
    except (HTTPException, NotFound):
        pass

async def send_timeout_msg(ctx, title: str, user: discord.User, ephemeral: bool = False):

    embed = ModernEmbed(title=f"{title} - {emoji.animated_clock} Timeout",
                        description=f"\n> {emoji.discord_mention} {user.mention} Temps écoulé ! Vous avez prit trop de temps a répondre :/")

    if isinstance(ctx, discord.ApplicationContext):
        if ctx.response.is_done():
            await ctx.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await ctx.respond(embed=embed, ephemeral=ephemeral)
    else:
        await ctx.edit(embed=embed, view=None)