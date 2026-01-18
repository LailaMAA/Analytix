import pandas as pd
import os
import sys
from sqlalchemy.orm import sessionmaker
from api.database import engine, SessionLocal
from api.structure_db import FactTrainingData, init_enterprise_db

def populate_training_only():
    print("START: Populating FACT_TRAINING_DATA (Maroc Dataset)")
    
    # Ensure tables exist
    init_enterprise_db()
    
    session = SessionLocal()
    path_fail = "data/raw/Pannes_moteurs_equilibre_Maroc.csv"
    
    if not os.path.exists(path_fail):
        print(f"ERROR: File not found at {path_fail}")
        return

    try:
        # Clear existing data in this table if needed (optional, but usually good for a clean sync)
        print("Cleaning existing records in FACT_TRAINING_DATA...")
        session.query(FactTrainingData).delete()
        session.commit()

        print(f"Reading {path_fail}...")
        df = pd.read_csv(path_fail).fillna(0)
        
        objects = []
        count = 0
        
        for idx, row in df.iterrows():
            try:
                objects.append(FactTrainingData(
                    vehicle_id=str(row.get('vehicle_id', '')),
                    engine_model=str(row.get('Model_moteur', 'Inconnu')),
                    vehicle_age=float(row.get('age_vehicule', 0)),
                    total_mileage=float(row.get('kilometrage_total', 0)),
                    engine_rpm=float(row.get('engine_rpm', 0)),
                    engine_load=float(row.get('engine_load', 0)),
                    engine_temperature=float(row.get('engine_temperature', 0)),
                    oil_temperature=float(row.get('oil_temperature', 0)),
                    oil_pressure=float(row.get('oil_pressure', 0)),
                    fuel_pressure=float(row.get('fuel_pressure', 0)),
                    last_maintenance_date=str(row.get('date_derniere_maintenance', '')),
                    warranty=str(row.get('Garantie', 'Non')),
                    service_start_date=str(row.get('Date_mise_service', '')),
                    region=str(row.get('region', 'Maroc')),
                    city=str(row.get('ville', '')),
                    failure_type=str(row.get('type_panne_moteur', '')),
                    days_before_failure=int(float(row.get('jours_avant_panne', 0))),
                    defective_part=str(row.get('Piece_defectuee', '')),
                    impacted_part=str(row.get('piece_impacte', ''))
                ))
                
                if len(objects) >= 5000:
                    session.bulk_save_objects(objects)
                    session.commit()
                    count += len(objects)
                    print(f"Inserted {count} rows...")
                    objects = []
            except Exception as e:
                if idx < 5: print(f"Error at row {idx}: {e}")
                continue
        
        if objects:
            session.bulk_save_objects(objects)
            session.commit()
            count += len(objects)
            
        print(f"SUCCESS: Populated {count} rows into FACT_TRAINING_DATA.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    populate_training_only()
