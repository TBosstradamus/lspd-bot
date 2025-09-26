import discord
from discord.ext import commands
from discord import app_commands

from utils import embeds, logger, permissions

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Löscht eine bestimmte Anzahl von Nachrichten im aktuellen Kanal.")
    @app_commands.describe(amount="Die Anzahl der zu löschenden Nachrichten (maximal 100).")
    @permissions.is_god_user()
    async def clear_messages(self, interaction: discord.Interaction, amount: int):
        """
        Löscht die angegebene Anzahl von Nachrichten aus dem aktuellen Kanal.
        """
        await interaction.response.defer(ephemeral=True)

        if not 1 <= amount <= 100:
            await interaction.followup.send(embed=embeds.create_error_embed("Die Anzahl muss zwischen 1 und 100 liegen."), ephemeral=True)
            return

        try:
            # Purge the messages
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(embed=embeds.create_success_embed("Nachrichten gelöscht", f'**{len(deleted)}** Nachrichten erfolgreich gelöscht.'), ephemeral=True)

            await logger.log_to_discord(
                self.bot,
                title="Nachrichten gelöscht",
                description=f"**{interaction.user.display_name}** hat **{len(deleted)}** Nachrichten in Kanal `{interaction.channel.name}` gelöscht.",
                color=discord.Color.red()
            )

        except Exception as e:
            await interaction.followup.send(embed=embeds.create_error_embed(f"Beim Löschen der Nachrichten ist ein Fehler aufgetreten: {e}"), ephemeral=True)
            await logger.log_to_discord(
                self.bot,
                title="Fehler beim Löschen",
                description=f"Fehler beim Löschen von Nachrichten in Kanal `{interaction.channel.name}`: {e}",
                color=discord.Color.red()
            )

async def setup(bot):
    await bot.add_cog(AdminCog(bot))