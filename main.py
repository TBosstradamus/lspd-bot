import discord
from discord import app_commands
import os
import sqlite3
from datetime import datetime
import asyncio
from itertools import cycle
from dateutil.parser import parse
from dateutil.parser._parser import ParserError

# --- Discord-Konfiguration ---

# Dein Bot-Token
TOKEN = "MTQxNzk3OTgwNjM0MzEwMjYxNQ.GXffq8.hZh7Yk7wOhCevrtob1-Ka7oKMX51vbRT5GwlMg"

# Deine Benutzer-ID für volle Berechtigungen (God-User)
GOD_USER_ID = 675898941262528512

# --------------------------------------------------------------------------------
# --- SERVER: Los Santos Police Department (PD) ---
# --------------------------------------------------------------------------------
PD_SERVER_ID = 1366042788054958171

# Kanal-IDs für den PD-Server
PD_UPDATES_CHANNEL_ID = 1366042791825772666 # Kanal für offizielle Ankündigungen
PD_MIRROR_CHANNEL_ID = 975319864201357980 # Kanal für Nachrichtenspiegelung
PD_DV_UPDATES_CHANNEL_ID = 1366042791825772665 # Kanal für Dienstvorschriften-Updates
PD_BESPRECHUNG_CHANNEL_ID = 1366042791825772665 # Kanal für Dienstbesprechung

# Rollen-IDs für den PD-Server
PD_LSPD_ROLE_ID = 1366042788054958177
PD_OFFICER_RANK_2_ID = 1366042788092842123

# Beförderungs-Rollen (in der Reihenfolge 1-12)
PD_PROMOTION_ROLES = [
     1366042788092842122, # Rang 1
     1366042788092842123, # Rang 2
     1366042788092842124, # Rang 3
     1366042788105289870, # Rang 4
     1366042788105289871, # Rang 5
     1366042788105289872, # Rang 6
     1366042788105289873, # Rang 7
     1366042788105289874, # Rang 8
     1366042788105289875, # Rang 9
     1366042788126523441, # Rang 10
     1366042788105289876, # Rang 11
     1366042788126523442, # Rang 12
]

# Rollen mit Beförderungsberechtigung auf dem PD-Server
PD_PROMOTION_PERMITTED_ROLES = [
     1366042788105289874, 1366042788105289875, 1366042788126523441, 
     1366042788105289876, 1366042788126523442, 1366042788092842115
]


# --------------------------------------------------------------------------------
# --- SERVER: LSPD Academy ---
# --------------------------------------------------------------------------------
ACADEMY_SERVER_ID = 1399407359087874110

# Kanal-IDs für den Academy-Server
ACADEMY_UPDATES_CHANNEL_ID = 1399407360853938252 # Kanal für offizielle Ankündigungen
ACADEMY_MIRROR_CHANNEL_ID = 987654321098765432 # Kanal für Nachrichtenspiegelung
ACADEMY_LOG_CHANNEL_ID = 1418009486836109375 # Kanal für Bot-Logs
ACADEMY_DV_UPDATES_CHANNEL_ID = 1399407360853938251 # Kanal für Dienstvorschriften-Updates
ACADEMY_BESPRECHUNG_CHANNEL_ID = 1399407360853938251 # Kanal für Dienstbesprechung

# Rollen-IDs für den Academy-Server
ACADEMY_LSPD_ROLE_ID = 1399407359087874112
ACADEMY_PROMOTION_ROLES = [
     1399407359125753916, # Rang 1
     1399407359125753917, # Rang 2
     1399407359125753918, # Rang 3
     1399407359125753919, # Rang 4
     1399407359125753920, # Rang 5
     1399407359125753921, # Rang 6
     1399407359125753922, # Rang 7
     1399407359125753923, # Rang 8
     1399407359125753924, # Rang 9
     1399407359138332831, # Rang 10
     1399407359138332832, # Rang 11
     1399407359138332833, # Rang 12
]

# Rollen mit Beförderungsberechtigung auf dem Academy-Server
ACADEMY_PROMOTION_PERMITTED_ROLES = [
     1399407359138332833, 1399407359138332832, 1399407359138332831, 1399407359100719227,
     1399407359125753924, 1399407359125753923, 1399407359100719231, 1399407359100719231
]


# --------------------------------------------------------------------------------
# --- Global & Mappings ---
# --------------------------------------------------------------------------------
# Kanal-ID für Bot-Logs (Wiederhergestellt)
LOG_CHANNEL_ID = 1417998626776682636

# Rollen-Mapping für die Synchronisation
POLICE_TO_ACADEMY_ROLES = dict(zip(PD_PROMOTION_ROLES, ACADEMY_PROMOTION_ROLES))
ACADEMY_TO_POLICE_ROLES = {v: k for k, v in POLICE_TO_ACADEMY_ROLES.items()}

# Mapping von Rangnummer zu Rollen-IDs für beide Server
PROMOTION_ROLE_MAP = {
     str(i + 1): (PD_PROMOTION_ROLES[i], ACADEMY_PROMOTION_ROLES[i])
     for i in range(len(PD_PROMOTION_ROLES))
}

# Kombinierte Rollenlisten für globale Befehlsberechtigungen
ALL_PROMOTION_ROLES = PD_PROMOTION_PERMITTED_ROLES + ACADEMY_PROMOTION_PERMITTED_ROLES
STATUS_ROLE_IDS = [ACADEMY_LSPD_ROLE_ID, PD_LSPD_ROLE_ID]

