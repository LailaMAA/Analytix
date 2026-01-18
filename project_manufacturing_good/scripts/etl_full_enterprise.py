import pandas as pd
import sys
import os
import random
from datetime import datetime, timedelta
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.structure_db import (
    SessionLocal, init_enterprise_db, 
    DimRegion, DimVehicle, DimFailureType, DimPart, DimDate, 
    DimCustomer, DimDealer,
    FactVehicleFailure, FactInventory, FactMaintenanceLog
)

# --- CONFIG ---
CSV_FILE = "data/raw/Pannes_moteurs_equilibre_Maroc.csv"

# --- GENERATORS ---
FAKE_COMPANIES = ["Maghreb Logistics", "Casa Transport", "Tanger Fret", "Atlas Tours", "Royal Fleet"]
FAKE_NAMES = ["Ahmed", "Fatima", "Youssef", "Khadija", "Omar", "Amina", "Hassan", "Zineb"]
FAKE_SURNAMES = ["Benali", "Alami", "Idrissi", "Tazi", "Berrada", "Fassi", "Chraibi"]
DEALER_SUFFIXES = ["Motors", "Auto Center", "Premium Garage", "Expert Service"]

def generate_customer():
    is_b2b = random.random() < 0.3
    if is_b2b:
        name = random.choice(FAKE_COMPANIES) + " " + str(random.randint(1, 99))
        ctype = "B2B"
    else:
        name = random.choice(FAKE_NAMES) + " " + random.choice(FAKE_SURNAMES)
        ctype = "B2C"
    return name, ctype

