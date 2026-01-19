import threading
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from api.structure_db import SessionLocal, FactPrediction, FactNotification, DimVehicle

class AlertScheduler:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()
        print(">> AlertScheduler démarré en tâche de fond.")

    def loop(self):
        while self.running:
            try:
                self.check_for_alerts()
            except Exception as e:
                print(f"Error in AlertScheduler: {e}")
            
            # Sleep for 60 seconds
            time.sleep(60)

    def check_for_alerts(self):
        db = SessionLocal()
        try:
            # 0. Check if table is empty
            if db.query(FactPrediction).count() == 0:
                print(">> [AlertScheduler] Aucune prédiction en base. En attente de données...")
                return

            # Check predictions from last 24h
            threshold_time = datetime.utcnow() - timedelta(hours=24)
            
            critical_preds = db.query(FactPrediction).filter(
                FactPrediction.failure_probability > 0.8,
                FactPrediction.prediction_date >= threshold_time
            ).all()

            for pred in critical_preds:
                # Get Vehicle Info
                vehicle = db.query(DimVehicle).filter(DimVehicle.vehicle_id == pred.vehicle_id).first()
                if not vehicle: continue
                
                vid_str = vehicle.original_vehicle_id
                
                # Deduplication: Check if we already alerted for this vehicle recently
                exists = db.query(FactNotification).filter(
                    FactNotification.vehicle_id == vid_str,
                    FactNotification.level == 'Critical',
                    FactNotification.created_at >= threshold_time
                ).first()
                
                if not exists:
                    # Generate Alert
                    title = f"Panne Imminente : {pred.predicted_failure_type}"
                    msg = f"Véhicule {vid_str} ({pred.engine_model}) : Risque critique ({int(pred.failure_probability*100)}%). Panne estimée dans {pred.predicted_days_before_failure} jours."
                    
                    new_notif = FactNotification(
                        title=title,
                        message=msg,
                        level='Critical',
                        vehicle_id=vid_str,
                        created_at=datetime.utcnow(),
                        is_read=False
                    )
                    db.add(new_notif)
                    print(f">> [AlertScheduler] Alerte générée pour {vid_str}")
            
            db.commit()
        finally:
            db.close()