# Rechtegruppe für den dv-update Befehl (Ränge 10, 11, 12)
DV_UPDATE_ROLES = [
    PD_PROMOTION_ROLES[9], PD_PROMOTION_ROLES[10], PD_PROMOTION_ROLES[11],
    ACADEMY_PROMOTION_ROLES[9], ACADEMY_PROMOTION_ROLES[10], ACADEMY_PROMOTION_ROLES[11]
]


# --- Intents und Bot-Client ---
intents = discord.Intents.default()
intents.members = True
bot = discord.Client(intents=intents, member_cache_flags=discord.MemberCacheFlags.all())
tree = app_commands.CommandTree(bot)

# --- Datenbankverbindung und Setup ---
conn = sqlite3.connect('lspd_assistant.db')
c = conn.cursor()

def setup_database():
     c.execute('''CREATE TABLE IF NOT EXISTS users (
                  user_id INTEGER PRIMARY KEY,
                  rank TEXT,
                  status TEXT DEFAULT 'aktiv'
                )''')
     c.execute('''CREATE TABLE IF NOT EXISTS registrations (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  event_name TEXT,
                  registered_at TEXT
                )''')
     conn.commit()

# --- Modals ---
class EinstellungModal(discord.ui.Modal, title="Persönliche Daten"):
     def __init__(self, user: discord.Member, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self.user = user

     name = discord.ui.TextInput(
          label="Vollständiger Name des Officers",
          placeholder="Max Mustermann",
          max_length=50,
          required=True
     )

     email = discord.ui.TextInput(
          label="E-Mail-Adresse",
          placeholder="beispiel@lspd.com",
          max_length=50,
          required=True
     )
     
     async def on_submit(self, interaction: discord.Interaction):
          # Den Academy-Server-Kontext für die Rollenzuweisung abrufen
          academy_guild = bot.get_guild(ACADEMY_SERVER_ID)
          
          if not academy_guild:
               await interaction.response.send_message("Der Academy-Server wurde nicht gefunden. Rollen können nicht zugewiesen werden.", ephemeral=True)
               return

          # Rollen-IDs für LSPD und Officer 1
          lspd_role_id = ACADEMY_LSPD_ROLE_ID
          officer1_role_id = ACADEMY_PROMOTION_ROLES[0]

          # Rollen-Objekte vom Academy-Server abrufen
          lspd_role = academy_guild.get_role(lspd_role_id)
          officer1_role = academy_guild.get_role(officer1_role_id)

          roles_to_add = []
          if lspd_role:
               roles_to_add.append(lspd_role)
          if officer1_role:
               roles_to_add.append(officer1_role)

          # Das Mitglied auf dem Academy-Server finden
          academy_member = academy_guild.get_member(self.user.id)
          if not academy_member:
               await interaction.response.send_message("Der Nutzer wurde auf dem Academy-Server nicht gefunden. Rollen können nicht zugewiesen werden.", ephemeral=True)
               return

          # Rollen hinzufügen
          if roles_to_add:
               try:
                    await academy_member.add_roles(*roles_to_add)
                    await log_to_discord(
                         title="Rollen zugewiesen",
                         description=f"Rollen `LSPD` und `Officer 1` wurden {self.user.mention} erfolgreich zugewiesen.",
                         color=discord.Color.green()
                    )
               except Exception as e:
                    await log_to_discord(
                         title="Fehler beim Rollen-Zuweisen",
                         description=f"Konnte Rollen für {self.user.mention} nicht zuweisen: {e}",
                         color=discord.Color.red()
                    )

          # Log-Embed für den internen Bot-Log (mit Footer)
          log_embed = discord.Embed(
               title="Officer-Registrierung",
               color=discord.Color.blue(),
               timestamp=datetime.now()
          )
          log_embed.add_field(name="Mitarbeiter", value=self.user.mention, inline=True)
          log_embed.add_field(name="Discord-ID", value=self.user.id, inline=True)
          log_embed.add_field(name="Name", value=self.name.value, inline=False)
          log_embed.add_field(name="E-Mail", value=self.email.value, inline=False)
          log_embed.set_footer(text=f"Registrierung veranlasst von: {interaction.user.display_name}")

          log_channel = bot.get_channel(ACADEMY_LOG_CHANNEL_ID)
          if log_channel:
               await log_channel.send(embed=log_embed)

          # Öffentliche Ankündigung (ohne Footer)
          announcement_embed = discord.Embed(
               title="Neuer Officer!",
               description=f"Bitte begrüßt unser neuestes Mitglied, {self.user.mention}, in der Academy des LSPD.",
               color=discord.Color.green()
          )

          personal_updates_channel = bot.get_channel(PD_UPDATES_CHANNEL_ID)
          if personal_updates_channel:
               await personal_updates_channel.send(embed=announcement_embed)
          
          academy_updates_channel = bot.get_channel(ACADEMY_UPDATES_CHANNEL_ID)
          if academy_updates_channel:
               await academy_updates_channel.send(embed=announcement_embed)
          
          await interaction.response.send_message(f'Die Daten für {self.user.mention} wurden erfolgreich gespeichert.', ephemeral=True)


# --- Views (Buttons) ---
class EinstellungButton(discord.ui.View):
     def __init__(self, user: discord.Member, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self.user = user

     @discord.ui.button(label="Daten eintragen", style=discord.ButtonStyle.success)
     async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
          # Überprüfe, ob der Button vom richtigen Nutzer geklickt wurde
          if interaction.user.id != self.user.id:
               await interaction.response.send_message("Du kannst nur deine eigenen Daten eintragen.", ephemeral=True)
               return

          await interaction.response.send_modal(EinstellungModal(user=self.user))
          await interaction.message.delete() # Löscht die Nachricht mit dem Button


# --- Logging-Funktion ---
async def log_to_discord(title, description, color=discord.Color.blue()):
     """Sendet eine Nachricht als Embed an den konfigurierten Log-Kanal."""
     log_channel = bot.get_channel(LOG_CHANNEL_ID)
     if log_channel:
          embed = discord.Embed(
               title=title,
               description=description,
               color=color,
               timestamp=datetime.now()
          )
          await log_channel.send(embed=embed)
     else:
          print(f"Fehler: Log-Kanal mit ID {LOG_CHANNEL_ID} nicht gefunden.")

# --- Hilfsfunktion für DM-Fallback ---
async def send_dm_or_fallback(interaction: discord.Interaction, user: discord.Member, message: str, embed: discord.Embed = None, view: discord.ui.View = None):
     """
     Sendet eine DM an einen Nutzer. Wenn dies fehlschlägt, erstellt es einen privaten Kanal.
     """
     try:
          # Versuche, die Nachricht als DM zu senden
          await user.send(content=message, embed=embed, view=view)
          
          # Wenn erfolgreich, sende eine private Bestätigung an den Initiator
          await interaction.followup.send(f'Eine Nachricht wurde erfolgreich als DM an {user.mention} gesendet.', ephemeral=True)
          return True

     except discord.Forbidden:
          # Fallback: DM ist blockiert, also einen privaten Kanal erstellen
          guild = interaction.guild
          if not guild:
               await interaction.followup.send("Dieser Befehl kann nicht in DMs ausgeführt werden, um einen Fallback-Kanal zu erstellen.", ephemeral=True)
               return False

          # Berechtigungen festlegen
          overwrites = {
               guild.default_role: discord.PermissionOverwrite(read_messages=False),
               user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
               guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
          }

          # Füge die Promotion-Rollen hinzu
          for role_id in ALL_PROMOTION_ROLES:
               role = guild.get_role(role_id)
               if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

          # Kanalname festlegen
          channel_name = f"privat-{user.name}"
          
          try:
               # Erstelle den Kanal mit den festgelegten Berechtigungen
               private_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
               
               # Sende die Nachricht in den neu erstellten Kanal
               await private_channel.send(content=f"{user.mention} {message}", embed=embed, view=view)
               
               await interaction.followup.send(
                    f'Konnte {user.mention} keine DM senden. Ein privater Kanal ({private_channel.mention}) wurde als Fallback erstellt.',
                    ephemeral=True
               )
               return True

          except discord.Forbidden:
               # Wenn der Bot nicht die Berechtigung hat, Kanäle zu erstellen
               await interaction.followup.send(f'Konnte {user.mention} keine DM senden und habe nicht die Berechtigung, einen Fallback-Kanal zu erstellen. Bitte überprüfe die Bot-Berechtigungen.', ephemeral=True)
               return False
          except Exception as e:
               # Unbekannte Fehler
               await interaction.followup.send(f"Ein unerwarteter Fehler ist aufgetreten: {e}", ephemeral=True)
               return False

# --- Status-Funktion ---
async def update_status():
     activities = cycle([
          discord.Activity(type=discord.ActivityType.streaming, name="discord.gg/x-roleplay", url="https://www.x-roleplay.de"),
          discord.Activity(type=discord.ActivityType.streaming, name="für X Beamte", url="https://www.x-roleplay.de")
     ])
     while True:
          current_activity = next(activities)
          if "X" in current_activity.name:
               unique_members = set()
               police_server = bot.get_guild(PD_SERVER_ID)
               academy_server = bot.get_guild(ACADEMY_SERVER_ID)

               if police_server:
                    for member in police_server.members:
                         if any(role.id in STATUS_ROLE_IDS for role in member.roles):
                              unique_members.add(member.id)
               if academy_server:
                    for member in academy_server.members:
                         if any(role.id in STATUS_ROLE_IDS for role in member.roles):
                              unique_members.add(member.id)
               
               count = len(unique_members)
               new_name = current_activity.name.replace("X", str(count))
               await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name=new_name, url="https://www.x-roleplay.de"))
          else:
               await bot.change_presence(activity=current_activity)
          await asyncio.sleep(15)


