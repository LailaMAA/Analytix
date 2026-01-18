import pandas as pd
import sys
import os
from datetime import datetime
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.structure_db import (
    SessionLocal, init_enterprise_db, 
    DimRegion, DimVehicle, DimFailureType, DimPart, DimDate, 
    FactVehicleFailure
)

def etl_process(csv_path="data/raw/data_test_real.csv"):
    print("🚀 ETL Started: Migrating CSV to FACT_VEHICLE_FAILURE Star Schema...")
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return

    # 1. Init DB
    init_enterprise_db()
    session = SessionLocal()
    
    # 2. Extract
    df = pd.read_csv(csv_path)
    # Normalize column names for robust matching
    df.columns = df.columns.str.strip()
    
    # Mapping Dictionary (CSV -> Internal Key)
    # This helps even if we access by strict name later, but allows us to handle variations if needed
    
    print(f"📦 Data Extracted: {len(df)} rows. Columns: {list(df.columns)}")
    
    # 3. Load Dimensions
    
    # --- DIM_REGION ---
    # CSV: region -> region_name, ville -> city_name
    regions_map = {} 
    unique_locs = df[['region', 'ville']].drop_duplicates().fillna("Unknown")
    
    for _, row in unique_locs.iterrows():
        r_name = str(row['region'])
        c_name = str(row['ville'])
        key = (r_name, c_name)
        
        existing = session.query(DimRegion).filter_by(region_name=r_name, city_name=c_name).first()
        if not existing:
            obj = DimRegion(region_name=r_name, city_name=c_name)
            session.add(obj)
            session.flush()
            regions_map[key] = obj.region_id
        else:
            regions_map[key] = existing.region_id

    # --- DIM_FAILURE_TYPE ---
    # CSV: type_panne_moteur -> failure_name
    fail_map = {}
    if 'type_panne_moteur' in df.columns:
        unique_fails = df['type_panne_moteur'].dropna().unique()
        for fname in unique_fails:
            fname = str(fname).strip()
            existing = session.query(DimFailureType).filter_by(failure_name=fname).first()
            if not existing:
                obj = DimFailureType(failure_name=fname)
                session.add(obj)
                session.flush()
                fail_map[fname] = obj.failure_type_id
            else:
                fail_map[fname] = existing.failure_type_id
    
    # --- DIM_PART ---
    # CSV: Piece_defectuee -> part_name
    part_map = {}
    if 'Piece_defectuee' in df.columns:
        unique_parts = df['Piece_defectuee'].dropna().unique()
        for pname in unique_parts:
            pname = str(pname).strip()
            existing = session.query(DimPart).filter_by(part_name=pname).first()
            if not existing:
                obj = DimPart(part_name=pname)
                session.add(obj)
                session.flush()
                part_map[pname] = obj.part_id
            else:
                part_map[pname] = existing.part_id

    # --- DIM_VEHICLE ---
    # CSV Mapping: 
    # vehicle_id -> original_vehicle_id
    # Model_moteur -> engine_model
    # age_vehicule -> vehicle_age
    # Garantie -> under_warranty
    # Date_mise_service -> service_start_date
    
    veh_map = {}
    unique_vehs = df.drop_duplicates(subset=['vehicle_id'])
    
    for _, row in unique_vehs.iterrows():
        vid = str(row['vehicle_id'])
        
        existing = session.query(DimVehicle).filter_by(original_vehicle_id=vid).first()
        if not existing:
            obj = DimVehicle(
                original_vehicle_id=vid,
                engine_model=str(row.get('Model_moteur', 'Unknown')),
                vehicle_age=float(row.get('age_vehicule', 0)),
                under_warranty=str(row.get('Garantie', 'Unknown')),
                service_start_date=str(row.get('Date_mise_service', ''))
            )
            session.add(obj)
            session.flush()
            veh_map[vid] = obj.vehicle_id
        else:
            veh_map[vid] = existing.vehicle_id
            
    session.commit()

    # --- FACT_VEHICLE_FAILURE ---
    # Mapping remainder columns to Fact
    
    facts_count = 0
    today_iso = datetime.now().strftime("%Y-%m-%d")
    
    # Create a Default Date Dim for today (Simulation of 'Extraction Date' or use record date if available)
    # Since CSV doesn't have a specific "Event Date" for every row (maybe date_derniere_maintenance?)
    # We will use date_derniere_maintenance if valid, else today.
    
    for _, row in df.iterrows():
        # Resolve FKs
        vid = str(row['vehicle_id'])
        reg = str(row.get('region', 'Unknown'))
        city = str(row.get('ville', 'Unknown'))
        fname = str(row.get('type_panne_moteur', ''))
        pname = str(row.get('Piece_defectuee', ''))
        if pname == 'nan': pname = ''
        
        # Date Handling
        # We try to use date_derniere_maintenance as the event date
        maint_date = str(row.get('date_derniere_maintenance', today_iso))
        
        # Get/Create Date Dim
        # (Simplified: Just using today or maint_date string as lookup? 
        #  Ideally we parse the date to get year/month/day)
        
        fact = FactVehicleFailure(
            vehicle_id=veh_map.get(vid),
            region_id=regions_map.get((reg, city)),
            failure_type_id=fail_map.get(fname),
            part_id=part_map.get(pname),
            # date_id -> skipped for simplicity or could implement lookup
            
            # Measures
            total_mileage=float(row.get('kilometrage_total', 0)),
            engine_rpm=float(row.get('engine_rpm', 0)),
            engine_load=float(row.get('engine_load', 0)),
            engine_temperature=float(row.get('engine_temperature', 0)),
            oil_temperature=float(row.get('oil_temperature', 0)),
            oil_pressure=float(row.get('oil_pressure', 0)),
            fuel_pressure=float(row.get('fuel_pressure', 0)),
            
            days_before_failure=int(row.get('jours_avant_panne', 0)) if pd.notna(row.get('jours_avant_panne')) else 0,
            last_maintenance_date=maint_date
        )
        session.add(fact)
        facts_count += 1
        
    session.commit()
    print(f"✅ ETL Succeeded! {facts_count} rows loaded into FACT_VEHICLE_FAILURE.")
    session.close()

if __name__ == "__main__":
    etl_process()
