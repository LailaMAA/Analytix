from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("sqlite:///Companyx_database (1).db")

df = pd.read_sql("SELECT * FROM FACT_PREDICTION LIMIT 5", engine)

print("✅ Colonnes trouvées :")
print(df.columns)
print("\n📄 Aperçu des données :")
print(df.head())
