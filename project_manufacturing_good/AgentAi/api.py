from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from ai_agent import MaintenanceAgent
from database import DatabaseManager
import os
import json

app = FastAPI(title="AI Maintenance Dashboard API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_agent_data():
    """Helper to fetch and process data through the agent."""
    db_manager = DatabaseManager()
    df = db_manager.fetch_predictions()
    
    if df is None or df.empty:
        # Note: In a production app, we'd handle this better. 
        # For this demo, we assume the DB is available or we could generate dummy data.
        return None
    
    return MaintenanceAgent(df)

@app.get("/api/stats")
async def get_stats():
    """Returns high-level KPIs."""
    agent = get_agent_data()
    if not agent:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    avg_days = agent.data['predicted_days_before_failure'].mean()
    critical_7d = agent.identify_critical_failures(7)
    warranty_count = agent.evaluate_business_impact(agent.identify_critical_failures(30))['warranty_exposure_count']
    
    return {
        "avg_days_before_failure": round(avg_days, 1),
        "critical_failures_7d": len(critical_7d),
        "warranty_exposure": warranty_count,
        "total_vehicles": len(agent.data)
    }

@app.get("/api/anomalies")
async def get_anomalies():
    """Returns detected regional anomalies."""
    agent = get_agent_data()
    if not agent:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    return {"anomalies": agent.detect_abnormal_patterns()}

@app.get("/api/parts")
async def get_parts():
    """Returns estimated spare parts demand."""
    agent = get_agent_data()
    if not agent:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    demand = agent.predict_spare_parts_demand(30)
    return demand.to_dict('records')

@app.get("/api/briefing")
async def get_briefing():
    """Returns the AI-generated daily briefing."""
    # We first try to read the last generated file
    try:
        if os.path.exists("daily_briefing.md"):
            with open("daily_briefing.md", "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content}
    except Exception:
        pass
    
    # Otherwise, generate a fresh one (might take time due to LLM call)
    agent = get_agent_data()
    if not agent:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    content = agent.generate_daily_briefing()
    return {"content": content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
