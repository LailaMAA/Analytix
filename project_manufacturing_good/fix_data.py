from sqlalchemy import create_engine, text
import random

SQLALCHEMY_DATABASE_URL = "sqlite:///./Companyx_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    # 1. Reset all to 0
    print("Resetting all technician counts to 0...")
    conn.execute(text("UPDATE DIM_DEALER SET technician_count = 0"))
    
    # 2. Get list of dealer IDs
    result = conn.execute(text("SELECT dealer_id FROM DIM_DEALER"))
    all_fs = [row[0] for row in result]
    print(f"Total Dealers: {len(all_fs)}")
    
    # 3. Pick 50 random dealers to have staff
    active_dealers = random.sample(all_fs, min(50, len(all_fs)))
    
    # 4. Update them
    print("Assigning staff to 50 locations...")
    # SQLite doesn't support list parameters in execute nicely with pure text, loop is safer for small batch
    for did in active_dealers:
        conn.execute(text("UPDATE DIM_DEALER SET technician_count = :cnt WHERE dealer_id = :did"), 
                     {"cnt": random.randint(2, 5), "did": did})
        
    conn.commit()
    print("✅ Data Fixed.")
