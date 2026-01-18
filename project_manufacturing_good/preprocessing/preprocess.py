import pandas as pd
import os
import sys
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from joblib import dump

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.structure_db import (
    SessionLocal, FactTrainingData, engine
)

def preprocess_data():
    # ==========================================
    # 1. Chargement des données (Depuis DB Centralisée)
    # ==========================================
    session = SessionLocal()
    try:
        print("🔌 Tentative de connexion à la Base de Données (FactTrainingData)...")
        # On lit directement la table "Flat" demandée par l'utilisateur
        query = session.query(FactTrainingData).statement
        df = pd.read_sql(query, session.bind)
        print(f"✅ Données chargées avec succès: {df.shape}")
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")
        return
    finally:
        session.close()

    if df.empty:
        print("⚠️ Aucune donnée trouvée dans FACT_TRAINING_DATA.")
        return

    # Drop Identifiers and non-feature columns
    cols_to_drop = ['training_id', 'vehicle_id', 'last_maintenance_date', 'service_start_date', 'city', 'region','defective_part','warranty','impacted_part']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore')

    
    categorical_cols = ['engine_model', 'failure_type']
    

    numerical_cols = [
        'total_mileage', 'engine_rpm', 'engine_temperature', 
        'oil_temperature', 'oil_pressure', 'fuel_pressure', 
        'vehicle_age', 'engine_load'
    ]
    

    label_encoders = {}
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
        
    
    scaler = MinMaxScaler()
    existing_num_cols = [c for c in numerical_cols if c in df.columns]
    if existing_num_cols:
        df[existing_num_cols] = scaler.fit_transform(df[existing_num_cols])
    

    output_path = os.path.join("data", "processed", "dataset_pretraite.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    
    target_cols = ['failure_type', 'days_before_failure']
    features = [c for c in df.columns if c not in target_cols]
    
    os.makedirs("models", exist_ok=True)
    dump(scaler, "models/scaler.pkl")
    dump(label_encoders, "models/label_encoders.pkl")
    dump(features, "models/features.joblib")
    dump(features, "models/feature_names.pkl") 
    
    print(f" Data processed and saved to {output_path}")
    print(f" {len(features)} Features saved to models/features.joblib")
    print(" Scaler and Encoders saved to models/")

if __name__ == "__main__":
    preprocess_data()