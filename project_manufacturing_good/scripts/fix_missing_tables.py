import sys
import os

# Add parent directory to path to import api modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.structure_db import init_enterprise_db

def fix_db():
    print("🛠️ Vérification et création des tables manquantes...")
    try:
        init_enterprise_db()
        print("✅ Base de données initialisée. La table FACT_PREDICTION devrait être présente.")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    fix_db()
