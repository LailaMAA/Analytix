from sqlalchemy.orm import Session
from sqlalchemy import desc
from api.structure_db import FactPrediction, DimVehicle
from query_engine.sql_agent import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

class DriverNotificationAgent:
    def __init__(self, db: Session):
        self.db = db

    def generate_ai_message(self, context: dict) -> dict:
        """
        Uses LLM to generate natural language alert and action.
        """
        llm = get_llm()
        if not llm:
            return {
                "title": context["default_title"],
                "action": context["default_action"]
            }

        prompt = f"""
        Act as an AI Vehicle Safety Assistant.
        Context:
        - Vehicle: {context['model']}
        - Predicted Failure: {context['failure_type']}
        - Probability: {context['probability']}
        - Days remaining: {context['days']}
        - Status Level: {context['status']}

        Task:
        1. Generate a short 'title' (max 6 words) for the alert header.
        2. Generate a direct 'action' (max 1 sentence) for the driver.
        
        Output format: JSON {{ "title": "...", "action": "..." }}
        Language: French.
        """
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            import json
            content = response.content.strip().replace("```json", "").replace("```", "")
            return json.loads(content)
        except Exception as e:
            print(f"LLM Gen Error: {e}")
            return {
                "title": context["default_title"],
                "action": context["default_action"]
            }

    def get_vehicle_status(self, vehicle_original_id: str):
        """
        Retrieves the latest health status for a vehicle based on AI predictions.
        """
        # 1. Find the vehicle (internal ID)
        vehicle = self.db.query(DimVehicle).filter(DimVehicle.original_vehicle_id == vehicle_original_id).first()
        
        if not vehicle:
            return {
                "status": "not_found",
                "message": f"Véhicule {vehicle_original_id} introuvable.",
                "color": "gray"
            }

        # 2. Get latest prediction
        latest_pred = self.db.query(FactPrediction)\
            .filter(FactPrediction.vehicle_id == vehicle.vehicle_id)\
            .order_by(desc(FactPrediction.prediction_date))\
            .first()

        if not latest_pred:
            return {
                "status": "healthy",
                "vehicle_model": vehicle.engine_model,
                "message": "Aucune donnée récente. Véhicule considéré sain.",
                "color": "green",
                "action": "Continuer l'entretien standard."
            }

        # 3. Analyze Risk
        is_failure = latest_pred.predicted_failure_type != "Aucune panne"
        risk_level = latest_pred.failure_probability
        
        if is_failure and risk_level > 0.7:
            # CRITICAL ALERT
            context = {
                "model": vehicle.engine_model,
                "failure_type": latest_pred.predicted_failure_type,
                "probability": f"{int(risk_level * 100)}%",
                "days": latest_pred.predicted_days_before_failure,
                "status": "CRITICAL",
                "default_title": "ALERTE CRITIQUE : Panne Imminente",
                "default_action": "IMMOBILISATION RECOMMANDÉE. Contactez le centre de maintenance immédiatement."
            }
            ai_text = self.generate_ai_message(context)
            
            return {
                "status": "critical",
                "vehicle_model": vehicle.engine_model,
                "alert_title": ai_text.get("title", context["default_title"]),
                "failure_type": latest_pred.predicted_failure_type,
                "days_remaining": latest_pred.predicted_days_before_failure,
                "probability": f"{int(risk_level * 100)}%",
                "color": "#ef4444", # Red
                "action": ai_text.get("action", context["default_action"])
            }
        elif is_failure and risk_level > 0.4:
            # WARNING
            context = {
                "model": vehicle.engine_model,
                "failure_type": latest_pred.predicted_failure_type,
                "probability": f"{int(risk_level * 100)}%",
                "days": latest_pred.predicted_days_before_failure,
                "status": "WARNING",
                "default_title": "Avertissement : Signes de fatigue",
                "default_action": "Planifiez une vérification lors du prochain arrêt."
            }
            ai_text = self.generate_ai_message(context)

            return {
                "status": "warning",
                "vehicle_model": vehicle.engine_model,
                "alert_title": ai_text.get("title", context["default_title"]),
                "failure_type": latest_pred.predicted_failure_type,
                "days_remaining": latest_pred.predicted_days_before_failure,
                "probability": f"{int(risk_level * 100)}%",
                "color": "#f59e0b", # Amber
                "action": ai_text.get("action", context["default_action"])
            }
        else:
            # HEALTHY - No need for expensive LLM call for healthy state usually, but can be added if requested.
            return {
                "status": "healthy",
                "vehicle_model": vehicle.engine_model,
                "message": "Systèmes nominaux. Bonne route !",
                "color": "#10b981", # Green
                "action": "Aucune action requise."
            }
