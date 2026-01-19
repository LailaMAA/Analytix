import sqlite3
import os

# Path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "Companyx_database.db")

def clear_notifications():
    if not os.path.exists(DB_PATH):
        print(f"Erreur : La base de données n'existe pas à l'emplacement : {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"Nettoyage des notifications...")
        
        # Clear the table (DELETE FROM)
        cursor.execute("DELETE FROM FACT_NOTIFICATION")
        count = cursor.rowcount
        print(f"✅ La table 'FACT_NOTIFICATION' a été vidée.")
        print("ℹ️  Toutes les notifications ont été supprimées.")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

if __name__ == "__main__":
    clear_notifications()
