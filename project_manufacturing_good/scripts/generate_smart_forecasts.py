import sqlite3
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "Companyx_database.db"

def generate_smart_forecasts():
    print("🧠 Generating SMART Forecasts from Predictions...")
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Clear old random forecasts (Reset for clear logic)
    conn.execute("DELETE FROM FACT_HR_FORECAST")
    conn.execute("DELETE FROM FACT_INVENTORY_FORECAST")
    conn.commit()

    # 2. Get FAILURE -> IMPACT logic (Metadata)
    # Estimate Technical Impact: 1 Failure = X technician hours required
    # Estimate Parts Impact: 1 Failure = 1 Unit of 'defective_part' needed
    
    # --- A. HR FORECAST (Technicians Needed) ---
    # Logic: 
    # High Probability Failure (>75%) = 100% need
    # Medium Probability Failure (>50%) = 50% weighted need
    # Capacity per Technician = 8 hours/day
    # Avg Repair Time = 4 hours
    
    print("  -> Calculating HR Needs...")
    sql_hr = """
        SELECT region, COUNT(*) as failure_count, SUM(failure_probability) as total_risk_score
        FROM FACT_PREDICTION
        WHERE failure_probability > 0.5
        GROUP BY region
    """
    df_hr = pd.read_sql_query(sql_hr, conn)
    
    # Map Region string to IDs
    # First, get region map
    cur = conn.cursor()
    cur.execute("SELECT region_name, region_id FROM DIM_REGION")
    region_map = {row[0].lower().strip(): row[1] for row in cur.fetchall()}
    
    forecasts_hr = []
    
    for _, row in df_hr.iterrows():
        r_name = str(row['region']).lower().strip()
        r_id = region_map.get(r_name)
        
        if not r_id:
             # Try partial match or skip
             # For demo, if region empty, assign to 'Grand Casablanca' (often ID 1 or 2)
             # Let's just pick first region if unknown, or skip
             if region_map:
                 r_id = list(region_map.values())[0]
             else:
                 continue

        # Calculation
        # Total failures expected = roughly total_risk_score
        # Tech hours = total_risk_score * 4 hours
        # Techs needed = Tech hours / 8 hours
        techs_needed = max(1, int((row['total_risk_score'] * 4) / 8))
        
        # Availability is inverse of load? Let's simplify: 
        # higher need -> lower availability rate
        availability = max(0.4, 1.0 - (techs_needed / 20.0)) # Dummy normalization
        
        forecasts_hr.append((r_id, 1, techs_needed, availability))
        
    # Insert HR
    if forecasts_hr:
        cur.executemany("INSERT INTO FACT_HR_FORECAST (region_id, time_id, required_technicians, availability_rate) VALUES (?, ?, ?, ?)", forecasts_hr)
    else:
        # Fallback if no predictions: Seed 1 entry
        print("  ⚠️ No strong predictions found for HR. Seeding default.")
        if region_map:
             rid = list(region_map.values())[0]
             cur.execute("INSERT INTO FACT_HR_FORECAST (region_id, time_id, required_technicians, availability_rate) VALUES (?, 1, 5, 0.9)", (rid,))

    # --- B. INVENTORY FORECAST (Parts Needed) ---
    print("  -> Calculating Stock Prediction...")
    # Find defective parts predicted
    # We need to link 'defective_part' name string to DIM_PART.part_id
    
    sql_inv = """
        SELECT defective_part, COUNT(*) as needed_count, AVG(failure_probability) as avg_prob
        FROM FACT_PREDICTION
        WHERE failure_probability > 0.4 AND defective_part IS NOT NULL AND defective_part != ''
        GROUP BY defective_part
    """
    df_inv = pd.read_sql_query(sql_inv, conn)
    
    cur.execute("SELECT part_name, part_id FROM DIM_PART")
    part_map = {row[0].lower().strip(): row[1] for row in cur.fetchall()}
    
    forecasts_inv = []
    
    for _, row in df_inv.iterrows():
        p_name = str(row['defective_part']).lower().strip()
        
        # Split commas if multiple parts
        sub_parts = [p.strip() for p in p_name.replace(',', ';').split(';')]
        
        for sp in sub_parts:
            # Fuzzy match or direct
            pid = part_map.get(sp)
            if not pid:
                # Try finding substring
                for db_p, db_id in part_map.items():
                    if sp in db_p or db_p in sp:
                        pid = db_id
                        break
            
            if pid:
                # Prediction Logic
                # Shortage = Needed count
                # Probability = avg_prob
                shortage = row['needed_count']
                prob = row['avg_prob']
                forecasts_inv.append((pid, 1, shortage, prob))

    if forecasts_inv:
        cur.executemany("INSERT INTO FACT_INVENTORY_FORECAST (part_id, time_id, predicted_shortage, reorder_probability) VALUES (?, ?, ?, ?)", forecasts_inv)
    else:
         print("  ⚠️ No specific parts predicted. Seeding default.")
         if part_map:
             pid = list(part_map.values())[0]
             cur.execute("INSERT INTO FACT_INVENTORY_FORECAST (part_id, time_id, predicted_shortage, reorder_probability) VALUES (?, 1, 10, 0.8)", (pid,))
             
    conn.commit()
    conn.close()
    print("✅ Smart Forecasts Generated & Stored.")

if __name__ == "__main__":
    generate_smart_forecasts()
