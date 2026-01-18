import sqlite3
import pandas as pd
import os

def populate_companyx_training():
    db_path = 'Companyx_database.db'
    csv_path = 'data/raw/Pannes_moteurs_equilibre_Maroc.csv'
    
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path).fillna(0)
    
    # Rename 'ville' to 'city' to match DB schema if necessary, 
    # but let's check the schema we found earlier:
    # training_id, vehicle_id, engine_model, vehicle_age, total_mileage, engine_rpm, 
    # engine_load, engine_temperature, oil_temperature, oil_pressure, fuel_pressure, 
    # last_maintenance_date, warranty, service_start_date, region, city, 
    # failure_type, days_before_failure, defective_part, impacted_part
    
    # Mapping CSV to DB
    # CSV columns: ['vehicle_id', 'engine_model', 'vehicle_age', 'total_mileage', 'engine_rpm', 
    # 'engine_load', 'engine_temperature', 'oil_temperature', 'oil_pressure', 'fuel_pressure', 
    # 'last_maintenance_date', 'days_before_failure', 'warranty', 'defective_part', 
    # 'service_start_date', 'failure_type', 'impacted_part', 'region', 'ville']
    
    df = df.rename(columns={'ville': 'city'})
    
    # Ensure all columns exist in DF as expected by DB
    expected_cols = [
        'vehicle_id', 'engine_model', 'vehicle_age', 'total_mileage', 'engine_rpm', 
        'engine_load', 'engine_temperature', 'oil_temperature', 'oil_pressure', 'fuel_pressure', 
        'last_maintenance_date', 'warranty', 'service_start_date', 'region', 'city', 
        'failure_type', 'days_before_failure', 'defective_part', 'impacted_part'
    ]
    
    # Select only relevant columns
    df = df[expected_cols]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Clearing FACT_TRAINING_DATA table...")
        cursor.execute("DELETE FROM FACT_TRAINING_DATA")
        conn.commit()
        
        print(f"Inserting {len(df)} rows into FACT_TRAINING_DATA...")
        df.to_sql('FACT_TRAINING_DATA', conn, if_exists='append', index=False)
        conn.commit()
        
        print("SUCCESS: FACT_TRAINING_DATA table populated.")
        
        # Verify count
        cursor.execute("SELECT COUNT(*) FROM FACT_TRAINING_DATA")
        count = cursor.fetchone()[0]
        print(f"Total rows in FACT_TRAINING_DATA: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_companyx_training()
