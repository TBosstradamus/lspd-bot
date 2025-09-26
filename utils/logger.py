import discord
from datetime import datetime
import config

async def log_to_discord(bot: discord.Client, title: str, description: str, color: discord.Color = discord.Color.blue()):
    """Sendet eine Nachricht als Embed an den konfigurierten Log-Kanal."""
    # The log channel ID is now sourced from the config file
    log_channel = bot.get_channel(config.LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        await log_channel.send(embed=embed)
    else:
        # Print an error if the channel is not found
        print(f"Fehler: Log-Kanal mit ID {config.LOG_CHANNEL_ID} nicht gefunden.")