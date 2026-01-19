from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        """
        Initializes the database connection.
        Reads DB_CONNECTION_STRING from environment variables.
        """
        load_dotenv()
        self.connection_string = os.getenv('DB_CONNECTION_STRING')
        self.engine = None
        
        if self.connection_string:
            try:
                self.engine = create_engine(self.connection_string)
                print("[DATABASE] 🔌 Connection successful.")
            except Exception as e:
                print(f"[DATABASE] ❌ Connection failed: {e}")
        else:
            print("[DATABASE] ⚠️ No DB_CONNECTION_STRING found in .env. Using simulation mode.")

    def fetch_predictions(self):
        """
        Fetches all records from the FACT_PREDICTION table.
        Returns a Pandas DataFrame.
        """
        if not self.engine:
            return None
        
        try:
            print("[DATABASE] ⏳ Fetching data from FACT_PREDICTION...")
            query = "SELECT * FROM FACT_PREDICTION"
            df = pd.read_sql(query, self.engine)
            print(f"[DATABASE] ✅ Loaded {len(df)} records.")
            return df
        except Exception as e:
            print(f"[DATABASE] ❌ Query failed: {e}")
            return None
