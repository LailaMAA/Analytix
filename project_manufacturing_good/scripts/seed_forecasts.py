import sqlite3
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "Companyx_database.db"

def seed_forecasts():
    print("🌱 Seeding Forecast Data...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Seed HR Forecast
    # Get Regions
    cursor.execute("SELECT region_id FROM DIM_REGION")
    regions = [r[0] for r in cursor.fetchall()]
    
    print(f"Found {len(regions)} regions. Seeding HR Forecasts...")
    
    for r_id in regions:
        # Simulate data
        req = random.randint(5, 15)
        avail = random.uniform(0.7, 0.95)
        # Check if exists
        cursor.execute("SELECT count(*) FROM FACT_HR_FORECAST WHERE region_id=?", (r_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO FACT_HR_FORECAST (region_id, time_id, required_technicians, availability_rate)
                VALUES (?, 1, ?, ?)
            """, (r_id, req, avail))

    # 2. Seed Inventory Forecast
    # Get Parts
    cursor.execute("SELECT part_id FROM DIM_PART")
    parts = [p[0] for p in cursor.fetchall()]
    
    print(f"Found {len(parts)} parts. Seeding Inventory Forecasts...")
    
    for p_id in parts:
        shortage = random.randint(10, 50)
        prob = random.uniform(0.1, 0.9)
        
        cursor.execute("SELECT count(*) FROM FACT_INVENTORY_FORECAST WHERE part_id=?", (p_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO FACT_INVENTORY_FORECAST (part_id, time_id, predicted_shortage, reorder_probability)
                VALUES (?, 1, ?, ?)
            """, (p_id, shortage, prob))

    conn.commit()
    conn.close()
    print("✅ Le seeding des prévisions est terminé.")

if __name__ == "__main__":
    seed_forecasts()
