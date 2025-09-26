# --- Discord-Konfiguration ---

# Dein Bot-Token
TOKEN = "MTQxNzk3OTgwNjM0MzEwMjYxNQ.GXffq8.hZh7Yk7wOhCevrtob1-Ka7oKMX51vbRT5GwlMg"

# Deine Benutzer-ID für volle Berechtigungen (God-User)
GOD_USER_ID = 675898941262528512

# Datenbank-Datei
DATABASE_FILE = "lspd_assistant.db"

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