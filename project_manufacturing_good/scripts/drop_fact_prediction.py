import sqlite3
import os

# Path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "Companyx_database.db")

def clear_table():
    if not os.path.exists(DB_PATH):
        print(f"Erreur : La base de données n'existe pas à l'emplacement : {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"Nettoyage de la base de données : {DB_PATH}")
        
        # Clear the table (DELETE FROM) instead of dropping it
        cursor.execute("DELETE FROM FACT_PREDICTION")
        print("✅ La table 'FACT_PREDICTION' a été vidée (toutes les lignes supprimées).")
        
        conn.commit()
        conn.close()
        
        print("ℹ️  Note : La structure de la table est conservée.")
        
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

if __name__ == "__main__":
    clear_table()
