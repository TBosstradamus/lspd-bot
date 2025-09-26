import sqlite3
import config

def get_db_connection():
    """Stellt eine Verbindung zur Datenbank her und gibt das Connection-Objekt zurück."""
    conn = sqlite3.connect(config.DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Initialisiert die Datenbank und erstellt die Tabellen, falls sie nicht existieren."""
    conn = get_db_connection()
    c = conn.cursor()

    # Tabelle für Benutzerdaten
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY,
                 rank TEXT,
                 status TEXT DEFAULT 'aktiv'
               )''')

    # Tabelle für Registrierungen (falls in Zukunft benötigt)
    c.execute('''CREATE TABLE IF NOT EXISTS registrations (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 event_name TEXT,
                 registered_at TEXT
               )''')

    conn.commit()
    conn.close()
    print("Datenbank erfolgreich initialisiert.")