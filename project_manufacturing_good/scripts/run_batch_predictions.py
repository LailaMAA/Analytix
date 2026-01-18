import sys
import os
import pandas as pd

# Fix Import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from inference.prediction_service import InferencePipeline
from api.structure_db import SessionLocal, FactPrediction

def run_predictions():
    print("Starting Batch Prediction Generation...")
    
    # 1. Load Data
    csv_path = "data/raw/data_test_real.csv"
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print(f"Reading input data from {csv_path}...")
    try:
        df_input = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 2. Init Pipeline
    try:
        print("Initializing Inference Pipeline...")
        pipeline = InferencePipeline()
    except Exception as e:
        print(f"Error loading models: {e}")
        return

    # 3. Clear existing predictions? (Optional, maybe user wants to append? Let's clear for clean demo)
    session = SessionLocal()
    try:
        print("Clearing old predictions from FACT_PREDICTION...")
        session.query(FactPrediction).delete()
        session.commit()
    except Exception as e:
        print(f"Error clearing table: {e}")
    finally:
        session.close()

    # 4. Generate Predictions
    print(f"Generating predictions for {len(df_input)} vehicles...")
    try:
        # prediction_service.predict already saves to DB!
        
        result = pipeline.predict(df_input)
        
        print("\nBatch Prediction Complete!")
        print(result.head())
        
    except Exception as e:
        print(f"Prediction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_predictions()