@bot.event
async def on_ready():
     setup_database()
     print(f'Eingeloggt als {bot.user}')
     await tree.sync()
     print('Globale Slash-Commands synchronisiert.')
     bot.loop.create_task(update_status())
     await log_to_discord(
          title="Bot-Status",
          description="Der Bot ist erfolgreich online gegangen und bereit.",
          color=discord.Color.green()
     )


@bot.event
async def on_member_join(member: discord.Member):
     """Weist neuen Mitgliedern auf dem Police-Server automatisch Rollen und Nickname zu."""
     if member.guild.id != PD_SERVER_ID:
          return
     
     academy_server = bot.get_guild(ACADEMY_SERVER_ID)
     if not academy_server:
          print("Academy-Server nicht gefunden.")
          return
     
     try:
          academy_member = await academy_server.fetch_member(member.id)
          if academy_member and any(role.id == ACADEMY_PROMOTION_ROLES[1] for role in academy_member.roles):
               lspd_role = member.guild.get_role(PD_LSPD_ROLE_ID)
               officer2_role = member.guild.get_role(PD_OFFICER_RANK_2_ID)
               
               roles_to_add = []
               if lspd_role:
                    roles_to_add.append(lspd_role)
               if officer2_role:
                    roles_to_add.append(officer2_role)
                    
               if roles_to_add:
                    await member.add_roles(*roles_to_add)
                    await log_to_discord(
                         title="Automatischer Rollen-Join",
                         description=f"Neues Mitglied {member.mention} ist dem Police-Server beigetreten und hat die Rollen `LSPD` und `Officer 2` erhalten.",
                         color=discord.Color.gold()
                    )

               # Nickname anpassen
               if academy_member.nick:
                    new_nickname = academy_member.nick
               else:
                    new_nickname = academy_member.name

               await member.edit(nick=new_nickname)
               await log_to_discord(
                    title="Automatischer Nickname-Join",
                    description=f"Der Nickname von {member.mention} wurde automatisch auf `{new_nickname}` gesetzt.",
                    color=discord.Color.blue()
               )
     
     except discord.Forbidden:
          # Dieser Fehler tritt auf, wenn der Bot nicht die Berechtigung hat, den Nickname oder die Rollen zu ändern
          await log_to_discord(
               title="Fehler: Fehlende Berechtigung",
               description=f"Konnte Rollen/Nickname für {member.mention} nicht zuweisen. Überprüfe die Berechtigungen des Bots auf dem Police-Server.",
               color=discord.Color.red()
          )

     except discord.NotFound:
          print(f"Mitglied {member.display_name} nicht auf Academy-Server gefunden.")
     except Exception as e:
          await log_to_discord(
               title="Fehler bei automatischem Rollen-Join",
               description=f"Ein unbekannter Fehler bei der Rollenzuweisung für {member.mention}: {e}",
               color=discord.Color.red()
          )


