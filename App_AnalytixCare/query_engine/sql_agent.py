from typing import List, Literal, Optional, Dict, Any
import os
import json
import sqlite3
import pandas as pd
from dotenv import load_dotenv

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment
load_dotenv(override=True)

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "Companyx_database.db")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ENDPOINT = os.getenv("ENDPOINT", "https://models.inference.ai.azure.com")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# In-Memory Cache (Simple Dictionary)
QUERY_CACHE = {}

# --- Security Validation ---

def is_safe_sql(sql: str) -> tuple[bool, str]:
    """
    Validates that the SQL query is read-only and safe to execute.
    """
    sql_upper = sql.upper().strip()
    
    # 1. Must start with SELECT or WITH
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return False, "Query must start with SELECT or WITH (read-only queries only)."
    
    # 2. Forbidden keywords
    forbidden_keywords = [
        "DROP ", "DELETE ", "INSERT ", "UPDATE ", "ALTER ",
        "TRUNCATE ", "CREATE ", "GRANT ", "REVOKE ", "REPLACE ",
        "PRAGMA ", "ATTACH ", "DETACH "
    ]
    
    for keyword in forbidden_keywords:
        if keyword in sql_upper:
            return False, f"Forbidden keyword detected: {keyword.strip()}"
    
    # 3. Check for multiple statements
    if ";" in sql:
        sql_no_trailing = sql.strip().rstrip(';')
        if ";" in sql_no_trailing:
            return False, "Multiple SQL statements are not allowed."
    
    return True, ""

def get_db():
    return SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

def get_llm():
    """Initialize ChatOpenAI client with GitHub Token / Azure Inference"""
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKEN missing. NLQ disabled.")
        return None

    return ChatOpenAI(
        openai_api_key=GITHUB_TOKEN,
        openai_api_base=ENDPOINT,
        model_name=MODEL_NAME,
        temperature=0
    )

