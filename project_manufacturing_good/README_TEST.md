# 🧪 Guide de Test - API Maintenance Prédictive

Ce guide vous explique comment lancer l'application et tester les prédictions avec vos fichiers CSV.

## 1. Préparation de l'environnement

Assurez-vous d'avoir installé les dépendances nécessaires :
```bash
pip install fastapi uvicorn pandas lightgbm scikit-learn sqlalchemy joblib requests
```

## 2. Lancer le Serveur API

Ouvrez un terminal et lancez le serveur FastAPI :
```bash
python api/main.py
```
*Le serveur sera accessible sur **http://127.0.0.1:8000***.  
*Vous pouvez voir la documentation interactive (Swagger) sur **http://127.0.0.1:8000/docs***.

## 3. Tester l'envoi d'un fichier CSV

Nous avons créé un script (`scripts/test_upload.py`) pour simplifier les tests. Ouvrez un **deuxième terminal** et lancez :

```bash
# Pour utiliser le fichier par défaut :
python scripts/test_upload.py

# Pour utiliser spécifiquement le fichier de test réduit (data_test.csv) :
python scripts/test_upload.py data/raw/data_test.csv
```

### Ce que fait ce script :
1. Il prend le fichier de données brutes (`data/raw/Pannes_moteurs_equilibre_Maroc.csv`).
2. Il l'envoie à l'API (`/predict/csv`).
3. Il affiche un **aperçu des résultats** (prédits par l'IA) directement dans votre terminal.

## 4. Vérifier les résultats en Base de Données

Toutes les prédictions sont enregistrées dans la base de données SQL locale `predictions.db`.  
La table contient **toutes les colonnes originales** du CSV plus les résultats de l'IA.

### Pour consulter les dernières prédictions via l'API :
Allez sur : [http://127.0.0.1:8000/predictions?limit=5](http://127.0.0.1:8000/predictions?limit=5)

### Pour vérifier manuellement (en Python) :
```python
import sqlite3
import pandas as pd

# Connexion à la base
conn = sqlite3.connect('predictions.db')
df = pd.read_sql_query("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT 10", conn)

# Affichage des colonnes cibles
print(df[['vehicle_id', 'type_panne_moteur', 'jours_avant_panne', 'probabilite_panne']])
conn.close()
```

## 5. Fonctionnement des Prédictions IA

- **`type_panne_moteur`** : Le type de panne prédit par le modèle de classification.
- **`jours_avant_panne`** : Nombre de jours estimés avant la panne (désormais un **entier arrondi**).
- **`probabilite_panne`** : Indice de confiance brut du modèle (ex: 0.98).

---
💡 **Note** : Si vous modifiez les modèles ou le dossier `data/`, vous pouvez ré-entraîner l'IA en utilisant `python scripts/retrain.py`.
