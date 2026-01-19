from sqlalchemy import create_engine, text
import pandas as pd

SQLALCHEMY_DATABASE_URL = "sqlite:///./Companyx_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    print("--- DIM_DEALER COUNT ---")
    result = conn.execute(text("SELECT COUNT(*) FROM DIM_DEALER"))
    print(result.scalar())

    print("\n--- SAMPLE DEALERS ---")
    df = pd.read_sql("SELECT * FROM DIM_DEALER LIMIT 10", conn)
    print(df.to_string())

    print("\n--- SUM TECHNICIANS BY REGION ---")
    df_sum = pd.read_sql("SELECT region_id, SUM(technician_count) as total FROM DIM_DEALER GROUP BY region_id", conn)
    print(df_sum.to_string())
