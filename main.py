import discord
from discord.ext import commands
import os
import asyncio

import config
from utils import database, logger

class LSPDAssistantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True  # Required for message content in on_message
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Load all cogs from the 'cogs' directory
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"Cog '{filename[:-3]}' geladen.")
                except Exception as e:
                    print(f"Fehler beim Laden von Cog '{filename[:-3]}': {e}")

        # Sync the command tree
        try:
            synced = await self.tree.sync()
            print(f"{len(synced)} Slash-Befehle synchronisiert.")
        except Exception as e:
            print(f"Fehler beim Synchronisieren der Befehle: {e}")

    async def on_command_error(self, ctx, error):
        # This is a fallback for any unhandled errors.
        # Specific errors should be handled in the cogs themselves.
        await logger.log_to_discord(self, "Unhandled Command Error", str(error), color=discord.Color.red())

def main():
    # Initialize the database
    database.setup_database()

    # Create and run the bot
    bot = LSPDAssistantBot()

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        # Centralized error handling for slash commands
        if isinstance(error, discord.app_commands.CheckFailure):
            await interaction.response.send_message("Du hast nicht die erforderlichen Berechtigungen für diesen Befehl.", ephemeral=True)
        else:
            # Log the error for debugging
            print(f"Ein Fehler ist im Command Tree aufgetreten: {error}")
            await logger.log_to_discord(
                bot,
                title="Slash Command Fehler",
                description=f"Ein Fehler ist bei der Ausführung von `{interaction.command.name}` aufgetreten.\n**Fehler:** {error}",
                color=discord.Color.red()
            )
            # Send a generic error message to the user
            if not interaction.response.is_done():
                await interaction.response.send_message("Ein unerwarteter Fehler ist aufgetreten.", ephemeral=True)
            else:
                await interaction.followup.send("Ein unerwarteter Fehler ist aufgetreten.", ephemeral=True)

    bot.run(config.TOKEN)

if __name__ == "__main__":
    main()