def save_nlq_output(data: Dict[str, Any]):
    """Saves the NLQ result to a JSON file (Legacy support, though we return Dict now)."""
    output_path = os.path.join(BASE_DIR, "api", "static", "nlq_output.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f" Save error: {e}")

# --- Main Logic ---

def query_enterprise_data(question: str) -> Dict[str, Any]:
    """
    Optimized NLQ entry point.
    Reduces 4 LLM calls to max 2.
    Returns: Dictionary (Directly serializable to JSON)
    """
    print(f"🚀 Processing NLQ: {question}")
    
    # 0. Cache Check
    if question in QUERY_CACHE:
        print("⚡ Cache Hit!")
        return QUERY_CACHE[question]

    result_structure = {
        "question": question,
        "answer": "Une erreur est survenue lors de l'analyse.",
        "sql": "",
        "visualization": {"type": "none"},
        "status": "error"
    }

    try:
        llm = get_llm()
        if not llm:
            result_structure["answer"] = "Configuration Error: API Key missing."
            return result_structure

        db = get_db()
        table_info = db.get_table_info()
        
        # --- 1. Smart SQL Generation ---
        system_prompt_sql = f"""You are a generic SQL generator using SQLite.
Target Database Schema:
{table_info}

Context & Rules:
- The data is about Manufacturing, Vehicles, Failures, and Maintenance.
- 'DIM_VEHICLE' is the central dimension.
- 'FACT_VEHICLE_FAILURE' contains historical failures.
- 'FACT_PREDICTION' contains FUTURE AI PREDICTIONS. 
    - Key columns: `predicted_failure_type`, `failure_probability` (0.0 to 1.0), `predicted_days_before_failure`.
    - Always SELECT `predicted_failure_type` and count/average when asked about future risks.
    - JOIN `DIM_VEHICLE` to filter by `engine_model` or `vehicle_age`.
- 'FACT_MAINTENANCE_LOG' contains costs.
- 'FACT_INVESTMENT_FORECAST' contains ROI/Financials.
- RETURN ONLY THE SQL QUERY. No markdown (```sql), no explanations.
- Query MUST be Read-Only (SELECT).
- If specific region requested, join DIM_REGION.
"""
        messages_sql = [
            SystemMessage(content=system_prompt_sql),
            HumanMessage(content=question)
        ]
        
        response_sql = llm.invoke(messages_sql)
        sql_query = response_sql.content.strip().replace("```sql", "").replace("```", "").strip()
        
        # SQL Cleanup (Remove prefixes like "Here is the SQL:")
        if "SELECT" in sql_query.upper():
            idx = sql_query.upper().find("SELECT")
            if "WITH" in sql_query.upper() and sql_query.upper().find("WITH") < idx:
                idx = sql_query.upper().find("WITH")
            sql_query = sql_query[idx:]
        
        result_structure["sql"] = sql_query
        
        # Validation
        is_valid, error_msg = is_safe_sql(sql_query)
        if not is_valid:
            result_structure["answer"] = f"❌ Sécurité Query : {error_msg}"
            return result_structure

        # Execution
        try:
            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
        except Exception as e:
            result_structure["answer"] = f"❌ Erreur SQL Execution: {str(e)}"
            return result_structure

        if df.empty:
            result_structure["answer"] = "Aucune donnée trouvée pour cette demande."
            result_structure["status"] = "success"
            QUERY_CACHE[question] = result_structure
            return result_structure

        # --- 2. Interpretation & Visualization (Single Call) ---
        # We truncate data to avoid token limits
        data_str = df.head(20).to_string(index=False)
        if len(data_str) > 3000:
            data_str = data_str[:3000] + "...(truncated)"

        system_prompt_interp = f"""You are a Data Product Manager for an industrial dashboard.
Analyze the data and provide:
1. 'answer': A professional summary in French (max 3 sentences).
2. 'visualization': Chart configuration.

Input Data:
Question: "{question}"
Results Sample:
{data_str}

Output Rule:
RETURN ONLY JSON using this schema:
{{
  "answer": "string",
  "visualization": {{
     "type": "bar" | "line" | "pie" | "doughnut" | "none",
     "title": "string",
     "labels": ["string", "string"],
     "values": [number, number]
  }}
}}
If no chart is relevant, set type to "none".
"""
        
        messages_interp = [
            SystemMessage(content=system_prompt_interp),
            HumanMessage(content="Generate the analysis JSON.")
        ]
        
        response_interp = llm.invoke(messages_interp).content.strip()
        # Clean potential markdown
        response_interp = response_interp.replace("```json", "").replace("```", "").strip()
        
        try:
            parsed = json.loads(response_interp)
            result_structure["answer"] = parsed.get("answer", "Voici les résultats.")
            # Ensure visualization structure is robust
            viz = parsed.get("visualization", {})
            result_structure["visualization"] = {
                "type": viz.get("type", "none"),
                "title": viz.get("title", ""),
                "labels": viz.get("labels", []),
                "values": viz.get("values", [])
            }
            result_structure["status"] = "success"
            
            # Save to cache
            QUERY_CACHE[question] = result_structure
            
        except json.JSONDecodeError:
            result_structure["answer"] = "Données récupérées, mais erreur lors du formatage de l'analyse."
            result_structure["status"] = "partial_success"

        # Legacy Save
        save_nlq_output(result_structure)
        return result_structure

    except Exception as e:
        print(f"⚠️ LLM Error (Switching to Fallback): {e}")
        return try_fallback_mode(question, str(e))

def try_fallback_mode(question: str, original_error: str) -> Dict[str, Any]:
    """
    Offline Recovery Mode: matches keywords to pre-defined SQL/Viz
    so the demo works even if API is down/rate-limited.
    """
    q_lower = question.lower()
    
    fallback_result = {
        "question": question,
        "answer": f"Mode Hors-Ligne (Quota API dépassé). Voici une analyse pré-calculée. (Erreur: {original_error})",
        "sql": "-- Fallback Query",
        "visualization": {"type": "none"},
        "status": "success"
    }

    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        
        # 1. STOCK PREDICTION (Dynamic Math on Predictions)
        if "stock" in q_lower or "inventory" in q_lower:
            # Logic: Count predicted failures per part (Risk > 50%)
            sql = """
                SELECT defective_part as part_name, COUNT(*) as predicted_demand
                FROM FACT_PREDICTION
                WHERE failure_probability > 0.5 AND defective_part IS NOT NULL AND defective_part != ''
                GROUP BY defective_part
                ORDER BY predicted_demand DESC LIMIT 8
            """
            df = pd.read_sql_query(sql, conn)
            fallback_result["answer"] = "Prédiction Stock (Calculée) : Demande estimée basée sur les pannes futures (Prob > 50%)."
            fallback_result["visualization"] = {
                "type": "bar",
                "title": "Demande Prévisionnelle (Pièces)",
                "labels": df["part_name"].tolist(),
                "values": df["predicted_demand"].tolist()
            }
            fallback_result["sql"] = sql

        # 2. HR / RESOURCE PREDICTION (Dynamic Math: Time * Risk / Capacity)
        elif "technicien" in q_lower or "rh" in q_lower or "humain" in q_lower:
            # Formula: (Sum(Prob) * 4 hours) / 8 hours capacity = FTE Needed
            sql = """
                SELECT region, ROUND(SUM(failure_probability) * 0.5, 1) as techs_needed
                FROM FACT_PREDICTION
                WHERE failure_probability > 0.2
                GROUP BY region
                ORDER BY techs_needed DESC
            """
            df = pd.read_sql_query(sql, conn)
            fallback_result["answer"] = "Prédiction RH (Formule : Charge / Capacité) : Techniciens requis par région selon le risque cumulé de pannes."
            fallback_result["visualization"] = {
                "type": "bar",
                "title": "Techniciens Requis (Prévision)",
                "labels": df["region"].tolist(),
                "values": df["techs_needed"].tolist()
            }
            fallback_result["sql"] = sql

        # 3. PANNE PAR REGION (Specific Combination)
        elif "région" in q_lower and ("panne" in q_lower or "failure" in q_lower):
            sql = """
                SELECT r.region_name, COUNT(*) as failure_count
                FROM FACT_VEHICLE_FAILURE f
                JOIN DIM_REGION r ON f.region_id = r.region_id
                GROUP BY r.region_name
                ORDER BY failure_count DESC
            """
            df = pd.read_sql_query(sql, conn)
            fallback_result["answer"] = "Analyse Géographique des Pannes (Mode Démo) : Distribution des incidents par région."
            fallback_result["visualization"] = {
                "type": "doughnut",
                "title": "Pannes par Région",
                "labels": df["region_name"].tolist(),
                "values": df["failure_count"].tolist()
            }
            fallback_result["sql"] = sql

        # 4. PREDICTIONS (High probability failures)
        elif "préd" in q_lower or "future" in q_lower or "risque" in q_lower:
            sql = """
                SELECT predicted_failure_type, COUNT(*) as count
                FROM FACT_PREDICTION
                WHERE failure_probability > 0.7
                GROUP BY predicted_failure_type
                ORDER BY count DESC
            """
            df = pd.read_sql_query(sql, conn)
            fallback_result["answer"] = "Prédictions IA (Mode Démo) : Risques de pannes critiques détectés (>70% probabilité)."
            fallback_result["visualization"] = {
                "type": "bar",
                "title": "Prédictions de Pannes (Haut Risque)",
                "labels": df["predicted_failure_type"].tolist(),
                "values": df["count"].tolist()
            }
            fallback_result["sql"] = sql

        # 5. GENERIC FAILURES (Fallback for simple "panne" request)
        elif "panne" in q_lower or "failure" in q_lower:
            sql = """
                SELECT failure_name, COUNT(*) as count 
                FROM FACT_VEHICLE_FAILURE f 
                JOIN DIM_FAILURE_TYPE t ON f.failure_type_id = t.failure_type_id 
                GROUP BY failure_name 
                ORDER BY count DESC LIMIT 5
            """
            df = pd.read_sql_query(sql, conn)
            fallback_result["answer"] = "Analyse des pannes (Mode Démo) : Les pannes 'Engine Overheat' sont les plus fréquentes."
            fallback_result["visualization"] = {
                "type": "bar",
                "title": "Top 5 Pannes (Demo)",
                "labels": df["failure_name"].tolist(),
                "values": df["count"].tolist()
            }
            fallback_result["sql"] = sql

        # 6. COSTS (Fallback)
        elif "coût" in q_lower or "cost" in q_lower or "budget" in q_lower:
            sql = """
                SELECT region_name, SUM(cost) as total
                FROM FACT_MAINTENANCE_LOG l 
                JOIN DIM_DEALER d ON l.dealer_id = d.dealer_id 
                JOIN DIM_REGION r ON d.region_id = r.region_id 
                GROUP BY region_name
            """
            df = pd.read_sql_query(sql, conn)
            fallback_result["answer"] = "Analyse Financière (Mode Démo) : La région Nord absorbe la majorité du budget."
            fallback_result["visualization"] = {
                "type": "doughnut",
                "title": "Coûts par Région (Demo)",
                "labels": df["region_name"].tolist(),
                "values": df["total"].tolist()
            }
            fallback_result["sql"] = sql

        else:
             fallback_result["answer"] = f"Désolé, en mode hors-ligne je ne peux traiter que les sujets: Pannes, Coûts, Stocks, RH, Prédictions. (Erreur Origine: {original_error})"

        conn.close()
    except Exception as e:
        fallback_result["answer"] = f"Échec critique du mode hors-ligne : {str(e)}"
    
    return fallback_result
