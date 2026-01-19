from sqlalchemy import create_engine, text
import pandas as pd

SQLALCHEMY_DATABASE_URL = "sqlite:///./Companyx_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

with engine.connect() as conn:
    print("--- CRITICAL VEHICLES (Risk > 70%) ---")
    query_crit = """
        SELECT v.original_vehicle_id, p.predicted_failure_type, p.failure_probability
        FROM FACT_PREDICTION p
        JOIN DIM_VEHICLE v ON p.vehicle_id = v.vehicle_id
        WHERE p.failure_probability > 0.7
        ORDER BY p.failure_probability DESC
        LIMIT 3
    """
    df_crit = pd.read_sql(query_crit, conn)
    print(df_crit.to_string())

    print("\n--- HEALTHY VEHICLES (Risk < 20%) ---")
    query_healthy = """
        SELECT v.original_vehicle_id, p.predicted_failure_type, p.failure_probability
        FROM FACT_PREDICTION p
        JOIN DIM_VEHICLE v ON p.vehicle_id = v.vehicle_id
        WHERE p.failure_probability < 0.2
        LIMIT 3
    """
    df_healthy = pd.read_sql(query_healthy, conn)
    print(df_healthy.to_string())
