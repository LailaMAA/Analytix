import sys
import os
import pandas as pd
from sqlalchemy.orm import Session

# Fix Import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.structure_db import (
    SessionLocal, init_enterprise_db, engine,
    FactTrainingData, FactPrediction, FactVehicleFailure,
    FactHRForecast, FactInventoryForecast, FactInvestmentForecast, FactWarrantyImpact,
    DimVehicle, DimRegion, DimPart, DimFailureType, DimDate
)

import traceback

def populate_dataset():
    print("START: Full Enterprise Data Migration (20k-35k per table)")
    init_enterprise_db()
    session = SessionLocal()

    try:
        # 1. DIM_REGION
        print("SEEDING: DIM_REGION")
        path_reg = "data/raw/DIM_REGION_35000.csv"
        if os.path.exists(path_reg):
            df = pd.read_csv(path_reg).fillna('Unknown')
            objects = []
            for _, row in df.iterrows():
                try:
                    objects.append(DimRegion(
                        region_id=int(float(row['region_id'])), 
                        region_name=str(row['region_name']), 
                        climate=str(row.get('climate', 'Moderate'))
                    ))
                except: continue
            session.bulk_save_objects(objects)
            session.commit()
            print(f"DONE: DIM_REGION ({session.query(DimRegion).count()} rows)")
        
        # 2. DIM_PART
        print("SEEDING: DIM_PART")
        path_part = "data/raw/DIM_PART_35000.csv"
        if os.path.exists(path_part):
            df = pd.read_csv(path_part).fillna('Unknown')
            objects = []
            for _, row in df.iterrows():
                try:
                    objects.append(DimPart(
                        part_id=int(float(row['part_id'])), 
                        part_name=str(row['part_name']), 
                        category=str(row.get('category', 'Mechanical')), 
                        unit_cost=float(row.get('unit_cost', 0)),
                        criticality_level=str(row.get('criticality_level', 'Medium'))
                    ))
                except: continue
            session.bulk_save_objects(objects)
            session.commit()
            print(f"DONE: DIM_PART ({session.query(DimPart).count()} rows)")

        # 3. DIM_VEHICLE
        print("SEEDING: DIM_VEHICLE")
        path_veh = "data/raw/DIM_VEHICLE_35000.csv"
        if os.path.exists(path_veh):
            df = pd.read_csv(path_veh).fillna('Unknown')
            objects = []
            for _, row in df.iterrows():
                try:
                    vid = int(float(row['vehicle_id']))
                    objects.append(DimVehicle(
                        vehicle_id=vid,
                        original_vehicle_id=str(vid),
                        engine_model=str(row.get('engine_model', 'Inconnu')),
                        vehicle_type=str(row.get('vehicle_type', 'Léger')),
                        vehicle_age=float(row.get('vehicle_age', 5.0)),
                        under_warranty=str(row.get('under_warranty', 'Non')),
                        service_start_date=str(row.get('service_start_date', '2020-01-01'))
                    ))
                    if len(objects) >= 5000:
                        session.bulk_save_objects(objects)
                        objects = []
                except: continue
            if objects:
                session.bulk_save_objects(objects)
            session.commit()
            print(f"DONE: DIM_VEHICLE ({session.query(DimVehicle).count()} rows)")

        # 4. DIM_TIME (DIM_DATE)
        print("SEEDING: DIM_DATE")
        path_time = "data/raw/DIM_TIME_35000.csv"
        if os.path.exists(path_time):
            df = pd.read_csv(path_time).fillna(0)
            objects = []
            for _, row in df.iterrows():
                try:
                    objects.append(DimDate(
                        date_id=int(float(row['time_id'])),
                        date_iso=str(row.get('date', row.get('date_id', '2024-01-01'))),
                        year=int(float(row.get('year', 2024))),
                        month=int(float(row.get('month', 1))),
                        day=int(float(row.get('day', 1)))
                    ))
                    if len(objects) >= 5000:
                        session.bulk_save_objects(objects)
                        objects = []
                except: continue
            if objects:
                session.bulk_save_objects(objects)
            session.commit()
            print(f"DONE: DIM_DATE ({session.query(DimDate).count()} rows)")

        # 5. FACT_VEHICLE_FAILURE (Maroc Context)
        print("SEEDING: FACT_VEHICLE_FAILURE (Maroc)")
        path_fail = "data/raw/Pannes_moteurs_equilibre_Maroc.csv"
        if os.path.exists(path_fail):
            df = pd.read_csv(path_fail).fillna(0)
            failure_types = {}
            objects = []
            for idx, row in df.iterrows():
                try:
                    ft_name = str(row['type_panne_moteur'])
                    if ft_name not in failure_types:
                        ft = session.query(DimFailureType).filter_by(failure_name=ft_name).first()
                        if not ft:
                            ft = DimFailureType(failure_name=ft_name)
                            session.add(ft)
                            session.flush()
                        failure_types[ft_name] = ft.failure_type_id
                    
                    objects.append(FactVehicleFailure(
                        vehicle_id=int(float(row.get('vehicle_id', idx+1))),
                        region_id=int(float(row.get('region_id', (idx % 35000) + 1))),
                        failure_type_id=failure_types[ft_name],
                        part_id=int(float(row.get('part_id', (idx % 35000) + 1))),
                        time_id=int(float(row.get('time_id', (idx % 35000) + 1))),
                        total_mileage=float(row['kilometrage_total']),
                        engine_rpm=float(row['engine_rpm']),
                        engine_temperature=float(row['engine_temperature']),
                        oil_pressure=float(row['oil_pressure']),
                        days_before_failure=int(float(row['jours_avant_panne'])),
                        last_maintenance_date=str(row['date_derniere_maintenance'])
                    ))
                    if len(objects) >= 5000:
                        session.bulk_save_objects(objects)
                        objects = []
                except Exception as e:
                    if idx < 5: print(f"Row {idx} skip: {e}")
                    continue
            if objects:
                session.bulk_save_objects(objects)
            session.commit()
            print(f"DONE: FACT_VEHICLE_FAILURE ({session.query(FactVehicleFailure).count()} rows)")

        # 6. BUSINESS FORECASTS
        print("SEEDING: FORECAST TABLES")
        tables = [
            ("data/raw/FACT_HR_FORECAST_35000.csv", FactHRForecast),
            ("data/raw/FACT_INVENTORY_FORECAST_35000.csv", FactInventoryForecast),
            ("data/raw/FACT_INVESTMENT_FORECAST_35000.csv", FactInvestmentForecast),
            ("data/raw/FACT_WARRANTY_IMPACT_35000.csv", FactWarrantyImpact),
        ]

        model_cols = {
            FactHRForecast: ['hr_event_id', 'region_id', 'time_id', 'required_technicians', 'availability_rate'],
            FactInventoryForecast: ['inventory_event_id', 'part_id', 'time_id', 'predicted_shortage', 'reorder_probability'],
            FactInvestmentForecast: ['investment_event_id', 'region_id', 'time_id', 'estimated_cost', 'roi_prediction'],
            FactWarrantyImpact: ['warranty_event_id', 'vehicle_id', 'time_id', 'warranty_impact_score', 'failure_confirmed']
        }

        for path, model in tables:
            if os.path.exists(path):
                df = pd.read_csv(path).fillna(0)
                df = df.head(30000)
                objects = []
                valid_keys = model_cols[model]
                for idx, row in df.iterrows():
                    try:
                        data = {k: row[k] for k in valid_keys if k in row}
                        for k, v in data.items():
                            if 'rate' in k or 'probability' in k or 'score' in k or 'cost' in k or 'prediction' in k:
                                data[k] = float(v)
                            else:
                                data[k] = int(float(v))
                        objects.append(model(**data))
                    except: continue
                session.bulk_save_objects(objects)
                session.commit()
                print(f"DONE: {model.__tablename__} ({session.query(model).count()} rows)")

        # 7. FACT_TRAINING_DATA
        print("SEEDING: FACT_TRAINING_DATA")
        if os.path.exists(path_fail):
            df = pd.read_csv(path_fail).fillna(0)
            objects = []
            for _, row in df.iterrows():
                objects.append(FactTrainingData(
                    vehicle_id=str(row['vehicle_id']),
                    engine_model=str(row['Model_moteur']),
                    vehicle_age=float(row['age_vehicule']),
                    total_mileage=float(row['kilometrage_total']),
                    engine_rpm=float(row['engine_rpm']),
                    engine_load=float(row.get('engine_load', 0)),
                    engine_temperature=float(row['engine_temperature']),
                    oil_temperature=float(row.get('oil_temperature', 0)),
                    oil_pressure=float(row['oil_pressure']),
                    fuel_pressure=float(row.get('fuel_pressure', 0)),
                    last_maintenance_date=str(row['date_derniere_maintenance']),
                    warranty=str(row['Garantie']),
                    service_start_date=str(row.get('Date_mise_service', '')),
                    region=str(row['region']),
                    city=str(row.get('ville', '')),
                    failure_type=str(row['type_panne_moteur']),
                    days_before_failure=int(float(row['jours_avant_panne'])),
                    defective_part=str(row['Piece_defectuee']),
                    impacted_part=str(row.get('piece_impacte', ''))
                ))
                if len(objects) >= 5000:
                    session.bulk_save_objects(objects)
                    objects = []
            if objects:
                session.bulk_save_objects(objects)
            session.commit()
            print(f"DONE: FACT_TRAINING_DATA ({session.query(FactTrainingData).count()} rows)")

        print("SUCCESS: High-Volume English Migration Complete!")
    
    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    populate_dataset()

if __name__ == "__main__":
    populate_dataset()

if __name__ == "__main__":
    populate_dataset()

if __name__ == "__main__":
    populate_dataset()

if __name__ == "__main__":
    populate_dataset()
