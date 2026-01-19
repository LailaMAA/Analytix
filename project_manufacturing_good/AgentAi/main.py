import pandas as pd
import random
from datetime import datetime, timedelta
from ai_agent import MaintenanceAgent
from database import DatabaseManager
from dotenv import load_dotenv
load_dotenv()

def generate_dummy_data(rows=50):
    """
    Generates dummy data simulating the FACT_PREDICTION table.
    Used as fallback if database connection is not configured.
    """
    print("[SIMULATION] 🎲 generating dummy data...")
    engine_models = ['V6 Turbo', 'V8 Hybrid', 'Electric Motor', 'Inline-4 Diesel']
    parts = ['Fuel Pump', 'Water Pump', 'Alternator', 'Brake Pad', 'Timing Belt', 'Battery', 'Turbocharger']
    failure_types = ['Component Degradation', 'Overheating', 'Electrical Short', 'Wear and Tear', 'Sensor Failure']
    regions = ['North', 'South', 'East', 'West']
    cities = {
        'North': ['Chicago', 'Detroit', 'Toronto'],
        'South': ['Houston', 'Miami', 'Atlanta'],
        'East': ['New York', 'Boston', 'Philadelphia'],
        'West': ['Los Angeles', 'Seattle', 'San Francisco']
    }

    data = []
    for i in range(rows):
        region = random.choice(regions)
        city = random.choice(cities[region])
        days_before_failure = random.randint(1, 90)
        
        # Introduce some patterns
        failure_type = random.choice(failure_types)
        if region == 'South' and random.random() > 0.7:
             failure_type = 'Overheating'

        record = {
            'vehicle_id': f'VEH-{1000+i}',
            'engine_model': random.choice(engine_models),
            'vehicle_age': random.randint(1, 10),
            'total_mileage': random.randint(10000, 150000),
            'engine_rpm': random.randint(2000, 6000),
            'engine_load': random.uniform(20, 90),
            'engine_temperature': random.uniform(80, 110),
            'oil_temperature': random.uniform(70, 100),
            'oil_pressure': random.uniform(30, 60),
            'fuel_pressure': random.uniform(40, 70),
            'last_maintenance_date': (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d'),
            'days_before_failure': days_before_failure,
            'warranty': random.choice([True, False]),
            'defective_part': random.choice(parts),
            'service_start_date': (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime('%Y-%m-%d'),
            'failure_type': failure_type,
            'impacted_part': random.choice(parts),
            'region': region,
            'city': city
        }
        data.append(record)
    
    return pd.DataFrame(data)

def main():
    print("--- Starting AI Maintenance Autonomous Analyst ---")
    
    # 1. Database Connection & Data Loading
    db_manager = DatabaseManager()
    df = db_manager.fetch_predictions()
    
    if df is None or df.empty:
        # Fallback to simulation
        df = generate_dummy_data(200)
    
    print(f"[DATA] Processing {df.shape[0]} records.")
    
    # 2. Initialize Agent
    agent = MaintenanceAgent(df)
    
    # 3. Analyze and Report
    print("\n--- Generating Analyst Details ---")
    report = agent.generate_daily_briefing()
    
    # 4. Output Results
    print(report)

    # Optional: Save report
    with open("daily_briefing.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n[Info] Briefing saved to 'daily_briefing.md'")
    
    # 5. Dispatch Alert
    agent.dispatch_alert(report)

if __name__ == "__main__":
    main()
