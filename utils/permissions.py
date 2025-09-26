import discord
from discord import app_commands
import config

def is_god_user():
    """A check for the GOD_USER_ID."""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id == config.GOD_USER_ID
    return app_commands.check(predicate)

def has_promotion_permission():
    """A check for roles that are permitted to promote/demote."""
    def predicate(interaction: discord.Interaction) -> bool:
        # This check is a bit more complex as has_any_role is not async and can't be used here directly.
        # Instead, we get the user's roles and check if any of them are in the permitted list.
        if interaction.user.id == config.GOD_USER_ID:
            return True

        permitted_roles = set(config.ALL_PROMOTION_ROLES)
        user_roles = {role.id for role in interaction.user.roles}
        return not permitted_roles.isdisjoint(user_roles)
    return app_commands.check(predicate)

def has_dv_update_permission():
    """A check for roles that are permitted to send DV updates."""
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id == config.GOD_USER_ID:
            return True

        permitted_roles = set(config.DV_UPDATE_ROLES)
        user_roles = {role.id for role in interaction.user.roles}
        return not permitted_roles.isdisjoint(user_roles)
    return app_commands.check(predicate)