# --- Server-übergreifende Synchronisation ---
@bot.event
async def on_message(message):
     if message.author.bot:
          return
     if message.channel.id == ACADEMY_MIRROR_CHANNEL_ID:
          target_channel = bot.get_channel(PD_MIRROR_CHANNEL_ID)
          if target_channel:
               embed = discord.Embed(
                    title="Nachricht von Academy-Discord",
                    description=message.content,
                    color=discord.Color.blue()
               )
               embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
               await target_channel.send(embed=embed)


@bot.event
async def on_member_update(before, after):
     police_server = bot.get_guild(PD_SERVER_ID)
     academy_server = bot.get_guild(ACADEMY_SERVER_ID)
     if not police_server or not academy_server:
          print("Ein Server wurde nicht gefunden.")
          return
     other_member = None
     if before.guild.id == PD_SERVER_ID:
          other_member = academy_server.get_member(after.id)
          role_map = POLICE_TO_ACADEMY_ROLES
     elif before.guild.id == ACADEMY_SERVER_ID:
          other_member = police_server.get_member(after.id)
          role_map = ACADEMY_TO_POLICE_ROLES
     else:
          return
     if not other_member:
          return
     for old_role_id, new_role_id in role_map.items():
          old_role = before.guild.get_role(old_role_id)
          new_role = other_member.guild.get_role(new_role_id)
          if not old_role or not new_role:
               continue
          if old_role in after.roles and old_role not in before.roles:
               if new_role not in other_member.roles:
                    await other_member.add_roles(new_role)
                    await log_to_discord(
                         title="Rollen-Synchronisation",
                         description=f"Rolle `{old_role.name}` für {after.mention} auf anderem Server synchronisiert.",
                         color=discord.Color.blue()
                    )
          elif old_role not in after.roles and old_role in before.roles:
               if new_role in other_member.roles:
                    await other_member.remove_roles(new_role)
                    await log_to_discord(
                         title="Rollen-Synchronisation",
                         description=f"Rolle `{old_role.name}` für {after.mention} auf anderem Server entfernt.",
                         color=discord.Color.blue()
                    )

# --- Benutzerdefinierte Berechtigungsprüfung ---
def is_god_user(interaction: discord.Interaction) -> bool:
     return interaction.user.id == GOD_USER_ID

# --- Personalmanagement ---
@tree.command(name="einstellung", description="Registriert einen neuen Officer.")
@app_commands.describe(user="Der Nutzer, der eingestellt wird.")
@app_commands.checks.has_any_role(*ALL_PROMOTION_ROLES)
async def einstellung(interaction: discord.Interaction, user: discord.Member):
     """
     Sendet dem neuen Officer eine Nachricht mit einem Button zur Dateneingabe.
     """
     await interaction.response.defer(ephemeral=True)

     embed = discord.Embed(
          title=f'👮‍♂️ Willkommen in der Academy des LSPD, {user.display_name}!',
          description=(
               "Bevor du offiziell Teil der Los Santos Police Department Academy wirst, "
               "benötigen wir noch einige persönliche Daten für dein Dispatch-Blatt. "
               "Diese Informationen sind entscheidend für deine Akte und den reibungslosen Ablauf. "
               "**Erst nach dem Absenden des Formulars erhältst du Zugriff auf den Discord.**\n\n"
               "Bitte fülle das Formular aus, indem du auf den Button klickst:"
          ),
          color=discord.Color.blue()
     )
     
     # Nutze die neue Fallback-Funktion, um die Nachricht zu senden
     await send_dm_or_fallback(
          interaction,
          user,
          message="Bitte klicke auf den Button, um deine Daten einzutragen.",
          embed=embed,
          view=EinstellungButton(user=user)
     )
     
     await log_to_discord(
          title="Befehl ausgeführt: einstellung",
          description=f"**{interaction.user.display_name}** hat die Registrierung für {user.mention} veranlasst.",
          color=discord.Color.blue()
     )


