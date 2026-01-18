import pandas as pd
import sys
import os
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.database import SessionLocal, init_db, VehicleData, engine

def migrate_csv_to_db(csv_path="data/raw/data_test_real.csv"):
    """
    Reads a CSV file and inserts its content into the VehicleData table.
    """
    print(f"--- Migration CSV -> DB ---")
    print(f"Source: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"Erreur: Fichier {csv_path} introuvable.")
        return

    # 1. Initialize DB (Create tables if not exist)
    init_db()
    
    # 2. Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Erreur lecture CSV: {e}")
        return
        
    print(f"Lignes trouvées: {len(df)}")
    
    # 3. Insert into DB
    session = SessionLocal()
    try:
        # Check if data already exists to avoid duplication (simple check)
        count = session.query(VehicleData).count()
        if count > 0:
            print(f"Attention: La table contient déjà {count} entrées.")
            # Optional: session.query(VehicleData).delete()
            
        records = []
        for _, row in df.iterrows():
            record = VehicleData(
                vehicle_id=str(row.get("vehicle_id", "")),
                Model_moteur=str(row.get("Model_moteur", "")),
                age_vehicule=float(row.get("age_vehicule", 0)),
                kilometrage_total=float(row.get("kilometrage_total", 0)),
                Garantie=str(row.get("Garantie", "")),
                date_derniere_maintenance=str(row.get("date_derniere_maintenance", "")),
                Date_mise_service=str(row.get("Date_mise_service", "")),
                engine_rpm=float(row.get("engine_rpm", 0)),
                engine_load=float(row.get("engine_load", 0)),
                engine_temperature=float(row.get("engine_temperature", 0)),
                oil_temperature=float(row.get("oil_temperature", 0)),
                oil_pressure=float(row.get("oil_pressure", 0)),
                fuel_pressure=float(row.get("fuel_pressure", 0)),
                region=str(row.get("region", "")),
                ville=str(row.get("ville", "")),
                Piece_defectuee=str(row.get("Piece_defectuee", "")),
                piece_impacte=str(row.get("piece_impacte", "")),
                type_panne_moteur=str(row.get("type_panne_moteur", "")),
                jours_avant_panne=int(row.get("jours_avant_panne", 0)) if pd.notna(row.get("jours_avant_panne")) else None
            )
            records.append(record)
        
        # Bulk insert is faster
        session.bulk_save_objects(records)
        session.commit()
        print(f"[OK] {len(records)} lignes insérées dans la base de données.")
        
    except Exception as e:
        session.rollback()
        print(f"Erreur lors de l'insertion: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # Check if arguments provided
    if len(sys.argv) > 1:
        migrate_csv_to_db(sys.argv[1])
    else:
        migrate_csv_to_db()
