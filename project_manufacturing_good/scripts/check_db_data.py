import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Adjust path to DB if needed, assuming valid CWD
DB_PATH = "Companyx_database.db"

def check_counts():
    if not os.path.exists(DB_PATH):
        print(f"❌ DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ["FACT_HR_FORECAST", "FACT_INVENTORY_FORECAST", "DIM_REGION", "DIM_PART"]
    
    print("--- Table Counts ---")
    for t in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            print(f"{t}: {count}")
        except Exception as e:
            print(f"{t}: Error {e}")
            
    conn.close()

if __name__ == "__main__":
    check_counts()