@tree.command(name="uprank", description="Befördert einen Nutzer.")
@app_commands.describe(user="Der zu befördernde Nutzer.", neuer_rang="Der neue Rang des Nutzers (1-12).")
@app_commands.checks.has_any_role(*ALL_PROMOTION_ROLES)
async def uprank(interaction: discord.Interaction, user: discord.Member, neuer_rang: str):
     await interaction.response.defer()

     if neuer_rang not in PROMOTION_ROLE_MAP:
          await interaction.followup.send(f'Ungültiger Rang: **{neuer_rang}**. Bitte gib eine Nummer zwischen 1 und 12 ein.', ephemeral=True)
          await log_to_discord(
               title="Fehler: Beförderung",
               description=f"{interaction.user.mention} hat einen ungültigen Rang (`{neuer_rang}`) verwendet.",
               color=discord.Color.red()
          )
          return
     
     # DM-Logik an den Anfang verschoben
     if interaction.guild.id == ACADEMY_SERVER_ID and neuer_rang == "2":
          police_server = bot.get_guild(PD_SERVER_ID)
          if police_server:
               police_server_channel = bot.get_channel(PD_MIRROR_CHANNEL_ID) or police_server.text_channels[0]
               invite = await police_server_channel.create_invite(max_uses=1, unique=True)
               dm_text = f"Herzlichen Glückwunsch zur Beförderung zum Officer 2! Du bist jetzt offiziell Teil des LSPD. Hier ist der Einladungslink zum Police-Discord: {invite.url}"
               
               # Nutze die Fallback-Funktion für die Einladungs-DM
               await send_dm_or_fallback(
                    interaction,
                    user,
                    message=dm_text
               )
          else:
               await interaction.followup.send("Police-Server wurde nicht gefunden. Einladungslink konnte nicht erstellt werden.", ephemeral=True)

     if interaction.guild.id == PD_SERVER_ID:
          new_role_id = PROMOTION_ROLE_MAP[neuer_rang][0]
     elif interaction.guild.id == ACADEMY_SERVER_ID:
          new_role_id = PROMOTION_ROLE_MAP[neuer_rang][1]
     else:
          await interaction.followup.send("Dieser Befehl kann nur auf dem Police- oder Academy-Discord verwendet werden.", ephemeral=True)
          return

     new_role = interaction.guild.get_role(new_role_id)
     if not new_role:
          await interaction.followup.send(f'Die Rolle für Rang **{neuer_rang}** wurde auf diesem Server nicht gefunden.', ephemeral=True)
          return

     roles_to_remove = []
     if interaction.guild.id == PD_SERVER_ID:
          all_role_ids = PD_PROMOTION_ROLES
     else:
          all_role_ids = ACADEMY_PROMOTION_ROLES

     for role_id in all_role_ids:
          role = user.guild.get_role(role_id)
          if role and role in user.roles:
               roles_to_remove.append(role)
     
     if roles_to_remove:
          await user.remove_roles(*roles_to_remove)

     await user.add_roles(new_role)

     c.execute("INSERT OR REPLACE INTO users (user_id, rank) VALUES (?, ?)", (user.id, new_role.name))
     conn.commit()

     # Embed für den öffentlichen Update-Kanal (ohne Footer)
     public_embed = discord.Embed(
          title="Offizielle Beförderung",
          color=discord.Color.dark_blue(),
          description=f"Ein Mitglied wurde befördert und hat den Rang gewechselt."
     )
     public_embed.add_field(name="Mitarbeiter", value=user.mention, inline=False)
     public_embed.add_field(name="Neuer Rang", value=f"**`{new_role.name}`**", inline=False)
     
     # Embed für den internen Bot-Log (mit Footer)
     log_embed = public_embed.copy()
     log_embed.set_footer(text=f"Beförderung veranlasst von: {interaction.user.display_name}")

     personal_updates_channel = bot.get_channel(PD_UPDATES_CHANNEL_ID)
     if personal_updates_channel:
          await personal_updates_channel.send(embed=public_embed)
     
     academy_updates_channel = bot.get_channel(ACADEMY_UPDATES_CHANNEL_ID)
     if academy_updates_channel:
          await academy_updates_channel.send(embed=public_embed)

     # Die Bestätigungsmeldung für den Befehlsgeber privat machen
     await interaction.followup.send(f'User {user.mention} wurde erfolgreich zum Rang **{new_role.name}** befördert.', ephemeral=True)
     await log_to_discord(
          title="Befehl ausgeführt: uprank",
          description=f"{interaction.user.mention} hat {user.mention} zum Rang `{new_role.name}` befördert.",
          color=discord.Color.orange()
     )


