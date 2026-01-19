import sqlite3
import os

# Path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "Companyx_database.db")

def enable_wal():
    if not os.path.exists(DB_PATH):
        print(f"Erreur : La base de données n'existe pas à l'emplacement : {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"Optimisation de la base de données (WAL Mode)...")
        
        # Enable Write-Ahead Logging
        cursor.execute("PRAGMA journal_mode=WAL;")
        mode = cursor.fetchone()[0]
        
        print(f"✅ Mode Journal modifié à : {mode.upper()}")
        print("Cela permettra à l'Agent IA et à l'API de travailler en même temps sans bloquer la base.")
        
        conn.close()
        
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

if __name__ == "__main__":
    enable_wal()
