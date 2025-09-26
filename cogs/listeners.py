import discord
from discord.ext import commands, tasks
from itertools import cycle

import config
from utils import logger, embeds

class ListenersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()

    def cog_unload(self):
        self.update_status.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Eingeloggt als {self.bot.user}')
        await logger.log_to_discord(
            self.bot,
            title="Bot-Status",
            description="Der Bot ist erfolgreich online gegangen und bereit.",
            color=discord.Color.green()
        )

    @tasks.loop(seconds=15)
    async def update_status(self):
        activities = cycle([
            discord.Activity(type=discord.ActivityType.streaming, name="discord.gg/x-roleplay", url="https://www.x-roleplay.de"),
            discord.Activity(type=discord.ActivityType.streaming, name="für X Beamte", url="https://www.x-roleplay.de")
        ])
        current_activity = next(activities)
        if "X" in current_activity.name:
            unique_members = set()
            police_server = self.bot.get_guild(config.PD_SERVER_ID)
            academy_server = self.bot.get_guild(config.ACADEMY_SERVER_ID)

            if police_server:
                for member in police_server.members:
                    if any(role.id in config.STATUS_ROLE_IDS for role in member.roles):
                        unique_members.add(member.id)
            if academy_server:
                for member in academy_server.members:
                    if any(role.id in config.STATUS_ROLE_IDS for role in member.roles):
                        unique_members.add(member.id)

            count = len(unique_members)
            new_name = current_activity.name.replace("X", str(count))
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name=new_name, url="https://www.x-roleplay.de"))
        else:
            await self.bot.change_presence(activity=current_activity)

    @update_status.before_loop
    async def before_update_status(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != config.PD_SERVER_ID:
            return

        academy_server = self.bot.get_guild(config.ACADEMY_SERVER_ID)
        if not academy_server:
            return

        try:
            academy_member = await academy_server.fetch_member(member.id)
            if academy_member and any(role.id == config.ACADEMY_PROMOTION_ROLES[1] for role in academy_member.roles):
                lspd_role = member.guild.get_role(config.PD_LSPD_ROLE_ID)
                officer2_role = member.guild.get_role(config.PD_OFFICER_RANK_2_ID)

                roles_to_add = [r for r in [lspd_role, officer2_role] if r]
                if roles_to_add:
                    await member.add_roles(*roles_to_add)

                if academy_member.nick:
                    await member.edit(nick=academy_member.nick)

        except discord.NotFound:
            pass # Member not on academy server, do nothing.
        except Exception as e:
            await logger.log_to_discord(self.bot, "Fehler bei on_member_join", str(e), color=discord.Color.red())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id == config.ACADEMY_MIRROR_CHANNEL_ID:
            target_channel = self.bot.get_channel(config.PD_MIRROR_CHANNEL_ID)
            if target_channel:
                embed = embeds.create_info_embed(
                    title="Nachricht von Academy-Discord",
                    description=message.content
                )
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
                await target_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        police_server = self.bot.get_guild(config.PD_SERVER_ID)
        academy_server = self.bot.get_guild(config.ACADEMY_SERVER_ID)
        if not police_server or not academy_server:
            return

        role_map = None
        other_member = None

        if before.guild.id == config.PD_SERVER_ID:
            other_member = academy_server.get_member(after.id)
            role_map = config.POLICE_TO_ACADEMY_ROLES
        elif before.guild.id == config.ACADEMY_SERVER_ID:
            other_member = police_server.get_member(after.id)
            role_map = config.ACADEMY_TO_POLICE_ROLES
        else:
            return

        if not other_member or not role_map:
            return

        # Role added
        added_roles = set(after.roles) - set(before.roles)
        for role in added_roles:
            if role.id in role_map:
                new_role_id = role_map[role.id]
                new_role = other_member.guild.get_role(new_role_id)
                if new_role and new_role not in other_member.roles:
                    await other_member.add_roles(new_role)

        # Role removed
        removed_roles = set(before.roles) - set(after.roles)
        for role in removed_roles:
            if role.id in role_map:
                old_role_id_in_other_server = role_map[role.id]
                old_role_in_other_server = other_member.guild.get_role(old_role_id_in_other_server)
                if old_role_in_other_server and old_role_in_other_server in other_member.roles:
                    await other_member.remove_roles(old_role_in_other_server)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # This is for classic commands, not slash commands.
        # Slash command errors are handled in the main bot file.
        print(f"Ein Fehler ist aufgetreten: {error}")
        await logger.log_to_discord(
            self.bot,
            title="Befehlsfehler",
            description=f"Ein Fehler ist bei der Ausführung von `{ctx.command.name}` aufgetreten. \n**Fehler:** {error}",
            color=discord.Color.red()
        )

async def setup(bot):
    await bot.add_cog(ListenersCog(bot))