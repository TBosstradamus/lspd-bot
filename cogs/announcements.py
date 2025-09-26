import discord
from discord.ext import commands
from discord import app_commands
from dateutil.parser import parse, ParserError
from datetime import datetime

import config
from utils import embeds, logger, permissions

class AnnouncementsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dv-update", description="Gibt eine offizielle Änderung der Dienstvorschriften bekannt.")
    @app_commands.describe(
        geaenderte_paragraphen="Liste geänderter Paragraphen (optional).",
        hinzugefuegte_paragraphen="Liste hinzugefügter Paragraphen (optional).",
        entfernte_paragraphen="Liste entfernter Paragraphen (optional)."
    )
    @permissions.has_dv_update_permission()
    async def dv_update(self, interaction: discord.Interaction, geaenderte_paragraphen: str = None, hinzugefuegte_paragraphen: str = None, entfernte_paragraphen: str = None):
        await interaction.response.defer(ephemeral=True)

        if not geaenderte_paragraphen and not hinzugefuegte_paragraphen and not entfernte_paragraphen:
            await interaction.followup.send(embed=embeds.create_error_embed("Du musst mindestens eines der optionalen Felder ausfüllen."), ephemeral=True)
            return

        # Using a standard info embed for the announcement
        embed = embeds.create_info_embed(
            title="🚨 Offizielle Änderung der Dienstvorschriften",
            description="Offizielle Änderungen der Dienstvorschriften wurden bekanntgegeben:"
        )

        if geaenderte_paragraphen:
            embed.add_field(name="✏️ Geändert", value=geaenderte_paragraphen, inline=False)
        if hinzugefuegte_paragraphen:
            embed.add_field(name="➕ Hinzugefügt", value=hinzugefuegte_paragraphen, inline=False)
        if entfernte_paragraphen:
            embed.add_field(name="➖ Entfernt", value=entfernte_paragraphen, inline=False)

        embed.set_footer(text=f"Bekanntgegeben von: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.color = discord.Color.dark_red() # Custom color for this specific announcement

        target_channel_ids = [config.PD_DV_UPDATES_CHANNEL_ID, config.ACADEMY_DV_UPDATES_CHANNEL_ID]
        for channel_id in target_channel_ids:
            target_channel = self.bot.get_channel(channel_id)
            if target_channel:
                await target_channel.send(embed=embed)

        await interaction.followup.send(embed=embeds.create_success_embed("Ankündigung gesendet", "Die Dienstvorschriften-Änderung wurde erfolgreich veröffentlicht."), ephemeral=True)
        await logger.log_to_discord(self.bot, title="DV-Update", description=f"{interaction.user.mention} hat eine DV-Änderung angekündigt.", color=discord.Color.gold())

    @app_commands.command(name="dienstbesprechung", description="Kündigt eine Dienstbesprechung für beide Server an.")
    @app_commands.describe(
        datum="Datum der Besprechung (TT.MM.JJJJ).",
        uhrzeit="Uhrzeit der Besprechung (HH:MM).",
        ort="Ort der Besprechung (z.B. Sprachkanal, Ingame-Ort)."
    )
    @permissions.has_dv_update_permission()
    async def dienstbesprechung(self, interaction: discord.Interaction, datum: str, uhrzeit: str, ort: str):
        await interaction.response.defer(ephemeral=True)

        try:
            combined_dt_str = f"{datum} {uhrzeit}"
            parsed_dt = parse(combined_dt_str, dayfirst=True)
            timestamp_formatted = parsed_dt.strftime("%d.%m.%Y um %H:%M Uhr")
        except (ParserError, ValueError):
            await interaction.followup.send(embed=embeds.create_error_embed("Ungültiges Datums- oder Uhrzeitformat. Bitte verwende `TT.MM.JJJJ` und `HH:MM`."), ephemeral=True)
            return

        # Using a standard info embed for the announcement
        embed = embeds.create_info_embed(
            title="📢 Offizielle Dienstbesprechung",
            description="Eine verbindliche Dienstbesprechung wurde angekündigt. Die Anwesenheit ist für alle Mitarbeiter verpflichtend."
        )
        embed.add_field(name="Datum", value=timestamp_formatted, inline=False)
        embed.add_field(name="Ort", value=ort, inline=False)
        embed.timestamp = parsed_dt
        embed.set_footer(text=f"Angekündigt von: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        target_channel_ids = [config.PD_BESPRECHUNG_CHANNEL_ID, config.ACADEMY_BESPRECHUNG_CHANNEL_ID]
        for channel_id in target_channel_ids:
            target_channel = self.bot.get_channel(channel_id)
            if target_channel:
                await target_channel.send(embed=embed)

        await interaction.followup.send(embed=embeds.create_success_embed("Ankündigung gesendet", "Die Dienstbesprechung wurde erfolgreich angekündigt."), ephemeral=True)
        await logger.log_to_discord(self.bot, title="Dienstbesprechung", description=f"{interaction.user.mention} hat eine Dienstbesprechung für den {timestamp_formatted} angekündigt.", color=discord.Color.blue())


async def setup(bot):
    await bot.add_cog(AnnouncementsCog(bot))