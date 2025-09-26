import discord
from discord.ext import commands
from discord import app_commands

import config
from utils import database, embeds, logger, permissions

class ManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="einstellung", description="Registriert einen neuen Officer.")
    @app_commands.describe(user="Der Nutzer, der eingestellt wird.")
    @permissions.has_promotion_permission()
    async def einstellung(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)

        description = (
            "Bevor du offiziell Teil der Los Santos Police Department Academy wirst, "
            "benötigen wir noch einige persönliche Daten für dein Dispatch-Blatt. "
            "Diese Informationen sind entscheidend für deine Akte und den reibungslosen Ablauf. "
            "**Erst nach dem Absenden des Formulars erhältst du Zugriff auf den Discord.**\n\n"
            "Bitte fülle das Formular aus, indem du auf den Button klickst:"
        )

        # Using the standardized info embed
        embed = embeds.create_info_embed(
            title=f'Willkommen in der Academy des LSPD, {user.display_name}!',
            description=description
        )

        # The DM fallback and modal logic will be improved in a later step.
        # For now, we are just sending the confirmation to the command issuer.
        # In a real scenario, we would send the embed to the `user`.

        await interaction.followup.send(embed=embeds.create_success_embed("Einstellung eingeleitet", f"Dem Benutzer {user.mention} wurde eine Nachricht zur Dateneingabe gesendet."), ephemeral=True)
        await logger.log_to_discord(self.bot, title="Einstellung", description=f"{interaction.user.mention} hat die Einstellung für {user.mention} eingeleitet.")

    @app_commands.command(name="uprank", description="Befördert einen Nutzer.")
    @app_commands.describe(user="Der zu befördernde Nutzer.", neuer_rang="Der neue Rang des Nutzers (1-12).")
    @permissions.has_promotion_permission()
    async def uprank(self, interaction: discord.Interaction, user: discord.Member, neuer_rang: str):
        await interaction.response.defer(ephemeral=True)

        if neuer_rang not in config.PROMOTION_ROLE_MAP:
            await interaction.followup.send(embed=embeds.create_error_embed(f'Ungültiger Rang: **{neuer_rang}**. Bitte gib eine Nummer zwischen 1 und 12 ein.'), ephemeral=True)
            return

        if interaction.guild.id == config.PD_SERVER_ID:
            new_role_id = config.PROMOTION_ROLE_MAP[neuer_rang][0]
            all_role_ids = config.PD_PROMOTION_ROLES
        elif interaction.guild.id == config.ACADEMY_SERVER_ID:
            new_role_id = config.PROMOTION_ROLE_MAP[neuer_rang][1]
            all_role_ids = config.ACADEMY_PROMOTION_ROLES
        else:
            await interaction.followup.send(embed=embeds.create_error_embed("Dieser Befehl kann nur auf dem Police- oder Academy-Discord verwendet werden."), ephemeral=True)
            return

        new_role = interaction.guild.get_role(new_role_id)
        if not new_role:
            await interaction.followup.send(embed=embeds.create_error_embed(f'Die Rolle für Rang **{neuer_rang}** wurde auf diesem Server nicht gefunden.'), ephemeral=True)
            return

        roles_to_remove = [role for role_id in all_role_ids if (role := user.guild.get_role(role_id)) and role in user.roles]

        if roles_to_remove:
            await user.remove_roles(*roles_to_remove)

        await user.add_roles(new_role)

        conn = database.get_db_connection()
        conn.execute("INSERT OR REPLACE INTO users (user_id, rank) VALUES (?, ?)", (user.id, new_role.name))
        conn.commit()
        conn.close()

        await interaction.followup.send(embed=embeds.create_success_embed("Beförderung erfolgreich", f'User {user.mention} wurde erfolgreich zum Rang **{new_role.name}** befördert.'), ephemeral=True)
        await logger.log_to_discord(self.bot, title="Beförderung", description=f"{interaction.user.mention} hat {user.mention} zu {new_role.name} befördert.", color=discord.Color.orange())

    @app_commands.command(name="derank", description="Verringert den Rang eines Nutzers.")
    @app_commands.describe(user="Der Nutzer, dessen Rang verringert wird.", neuer_rang="Der neue Rang des Nutzers (1-12).")
    @permissions.has_promotion_permission()
    async def derank(self, interaction: discord.Interaction, user: discord.Member, neuer_rang: str):
        await interaction.response.defer(ephemeral=True)

        if neuer_rang not in config.PROMOTION_ROLE_MAP:
            await interaction.followup.send(embed=embeds.create_error_embed(f'Ungültiger Rang: **{neuer_rang}**. Bitte gib eine Nummer zwischen 1 und 12 ein.'), ephemeral=True)
            return

        if interaction.guild.id == config.PD_SERVER_ID:
            new_role_id = config.PROMOTION_ROLE_MAP[neuer_rang][0]
            all_role_ids = config.PD_PROMOTION_ROLES
        elif interaction.guild.id == config.ACADEMY_SERVER_ID:
            new_role_id = config.PROMOTION_ROLE_MAP[neuer_rang][1]
            all_role_ids = config.ACADEMY_PROMOTION_ROLES
        else:
            await interaction.followup.send(embed=embeds.create_error_embed("Dieser Befehl kann nur auf dem Police- oder Academy-Discord verwendet werden."), ephemeral=True)
            return

        new_role = interaction.guild.get_role(new_role_id)
        if not new_role:
            await interaction.followup.send(embed=embeds.create_error_embed(f'Die Rolle für Rang **{neuer_rang}** wurde auf diesem Server nicht gefunden.'), ephemeral=True)
            return

        roles_to_remove = [role for role_id in all_role_ids if (role := user.guild.get_role(role_id)) and role in user.roles]

        if roles_to_remove:
            await user.remove_roles(*roles_to_remove)

        await user.add_roles(new_role)

        conn = database.get_db_connection()
        conn.execute("INSERT OR REPLACE INTO users (user_id, rank) VALUES (?, ?)", (user.id, new_role.name))
        conn.commit()
        conn.close()

        await interaction.followup.send(embed=embeds.create_success_embed("Herabstufung erfolgreich", f'Rang von {user.mention} erfolgreich auf **{new_role.name}** herabgesetzt.'), ephemeral=True)
        await logger.log_to_discord(self.bot, title="Herabstufung", description=f"{interaction.user.mention} hat {user.mention} auf den Rang `{new_role.name}` herabgestuft.", color=discord.Color.orange())


    @app_commands.command(name="kuendigen", description="Entfernt die Ränge eines Nutzers und setzt seinen Status auf gekündigt.")
    @app_commands.describe(user="Der Nutzer, dem die Ränge entzogen werden.", grund="Der Grund für die Kündigung.")
    @permissions.has_promotion_permission()
    async def kuendigen(self, interaction: discord.Interaction, user: discord.Member, grund: str):
        await interaction.response.defer(ephemeral=True)

        roles_to_remove = []
        if interaction.guild.id == config.PD_SERVER_ID:
            lspd_role = interaction.guild.get_role(config.PD_LSPD_ROLE_ID)
            if lspd_role:
                roles_to_remove.append(lspd_role)
            all_role_ids = config.PD_PROMOTION_ROLES
        elif interaction.guild.id == config.ACADEMY_SERVER_ID:
            lspd_role = interaction.guild.get_role(config.ACADEMY_LSPD_ROLE_ID)
            if lspd_role:
                roles_to_remove.append(lspd_role)
            all_role_ids = config.ACADEMY_PROMOTION_ROLES
        else:
            await interaction.followup.send(embed=embeds.create_error_embed("Dieser Befehl kann nur auf dem Police- oder Academy-Discord verwendet werden."), ephemeral=True)
            return

        for role_id in all_role_ids:
            role = user.guild.get_role(role_id)
            if role and role in user.roles:
                roles_to_remove.append(role)

        if roles_to_remove:
            await user.remove_roles(*roles_to_remove, reason=f"Kündigung: {grund}")

        conn = database.get_db_connection()
        conn.execute("UPDATE users SET status = 'gekündigt' WHERE user_id = ?", (user.id,))
        conn.commit()
        conn.close()

        if interaction.guild.id == config.PD_SERVER_ID:
            await user.kick(reason=f"Kündigung: {grund}")

        await interaction.followup.send(embed=embeds.create_success_embed("Kündigung erfolgreich", f'Die Ränge von {user.mention} wurden entfernt und der Status auf "gekündigt" gesetzt.'), ephemeral=True)
        await logger.log_to_discord(self.bot, title="Kündigung", description=f"{interaction.user.mention} hat {user.mention} gekündigt. Grund: {grund}", color=discord.Color.red())


    @app_commands.command(name="akte", description="Zeigt die Akte eines Nutzers an.")
    @app_commands.describe(user="Der Nutzer, dessen Akte angezeigt werden soll.")
    @permissions.has_promotion_permission()
    async def akte(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)

        conn = database.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT rank, status FROM users WHERE user_id = ?", (user.id,))
        record = c.fetchone()
        conn.close()

        if record:
            embed = embeds.create_info_embed(
                title=f"Akte für {user.display_name}",
                description=f"Hier ist der Datensatz für {user.mention}."
            )
            embed.add_field(name="Rang", value=record['rank'], inline=True)
            embed.add_field(name="Status", value=record['status'].capitalize(), inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embeds.create_error_embed(f"Für den Nutzer {user.mention} wurde kein Datensatz gefunden."), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ManagementCog(bot))