import pandas as pd
import joblib
import numpy as np

class InferencePipeline:

    def __init__(self):
        # Chargement des modèles
        self.model_type = joblib.load("models/failure_type_model.joblib")
        self.model_days = joblib.load("models/days_before_failure_model.joblib")
        # Chargement des objets de prétraitement
        self.scaler = joblib.load("models/scaler.pkl")
        self.label_encoders = joblib.load("models/label_encoders.pkl")
        self.features = joblib.load("models/features.joblib")

    def preprocess(self, df):
        df_proc = df.copy()
        
        # Standardize Input Names (Map CSV French/Common names to English Standards)
        rename_map = {
             "kilometrage_total": "total_mileage",
             "age_vehicule": "vehicle_age",
             "Model_moteur": "engine_model",
             "Garantie": "warranty",
             "ville": "city",
             "Piece_defectuee": "defective_part",
             "piece_impacte": "impacted_part"
        }
        df_proc = df_proc.rename(columns=rename_map)
        
        # Encodage des colonnes catégorielles
        for col, le in self.label_encoders.items():
            if col in df_proc.columns:
                df_proc[col] = le.transform(df_proc[col].astype(str))
        
        # Gestion de la colonne warranty
        if "warranty" in df_proc.columns:
            df_proc["warranty"] = df_proc["warranty"].map({
                "Oui": 1, "Non": 0, "1": 1, "0": 0, 1: 1, 0: 0
            }).fillna(0)

        # Normalisation des colonnes numériques
        numerical_cols = [
            "total_mileage", "engine_rpm", "engine_temperature",
            "oil_temperature", "oil_pressure", "fuel_pressure",
            "vehicle_age", "engine_load"
        ]
        cols_to_scale = [c for c in numerical_cols if c in df_proc.columns]
        if cols_to_scale:
            df_proc[cols_to_scale] = self.scaler.transform(df_proc[cols_to_scale])

        return df_proc

    def predict(self, df_input):
        # Prétraitement
        df_processed = self.preprocess(df_input)
        
        # Sélection des features
        X = df_processed[self.features]

        # Enforce column order for Classification Model
        if hasattr(self.model_type, "feature_names_in_"):
            X_type = X[self.model_type.feature_names_in_]
        else:
            X_type = X

        # Classification (Type de panne)
        type_pred_indices = self.model_type.predict(X_type)
        type_proba = self.model_type.predict_proba(X_type).max(axis=1)
        
        # Décodage du type de panne
        le_type = self.label_encoders["failure_type"]
        type_pred_labels = le_type.inverse_transform(type_pred_indices)

        # Régression (Jours avant panne)
        X_reg = X.copy()
        X_reg['failure_type'] = type_pred_indices
        if hasattr(self.model_days, "feature_names_in_"):
            X_reg = X_reg[self.model_days.feature_names_in_]
        jours_pred = self.model_days.predict(X_reg)
        
        # Préparation du DataFrame final pour sauvegarde et retour
        # On repart de df_input pour avoir les valeurs NON-SCALÉES (originales)
        df_result = df_input.copy()
        
        # On applique le même renommage que dans preprocess pour la cohérence DB
        rename_map = {
             "kilometrage_total": "total_mileage",
             "age_vehicule": "vehicle_age",
             "Model_moteur": "engine_model",
             "Garantie": "warranty",
             "ville": "city",
             "Piece_defectuee": "defective_part",
             "piece_impacte": "impacted_part"
        }
        df_result = df_result.rename(columns=rename_map)

        # Ajout des résultats de prédiction
        df_result["predicted_failure_type"] = type_pred_labels
        df_result["failure_probability"] = type_proba
        df_result["predicted_days_before_failure"] = jours_pred.round(0).clip(min=0).astype(int)

        # MAPPING: Infer impacted and defective parts based on failure type
        # ----------------------------------------------------------------
        FAILURE_MAPPING = {
            "surchauffe moteur": {
                "impacted_part": "Bloc-cylindres, Culasse, Pistons",
                "defective_part": "Joint de culasse, Culasse, Thermostat"
            },
            "defaut de lubrification": {
                "impacted_part": "Vilebrequin, Bielles, Pistons",
                "defective_part": "Pompe à huile, Filtre à huile, Joints"
            },
            "defaut d injection": {
                "impacted_part": "Pistons, Soupapes, Culasse",
                "defective_part": "Injecteurs, Pompe carburant, Capteurs pression"
            },
            "defaut de refroidissement": {
                "impacted_part": "Bloc-cylindres, Culasse",
                "defective_part": "Pompe à eau, Radiateur, Ventilateur"
            },
            "defaut electrique": {
                "impacted_part": "Démarreur, Capteurs, Alternateur",
                "defective_part": "Batterie, Alternateur, Capteurs, Faisceau"
            },
            "usure mecanique": {
                "impacted_part": "Pistons, Segments, Soupapes, Bielles",
                "defective_part": "Segments, Soupapes, Courroie, Arbre à cames"
            }
        }

        # Accent-insensitive normalization
        def normalize_ft(text):
            import unicodedata
            if not text: return ""
            # Lowercase + replace apostrophes with space (as seen in model output)
            t = str(text).lower().replace("'", " ").replace("’", " ").strip()
            # Remove accents
            t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
            return t

        # Apply mapping
        def get_impacted(ft):
            ft_norm = normalize_ft(ft)
            return FAILURE_MAPPING.get(ft_norm, {}).get("impacted_part", "Inconnu")
        
        def get_defective(ft):
            ft_norm = normalize_ft(ft)
            return FAILURE_MAPPING.get(ft_norm, {}).get("defective_part", "Inconnu")

        df_result["impacted_part"] = df_result["predicted_failure_type"].apply(get_impacted)
        df_result["defective_part"] = df_result["predicted_failure_type"].apply(get_defective)


        # Logique métier : Si "Aucune panne", alors jours_avant_panne = 0
        mask_no_failure = df_result["predicted_failure_type"].str.strip() == "Aucune panne"
        df_result.loc[mask_no_failure, "predicted_days_before_failure"] = 0

        # Sauvegarde dans la base
        self.save_predictions(df_result)
        
        return df_result[[
            "vehicle_id",
            "predicted_failure_type",
            "failure_probability",
            "predicted_days_before_failure",
            "impacted_part",
            "defective_part"
        ]]

    def save_predictions(self, df_full):
        from api.structure_db import SessionLocal, FactPrediction, DimVehicle, FactVehicleFailure, DimFailureType
        from sqlalchemy import func
        
        session = SessionLocal()
        try:
            for _, row in df_full.iterrows():
                vid_str = str(row['vehicle_id'])
                
                # Normalisation de la garantie pour la cohérence
                raw_warranty = str(row.get('warranty', 'Non'))
                final_warranty = "Oui" if any(x in raw_warranty.lower() for x in ["oui", "yes", "1", "true", "sous garantie"]) else "Non"

                veh = session.query(DimVehicle).filter_by(original_vehicle_id=vid_str).first()
                if not veh:
                    # Auto-create vehicle
                    veh = DimVehicle(
                        original_vehicle_id=vid_str,
                        engine_model=str(row.get('engine_model', 'Unknown')),
                        vehicle_age=float(row.get('vehicle_age', 0)),
                        under_warranty=final_warranty
                    )
                    session.add(veh)
                    session.flush() # Get ID
                else:
                    # UPDATE MUST ALWAYS HAPPEN to sync Warranty KPI
                    veh.under_warranty = final_warranty
                    veh.vehicle_age = float(row.get('vehicle_age', veh.vehicle_age))
                    veh.engine_model = str(row.get('engine_model', veh.engine_model))
                
                # Intelligent Part Recommendation ... [skipped logic]
                pred_failure = row['predicted_failure_type']
                rec_part_id = None
                
                if pred_failure != "Aucune panne":
                    common = session.query(FactVehicleFailure.part_id)\
                        .join(DimFailureType, FactVehicleFailure.failure_type_id == DimFailureType.failure_type_id)\
                        .filter(DimFailureType.failure_name == pred_failure)\
                        .group_by(FactVehicleFailure.part_id)\
                        .order_by(func.count(FactVehicleFailure.part_id).desc())\
                        .first()
                    if common: rec_part_id = common[0]

                pred = FactPrediction(
                    vehicle_id=veh.vehicle_id,
                    
                    # Snapshot Inputs
                    engine_model=str(row.get('engine_model', 'Unknown')),
                    vehicle_age=float(row.get('vehicle_age', 0)),
                    total_mileage=float(row.get('total_mileage', 0)),
                    warranty=final_warranty,
                    last_maintenance_date=str(row.get('last_maintenance_date', '')),
                    service_start_date=str(row.get('service_start_date', '')),
                    
                    engine_rpm=float(row.get('engine_rpm', 0)),
                    engine_load=float(row.get('engine_load', 0)),
                    engine_temperature=float(row.get('engine_temperature', 0)),
                    oil_temperature=float(row.get('oil_temperature', 0)),
                    oil_pressure=float(row.get('oil_pressure', 0)),
                    fuel_pressure=float(row.get('fuel_pressure', 0)),
                    
                    region=str(row.get('region', '')),
                    city=str(row.get('city', '')),
                    defective_part=str(row.get('defective_part', '')),
                    impacted_part=str(row.get('impacted_part', '')),
                    
                    # Outputs
                    predicted_failure_type=pred_failure,
                    failure_probability=float(row['failure_probability']),
                    predicted_days_before_failure=int(row['predicted_days_before_failure']),
                    
                    # Recommendation
                    recommended_part_id=rec_part_id
                )
                session.add(pred)
            session.commit()
            print(f" Saved {len(df_full)} predictions to FACT_PREDICTION.")
        except Exception as e:
            print(f" Failed to save predictions: {e}")
        finally:
            session.close()
