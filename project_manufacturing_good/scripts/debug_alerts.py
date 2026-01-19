import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.structure_db import SessionLocal, FactPrediction, FactNotification

def debug_alerts():
    db = SessionLocal()
    try:
        print("🔍 Diagnostic des Alertes IA (Debug)...")
        
        # 1. Check Total Predictions
        total_preds = db.query(FactPrediction).count()
        print(f"📊 Total Prédictions en base : {total_preds}")
        
        if total_preds == 0:
            print("❌ Aucune prédiction trouvée ! Importez d'abord un fichier CSV.")
            return

        # 2. Check Recent Predictions (24h)
        threshold_time = datetime.utcnow() - timedelta(hours=24)
        recent_preds = db.query(FactPrediction).filter(FactPrediction.prediction_date >= threshold_time).all()
        print(f"🕒 Prédictions récentes (< 24h) : {len(recent_preds)}")
        
        # 3. Check High Risk Preds (> 0.5 for debug)
        risky_preds = db.query(FactPrediction).filter(
            FactPrediction.failure_probability > 0.5,
            FactPrediction.prediction_date >= threshold_time
        ).all()
        print(f"⚠️ Prédictions à risque (> 50%) : {len(risky_preds)}")
        
        for p in risky_preds:
            print(f"   - ID: {p.vehicle_id} | Prob: {p.failure_probability:.2f} | Type: {p.predicted_failure_type}")

        # 4. Check Existing Notifications
        notifs = db.query(FactNotification).all()
        print(f"🔔 Notifications existantes : {len(notifs)}")
        for n in notifs:
            print(f"   - [{n.level}] {n.title} (Vehicule: {n.vehicle_id})")

    finally:
        db.close()

if __name__ == "__main__":
    debug_alerts()
