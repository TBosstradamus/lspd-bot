import discord
from datetime import datetime

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Erstellt ein standardisiertes Erfolgs-Embed."""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    return embed

def create_error_embed(description: str) -> discord.Embed:
    """Erstellt ein standardisiertes Fehler-Embed."""
    embed = discord.Embed(
        title="❌ Fehler",
        description=description,
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    return embed

def create_info_embed(title: str, description: str) -> discord.Embed:
    """Erstellt ein standardisiertes Info-Embed."""
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    return embed

def create_log_embed(title: str, description: str, color: discord.Color = discord.Color.greyple()) -> discord.Embed:
    """Erstellt ein standardisiertes Log-Embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    return embed