@tree.command(name="derank", description="Verringert den Rang eines Nutzers.")
@app_commands.describe(user="Der Nutzer, dessen Rang verringert wird.", neuer_rang="Der neue Rang des Nutzers (1-12).")
@app_commands.checks.has_any_role(*ALL_PROMOTION_ROLES)
async def derank(interaction: discord.Interaction, user: discord.Member, neuer_rang: str):
     await interaction.response.defer()
     if neuer_rang not in PROMOTION_ROLE_MAP:
          await interaction.followup.send(f'Ungültiger Rang: **{neuer_rang}**. Bitte gib eine Nummer zwischen 1 und 12 ein.', ephemeral=True)
          await log_to_discord(
               title="Fehler: Herabstufung",
               description=f"{interaction.user.mention} hat einen ungültigen Rang (`{neuer_rang}`) verwendet.",
               color=discord.Color.red()
          )
          return

     if interaction.guild.id == PD_SERVER_ID:
          new_role_id = PROMOTION_ROLE_MAP[neuer_rang][0]
     elif interaction.guild.id == ACADEMY_SERVER_ID:
          new_role_id = PROMOTION_ROLE_MAP[neuer_rang][1]
     else:
          await interaction.followup.send("Dieser Befehl kann nur auf dem Police- oder Academy-Discord verwendet werden.", ephemeral=True)
          return

     new_role = interaction.guild.get_role(new_role_id)
     if not new_role:
          await interaction.followup.send(f'Die Rolle für Rang **{neuer_rang}** wurde auf diesem Server nicht gefunden.', ephemeral=True)
          return
          
     roles_to_remove = []
     if interaction.guild.id == PD_SERVER_ID:
          all_role_ids = PD_PROMOTION_ROLES
     else:
          all_role_ids = ACADEMY_PROMOTION_ROLES

     for role_id in all_role_ids:
          role = user.guild.get_role(role_id)
          if role and role in user.roles:
               roles_to_remove.append(role)
     
     if roles_to_remove:
          await user.remove_roles(*roles_to_remove)

     await user.add_roles(new_role)

     c.execute("INSERT OR REPLACE INTO users (user_id, rank) VALUES (?, ?)", (user.id, new_role.name))
     conn.commit()

     # Embed für den öffentlichen Update-Kanal (ohne Footer)
     public_embed = discord.Embed(
          title="Offizielle Herabstufung",
          color=discord.Color.dark_orange(),
          description=f"Ein Mitglied wurde herabgestuft und hat den Rang gewechselt."
     )
     public_embed.add_field(name="Mitarbeiter", value=user.mention, inline=False)
     public_embed.add_field(name="Neuer Rang", value=f"**`{new_role.name}`**", inline=False)
     
     # Embed für den internen Bot-Log (mit Footer)
     log_embed = public_embed.copy()
     log_embed.set_footer(text=f"Herabstufung veranlasst von: {interaction.user.display_name}")

     personal_updates_channel = bot.get_channel(PD_UPDATES_CHANNEL_ID)
     if personal_updates_channel:
          await personal_updates_channel.send(embed=public_embed)
     
     academy_updates_channel = bot.get_channel(ACADEMY_UPDATES_CHANNEL_ID)
     if academy_updates_channel:
          await academy_updates_channel.send(embed=public_embed)

     # Die Bestätigungsmeldung für den Befehlsgeber privat machen
     await interaction.followup.send(f'Rang von {user.mention} erfolgreich auf **{new_role.name}** herabgesetzt.', ephemeral=True)
     await log_to_discord(
          title="Befehl ausgeführt: derank",
          description=f"{interaction.user.mention} hat {user.mention} auf den Rang `{new_role.name}` herabgestuft.",
          color=discord.Color.orange()
     )


@tree.command(name="kuendigen", description="Entfernt die Ränge eines Nutzers und setzt seinen Status auf gekündigt.")
@app_commands.describe(user="Der Nutzer, dem die Ränge entzogen werden.", grund="Der Grund für die Kündigung.")
@app_commands.checks.has_any_role(*ALL_PROMOTION_ROLES)
async def kuendigen(interaction: discord.Interaction, user: discord.Member, grund: str):
     await interaction.response.defer()

     roles_to_remove = []
     
     if interaction.guild.id == PD_SERVER_ID:
          lspd_role = interaction.guild.get_role(PD_LSPD_ROLE_ID)
          if lspd_role:
               roles_to_remove.append(lspd_role)
               
          all_role_ids = PD_PROMOTION_ROLES
          for role_id in all_role_ids:
               role = user.guild.get_role(role_id)
               if role and role in user.roles:
                    roles_to_remove.append(role)
     elif interaction.guild.id == ACADEMY_SERVER_ID:
          lspd_role = interaction.guild.get_role(ACADEMY_LSPD_ROLE_ID)
          if lspd_role:
               roles_to_remove.append(lspd_role)

          all_role_ids = ACADEMY_PROMOTION_ROLES
          for role_id in all_role_ids:
               role = user.guild.get_role(role_id)
               if role and role in user.roles:
                    roles_to_remove.append(role)

     if roles_to_remove:
          await user.remove_roles(*roles_to_remove, reason=f"Kündigung: {grund}")
     
     c.execute("UPDATE users SET status = 'gekündigt' WHERE user_id = ?", (user.id,))
     conn.commit()

     # Nickname auf dem Academy-Discord zurücksetzen
     academy_guild = bot.get_guild(ACADEMY_SERVER_ID)
     if academy_guild:
         academy_member = academy_guild.get_member(user.id)
         if academy_member:
             try:
                 await academy_member.edit(nick=None)  # Setzt den Nickname auf den globalen Namen zurück
                 await log_to_discord(
                     title="Nickname zurückgesetzt",
                     description=f"Der Nickname von {user.mention} wurde auf dem Academy-Server zurückgesetzt.",
                     color=discord.Color.red()
                 )
             except discord.Forbidden:
                 await log_to_discord(
                     title="Fehler beim Nickname-Zurücksetzen",
                     description=f"Konnte Nickname für {user.mention} auf Academy-Server nicht zurücksetzen. Fehlende Berechtigungen.",
                     color=discord.Color.red()
                 )
             except Exception as e:
                 await log_to_discord(
                     title="Fehler beim Nickname-Zurücksetzen",
                     description=f"Ein Fehler ist beim Zurücksetzen des Nicknames von {user.mention} aufgetreten: {e}",
                     color=discord.Color.red()
                 )

     # Mitglied vom PD-Server kicken, wenn der Befehl dort ausgeführt wird
     if interaction.guild.id == PD_SERVER_ID:
          try:
               await user.kick(reason=f"Kündigung: {grund}")
               await log_to_discord(
                    title="Mitglied gekickt",
                    description=f"Mitglied {user.mention} wurde vom PD-Server gekickt. Grund: {grund}",
                    color=discord.Color.red()
               )
          except discord.Forbidden:
               await log_to_discord(
                    title="Fehler beim Kicken",
                    description=f"Konnte {user.mention} nicht vom PD-Server kicken. Fehlende Berechtigungen.",
                    color=discord.Color.red()
               )
          except Exception as e:
               await log_to_discord(
                    title="Fehler beim Kicken",
                    description=f"Ein Fehler ist beim Kicken von {user.mention} aufgetreten: {e}",
                    color=discord.Color.red()
               )
     
     # Embed für den öffentlichen Update-Kanal (ohne Footer)
     public_embed = discord.Embed(
          title="Offizielle Kündigung",
          color=discord.Color.dark_red(),
          description=f"Ein Mitglied wurde aus dem Dienst entlassen."
     )
     public_embed.add_field(name="Ehemaliger Mitarbeiter", value=user.mention, inline=False)
     public_embed.add_field(name="Grund", value=grund, inline=False)

     # Embed für den internen Bot-Log (mit Footer)
     log_embed = public_embed.copy()
     log_embed.set_footer(text=f"Kündigung veranlasst von: {interaction.user.display_name}")

     personal_updates_channel = bot.get_channel(PD_UPDATES_CHANNEL_ID)
     if personal_updates_channel:
          await personal_updates_channel.send(embed=public_embed)
     
     academy_updates_channel = bot.get_channel(ACADEMY_UPDATES_CHANNEL_ID)
     if academy_updates_channel:
          await academy_updates_channel.send(embed=public_embed)
     
     await interaction.followup.send(f'Die Ränge von {user.mention} wurden entfernt und der Status auf "gekündigt" gesetzt. Das Mitglied wurde vom PD-Server gekickt und der Name auf dem Academy-Server zurückgesetzt.', ephemeral=True)
     await log_to_discord(
          title="Befehl ausgeführt: kuendigen",
          description=f"{interaction.user.mention} hat die Ränge von {user.mention} entfernt. Grund: {grund}",
          color=discord.Color.orange()
     )