def etl_full_enterprise():
    print("🚀 ETL Started: Building Full Automotive ERP...")
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ File not found: {CSV_FILE}")
        return

    init_enterprise_db()
    session = SessionLocal()
    
    # 1. READ CSV (Real Data)
    # -----------------------
    print(f"📂 Reading {CSV_FILE}...")
    try:
        # utf-8-sig automatically handles the BOM (\ufeff)
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig', sep=None, engine='python')
    except Exception as e:
        print(f"⚠️ UTF-8-SIG failed ({e}), trying latin1...")
        df = pd.read_csv(CSV_FILE, encoding='latin1', sep=None, engine='python')
        
    # Clean columns: strip whitespace, lower case match map? No, we stick to strict names but clean them.
    df.columns = df.columns.str.strip()
    
    # Explicit renaming for known issues
    rename_map = {
        'ï»¿vehicle_id': 'vehicle_id',
        'Model_moteur': 'Model_moteur',
        'region': 'region',
        'ville': 'ville'
    }
    # If standard columns are lowercased or slightly diff
    for col in df.columns:
        if 'vehicle' in col.lower() and 'id' in col.lower():
            rename_map[col] = 'vehicle_id'
            
    df = df.rename(columns=rename_map)
    
    print(f"📦 Loaded {len(df)} rows. Columns found: {list(df.columns)}")
    
    required = ['vehicle_id']
    for r in required:
        if r not in df.columns:
            print(f"❌ CRITICAL: Column '{r}' missing. Available: {list(df.columns)}")
            return

    # 2. POPULATE CORE DIMENSIONS (Real)
    # -----------------------
    print("Store Core Dimensions...")
    
    # --- DIM_REGION ---
    regions_map = {}
    # Fallback columns if names differ
    col_reg = 'region'
    col_city = 'ville' 
    if 'region' not in df.columns: # Demo mode fallback
         df['region'] = 'Inconnue'
         df['ville'] = 'Inconnue'

    unique_locs = df[[col_reg, col_city]].drop_duplicates().fillna("Unknown")
    
    # Also generate dealers for each region/city
    dealers_map = {} # (region_id) -> [dealer_ids]

    for _, row in unique_locs.iterrows():
        r_name = str(row[col_reg])
        c_name = str(row[col_city])
        
        # Region
        existing = session.query(DimRegion).filter_by(region_name=r_name, city_name=c_name).first()
        if not existing:
            obj = DimRegion(region_name=r_name, city_name=c_name)
            session.add(obj)
            session.flush()
            rid = obj.region_id
        else:
            rid = existing.region_id
        regions_map[(r_name, c_name)] = rid
        
        # Create 1-2 Dealers per City (Synthetic)
        if rid not in dealers_map:
            dealers_map[rid] = []
            num_dealers = random.randint(1, 2)
            for _ in range(num_dealers):
                d_name = f"{c_name} {random.choice(DEALER_SUFFIXES)}"
                dealer = DimDealer(
                    name=d_name,
                    region_id=rid,
                    technician_count=random.randint(5, 20),
                    daily_capacity=random.randint(10, 50)
                )
                session.add(dealer)
                session.flush()
                dealers_map[rid].append(dealer.dealer_id)

    # --- DIM_FAILURE_TYPE ---
    fail_map = {}
    col_fail = 'type_panne_moteur'
    if col_fail in df.columns:
        for fname in df[col_fail].dropna().unique():
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
    part_map = {}
    col_part = 'Piece_defectuee'
    if col_part in df.columns:
        for pname in df[col_part].dropna().unique():
            pname = str(pname).strip()
            if pname == 'nan': continue
            existing = session.query(DimPart).filter_by(part_name=pname).first()
            if not existing:
                cost = random.randint(50, 800) # Synthetic cost
                obj = DimPart(part_name=pname, category="Mechanical", unit_cost=cost)
                session.add(obj)
                session.flush()
                part_map[pname] = obj.part_id
            else:
                part_map[pname] = existing.part_id

    # 3. POPULATE VEHICLES & CUSTOMERS (Mixed)
    # -----------------------
    veh_map = {}
    
    # Pre-generate some customers
    customers = []
    for _ in range(50): # 50 simulated customers owning the fleet
        name, ctype = generate_customer()
        cust = DimCustomer(
            name=name, type=ctype, 
            email=f"contact@{name.replace(' ', '').lower()}.com", 
            phone=f"+2126{random.randint(10000000, 99999999)}"
        )
        session.add(cust)
        customers.append(cust)
    session.flush()
    
    unique_v = df.drop_duplicates(subset=['vehicle_id'])
    for _, row in unique_v.iterrows():
        vid = str(row['vehicle_id']).strip()
        if not vid: continue
        
        # Check if we already processed this ID (in case drop_duplicates wasn't perfect due to whitespace)
        if vid in veh_map:
            continue
            
        # Assign random customer
        owner = random.choice(customers)
        
        existing = session.query(DimVehicle).filter_by(original_vehicle_id=vid).first()
        if not existing:
            obj = DimVehicle(
                original_vehicle_id=vid,
                engine_model=str(row.get('Model_moteur', 'Unknown')),
                vehicle_age=float(row.get('age_vehicule', 0)),
                under_warranty=str(row.get('Garantie', 'Unknown')),
                service_start_date=str(row.get('Date_mise_service', '')),
                customer_id=owner.customer_id
            )
            session.add(obj)
            session.flush()
            veh_map[vid] = obj.vehicle_id
        else:
            veh_map[vid] = existing.vehicle_id

    # 4. POPULATE FAILURE FACTS (Real)
    # -----------------------
    facts_count = 0
    today_iso = datetime.now().strftime("%Y-%m-%d")
    
    for _, row in df.iterrows():
        vid = veh_map.get(str(row['vehicle_id']))
        rkey = (str(row[col_reg]), str(row[col_city]))
        rid = regions_map.get(rkey)
        fid = fail_map.get(str(row.get(col_fail, '')).strip())
        pid = part_map.get(str(row.get(col_part, '')).strip())
        
        fact = FactVehicleFailure(
            vehicle_id=vid,
            region_id=rid,
            failure_type_id=fid,
            part_id=pid,
            
            total_mileage=float(row.get('kilometrage_total', 0)),
            engine_rpm=float(row.get('engine_rpm', 0)),
            engine_temperature=float(row.get('engine_temperature', 0)),
            oil_pressure=float(row.get('oil_pressure', 0)),
            days_before_failure=int(row.get('jours_avant_panne', 0) or 0),
            last_maintenance_date=str(row.get('date_derniere_maintenance', today_iso))
        )
        session.add(fact)
        facts_count += 1
        
    # 5. POPULATE SYNTHETIC INVENTORY & LOGS
    # -----------------------
    print("⚙️ Generating Synthetic Business Data...")
    
    # Inventory: For each dealer, add stock for known parts
    inv_count = 0
    all_part_ids = list(part_map.values())
    
    for rid, d_list in dealers_map.items():
        for did in d_list:
            # Each dealer stocks some parts
            for pid in all_part_ids:
                if random.random() > 0.3: # 70% chance to stock a part
                    stock = random.randint(0, 50)
                    fact_inv = FactInventory(
                        dealer_id=did,
                        part_id=pid,
                        current_stock=stock,
                        reorder_level=10,
                        last_restock_date=today_iso
                    )
                    session.add(fact_inv)
                    inv_count += 1
                    
    # Maintenance Logs: Fake history
    log_count = 0
    all_veh_ids = list(veh_map.values())
    all_dealer_ids = [d for sublist in dealers_map.values() for d in sublist]
    
    if all_dealer_ids and all_veh_ids:
        for vid in all_veh_ids:
            # 1 to 3 past logs per vehicle
            for _ in range(random.randint(1, 3)):
                log = FactMaintenanceLog(
                    vehicle_id=vid,
                    dealer_id=random.choice(all_dealer_ids),
                    date_iso=(datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
                    description=random.choice(["Routine Inspection", "Oil Change", "Tire Rotation", "Brake Check"]),
                    cost=float(random.randint(100, 1000))
                )
                session.add(log)
                log_count += 1

    session.commit()
    print(f"✅ Full ERP Build Complete!")
    print(f"   - Real Failures: {facts_count}")
    print(f"   - Synthetic Customers: {len(customers)}")
    print(f"   - Synthetic Inventory Records: {inv_count}")
    print(f"   - Synthetic Maintenance Logs: {log_count}")
    session.close()

if __name__ == "__main__":
    etl_full_enterprise()
