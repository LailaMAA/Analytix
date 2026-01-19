from database import DatabaseManager
import pandas as pd

def verify_connection():
    print("--- Vérification de la connexion à la base de données ---")
    db = DatabaseManager()
    
    # 1. Check connection
    if db.engine:
        print(f"✅ Moteur SQLAlchemy créé avec succès : {db.connection_string}")
    else:
        print("❌ Échec de la création du moteur.")
        return

    # 2. Fetch data
    df = db.fetch_predictions()
    
    if df is not None and not df.empty:
        print(f"\n✅ Données récupérées avec succès.")
        print("📋 Colonnes disponibles :")
        for col in df.columns:
            print(f" - {col}")
        print("\n🔍 Aperçu des 5 premières lignes :")
        print(df.head().to_string())
        
        # Verify it's not dummy data (dummy data usually has nice round numbers or specific patterns, 
        # but here we just check if it matches what we expect from the DB file)
        print("\n🌍 Répartition par région (pour confirmation) :")
        print(df['region'].value_counts())
    else:
        print("❌ Aucune donnée trouvée ou erreur lors de la requête.")

if __name__ == "__main__":
    verify_connection()
