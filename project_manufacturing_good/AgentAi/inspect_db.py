import sqlalchemy
from sqlalchemy import create_engine, inspect
import os

# Use absolute path to avoid relative path confusion with special characters
db_path = os.path.abspath("Companyx_database.db")
print(f"Checking database at: {db_path}")

# SQLite URI
connection_str = f"sqlite:///{db_path}"
engine = create_engine(connection_str)

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Connection successful. Found {len(tables)} tables:")
    for table in tables:
        print(f" - {table}")
        
    if 'FACT_PREDICTION' in tables:
        print("\nTable FACT_PREDICTION found!")
    else:
        print("\nTable FACT_PREDICTION NOT found.")

except Exception as e:
    print(f"Error connecting: {e}")