@tree.command(name="dv-update", description="Gibt eine offizielle Änderung der Dienstvorschriften bekannt.")
@app_commands.describe(
     geaenderte_paragraphen="Liste geänderter Paragraphen (optional).",
     hinzugefuegte_paragraphen="Liste hinzugefügter Paragraphen (optional).",
     entfernte_paragraphen="Liste entfernter Paragraphen (optional)."
)
@app_commands.checks.has_any_role(*DV_UPDATE_ROLES)
async def dv_update(interaction: discord.Interaction, geaenderte_paragraphen: str = None, hinzugefuegte_paragraphen: str = None, entfernte_paragraphen: str = None):
     await interaction.response.defer(ephemeral=True)

     # Prüfen, ob mindestens ein Feld ausgefüllt ist
     if not geaenderte_paragraphen and not hinzugefuegte_paragraphen and not entfernte_paragraphen:
          await interaction.followup.send("Du musst mindestens einen der Felder `geaenderte_paragraphen`, `hinzugefuegte_paragraphen` oder `entfernte_paragraphen` ausfüllen.", ephemeral=True)
          return

     # Liste der Zielkanäle auf beiden Servern
     target_channel_ids = [PD_DV_UPDATES_CHANNEL_ID, ACADEMY_DV_UPDATES_CHANNEL_ID]
     
     update_sent = False

     for channel_id in target_channel_ids:
          target_channel = bot.get_channel(channel_id)
          
          if not target_channel:
               await log_to_discord(
                    title="Fehler beim Befehl: dv-update",
                    description=f"Der Kanal mit der ID `{channel_id}` wurde nicht gefunden. Ankündigung konnte nicht gesendet werden.",
                    color=discord.Color.red()
               )
               continue
          
          try:
               embed = discord.Embed(
                    title="🚨 Offizielle Änderung der Dienstvorschriften",
                    description="Offizielle Änderungen der Dienstvorschriften wurden bekanntgegeben:",
                    color=discord.Color.dark_red(),
                    timestamp=datetime.now()
               )
               
               if geaenderte_paragraphen:
                    embed.add_field(name="✏️ Geändert", value=geaenderte_paragraphen, inline=False)
               if hinzugefuegte_paragraphen:
                    embed.add_field(name="➕ Hinzugefügt", value=hinzugefuegte_paragraphen, inline=False)
               if entfernte_paragraphen:
                    embed.add_field(name="➖ Entfernt", value=entfernte_paragraphen, inline=False)
               
               embed.set_footer(text=f"Bekanntgegeben von: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

               await target_channel.send(embed=embed)
               update_sent = True

          except Exception as e:
               await interaction.followup.send(f"Ein Fehler ist beim Senden an `{target_channel.name}` aufgetreten: {e}", ephemeral=True)
               await log_to_discord(
                    title="Fehler beim Befehl: dv-update",
                    description=f"Fehler bei der Ankündigung durch {interaction.user.mention} im Kanal {target_channel.mention}: {e}",
                    color=discord.Color.red()
               )
               continue

     if update_sent:
          await interaction.followup.send(f"Die Dienstvorschriften-Änderung wurde erfolgreich in beiden Kanälen veröffentlicht.", ephemeral=True)
          
          await log_to_discord(
               title="Befehl ausgeführt: dv-update",
               description=f"**{interaction.user.display_name}** hat eine Dienstvorschriften-Änderung in beiden Discord-Servern angekündigt.",
               color=discord.Color.gold()
          )

@tree.command(name="dienstbesprechung", description="Kündigt eine Dienstbesprechung für beide Server an.")
@app_commands.describe(
     datum="Datum der Besprechung (TT.MM.JJJJ).",
     uhrzeit="Uhrzeit der Besprechung (HH:MM).",
     ort="Ort der Besprechung (z.B. Sprachkanal, Ingame-Ort)."
)
@app_commands.checks.has_any_role(*DV_UPDATE_ROLES)
async def dienstbesprechung(interaction: discord.Interaction, datum: str, uhrzeit: str, ort: str):
    await interaction.response.defer(ephemeral=True)

    try:
        # Versuch, Datum und Uhrzeit zu validieren und zu parsen
        combined_dt_str = f"{datum} {uhrzeit}"
        parsed_dt = parse(combined_dt_str, dayfirst=True)
        # Erstelle eine formatierte Zeitangabe für den Embed-Footer
        timestamp_formatted = parsed_dt.strftime("%d.%m.%Y um %H:%M Uhr")
    except (ParserError, ValueError):
        await interaction.followup.send(
            "Ungültiges Datums- oder Uhrzeitformat. Bitte verwende `TT.MM.JJJJ` und `HH:MM`.", 
            ephemeral=True
        )
        await log_to_discord(
            title="Fehler beim Befehl: dienstbesprechung",
            description=f"Ungültiges Format durch {interaction.user.mention}: Datum='{datum}', Uhrzeit='{uhrzeit}'",
            color=discord.Color.red()
        )
        return

    # Liste der Zielkanäle auf beiden Servern
    target_channel_ids = [PD_BESPRECHUNG_CHANNEL_ID, ACADEMY_BESPRECHUNG_CHANNEL_ID]
    
    besprechung_sent = False

    for channel_id in target_channel_ids:
        target_channel = bot.get_channel(channel_id)

        if not target_channel:
            await log_to_discord(
                title="Fehler beim Befehl: dienstbesprechung",
                description=f"Der Kanal mit der ID `{channel_id}` wurde nicht gefunden. Ankündigung konnte nicht gesendet werden.",
                color=discord.Color.red()
            )
            continue
        
        try:
            embed = discord.Embed(
                title="📢 Offizielle Dienstbesprechung",
                description="Eine verbindliche Dienstbesprechung wurde angekündigt. Die Anwesenheit ist für alle Mitarbeiter verpflichtend.",
                color=discord.Color.blue(),
                timestamp=parsed_dt
            )
            embed.add_field(name="Datum", value=timestamp_formatted, inline=False)
            embed.add_field(name="Ort", value=ort, inline=False)
            embed.set_footer(text=f"Angekündigt von: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

            await target_channel.send(embed=embed)
            besprechung_sent = True

        except Exception as e:
            await interaction.followup.send(f"Ein Fehler ist beim Senden an `{target_channel.name}` aufgetreten: {e}", ephemeral=True)
            await log_to_discord(
                title="Fehler beim Befehl: dienstbesprechung",
                description=f"Fehler bei der Ankündigung durch {interaction.user.mention} im Kanal {target_channel.mention}: {e}",
                color=discord.Color.red()
            )
            continue
    
    if besprechung_sent:
        await interaction.followup.send("Die Dienstbesprechung wurde erfolgreich in beiden Kanälen angekündigt.", ephemeral=True)
        await log_to_discord(
            title="Befehl ausgeführt: dienstbesprechung",
            description=f"**{interaction.user.display_name}** hat eine Dienstbesprechung für den {timestamp_formatted} angekündigt.",
            color=discord.Color.blue()
        )


@tree.command(name="clear", description="Löscht eine bestimmte Anzahl von Nachrichten im aktuellen Kanal.")
@app_commands.describe(amount="Die Anzahl der zu löschenden Nachrichten (maximal 100).")
@app_commands.check(is_god_user)
async def clear_messages(interaction: discord.Interaction, amount: int):
     """
     Löscht die angegebene Anzahl von Nachrichten aus dem aktuellen Kanal.
     """
     if amount <= 0 or amount > 100:
          await interaction.response.send_message("Die Anzahl muss zwischen 1 und 100 liegen.", ephemeral=True)
          return
     
     await interaction.response.defer(ephemeral=True)
     
     try:
          deleted = await interaction.channel.purge(limit=amount + 1)
          await interaction.followup.send(f'**{len(deleted) - 1}** Nachrichten erfolgreich gelöscht.', ephemeral=True)
          
          await log_to_discord(
               title="Befehl ausgeführt: clear",
               description=f"**{interaction.user.display_name}** hat **{len(deleted) - 1}** Nachrichten in Kanal `{interaction.channel.name}` gelöscht.",
               color=discord.Color.red()
          )
          
     except Exception as e:
          await interaction.followup.send(f"Beim Löschen der Nachrichten ist ein Fehler aufgetreten: {e}", ephemeral=True)
          await log_to_discord(
               title="Fehler beim Befehl: clear",
               description=f"Fehler beim Löschen von Nachrichten in Kanal `{interaction.channel.name}`: {e}",
               color=discord.Color.red()
          )


# --- Fehlerbehandlung für Befehle ---
@tree.error
async def on_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
     if isinstance(error, app_commands.MissingAnyRole) or isinstance(error, app_commands.CheckFailure):
          if interaction.response.is_done():
               await interaction.followup.send("Du hast nicht die erforderlichen Berechtigungen für diesen Befehl.", ephemeral=True)
          else:
               await interaction.response.send_message("Du hast nicht die erforderlichen Berechtigungen für diesen Befehl.", ephemeral=True)
     else:
          print(f"Ein Fehler ist aufgetreten: {error}")
          if interaction.response.is_done():
               await interaction.followup.send(f"Ein unerwarteter Fehler ist aufgetreten: {error}", ephemeral=True)
          else:
               await interaction.response.send_message(f"Ein unerwarteter Fehler ist aufgetreten: {error}", ephemeral=True)
     
     await log_to_discord(
          title="Befehlsfehler",
          description=f"Ein Fehler ist bei der Ausführung von `{interaction.command.name}` aufgetreten. \n**Befehlsgeber:** {interaction.user.mention}\n**Fehler:** {error}",
          color=discord.Color.red()
     )


# --- Bot starten ---
bot.run(TOKEN)