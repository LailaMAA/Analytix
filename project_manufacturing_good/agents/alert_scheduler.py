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
            
            # Sleep for 30 seconds
            time.sleep(30)

    def check_for_alerts(self):
        db = SessionLocal()
        try:
            # 0. Check if table is empty
            if db.query(FactPrediction).count() == 0:
                return

            # Check predictions from last hour
            threshold_time = datetime.utcnow() - timedelta(hours=1)
            
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
                    # Use a standard print for system log but avoid spamming
                    print(f"[SYSTEM] AlertScheduler: Alerte generee pour {vid_str}")
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[ERROR] AlertScheduler: {e}")
        finally:
            db.close()
