import pandas as pd
import os
import joblib
import datetime
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.model_selection import train_test_split
import shutil

def retrain_pipeline(data_path="data/raw/data_test_real.csv", version_name=None):
    if not version_name:
        version_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"--- Démarrage du réentraînement (version: {version_name}) ---")
    
    # 1. Chargement des données
    if not os.path.exists(data_path):
        print(f"Erreur: Fichier {data_path} introuvable.")
        return
    
    df = pd.read_csv(data_path)
    print(f"[OK] Données chargées: {df.shape}")

    # 2. Prétraitement
    df.drop(columns=["date_derniere_maintenance", "Date_mise_service"], inplace=True, errors='ignore')
    df["Garantie"] = df["Garantie"].map({"Oui": 1, "Non": 0}).fillna(0)

    categorical_cols = ["Model_moteur", "type_panne_moteur", "Piece_defectuee", "piece_impacte", "region", "ville"]
    label_encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le

    numerical_cols = [
        "kilometrage_total", "engine_rpm", "engine_load", "engine_temperature",
        "oil_temperature", "oil_pressure", "fuel_pressure", "age_vehicule"
    ]
    scaler = MinMaxScaler()
    df[numerical_cols] = scaler.fit_transform(df[numerical_cols])

    # 3. Entraînement CLASSIFICATION (Type de panne)
    print("Entraînement du modèle de classification...")
    y_class = df["type_panne_moteur"]
    X = df.drop(columns=["type_panne_moteur", "jours_avant_panne", "vehicle_id", "Piece_defectuee", "piece_impacte", "ville", "region"], errors='ignore')
    
    # Save features list
    features = list(X.columns)

    X_train, X_test, y_train, y_test = train_test_split(X, y_class, test_size=0.2, stratify=y_class, random_state=42)
    model_type = LGBMClassifier(n_estimators=500, learning_rate=0.1, random_state=42, verbose=-1)
    model_type.fit(X_train, y_train)
    print("[OK] Classification terminée.")

    # 4. Entraînement RÉGRESSION (Jours avant panne)
    print("Entraînement du modèle de régression...")
    y_reg = df["jours_avant_panne"]
    X_reg = X.copy() # Même features pour simplifier

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)
    model_days = LGBMRegressor(n_estimators=500, learning_rate=0.05, random_state=42, verbose=-1)
    model_days.fit(X_train_r, y_train_r)
    print("[OK] Régression terminée.")

    # 5. Sauvegarde Versionnée
    version_dir = f"models/versions/{version_name}"
    os.makedirs(version_dir, exist_ok=True)
    
    joblib.dump(model_type, f"{version_dir}/type_panne_model.joblib")
    joblib.dump(model_days, f"{version_dir}/jours_avant_panne_model.joblib")
    joblib.dump(scaler, f"{version_dir}/scaler.pkl")
    joblib.dump(label_encoders, f"{version_dir}/label_encoders.pkl")
    joblib.dump(features, f"{version_dir}/features.joblib")

    # 6. Mise à jour des modèles "current" (copie dans models/)
    for f in ["type_panne_model.joblib", "jours_avant_panne_model.joblib", "scaler.pkl", "label_encoders.pkl", "features.joblib"]:
        shutil.copy(f"{version_dir}/{f}", f"models/{f}")

    print(f"\n--- Réentraînement terminé ! ---")
    print(f"Fichiers sauvegardés dans : {version_dir}")
    print(f"Modèles 'current' mis à jour dans : models/")

if __name__ == "__main__":
    retrain_pipeline()
