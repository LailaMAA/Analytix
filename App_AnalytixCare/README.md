# Projet Maintenance Prédictive - Industrie 4.0

Ce projet implémente un système complet de maintenance prédictive pour les moteurs industriels au Maroc. Il utilise le Machine Learning pour prédire simultanément le **type de panne** et le **délai avant la prochaine panne**.

---

## 🚀 Architecture du Système

1.  **Entrée des données** : Chargement de fichiers CSV ou données via API.
2.  **Prétraitement** : Nettoyage, encodage catégoriel (LabelEncoder) et normalisation (MinMaxScaler).
3.  **Moteur ML** : 
    *   **Classification** (LightGBM) : Prédit le type de panne probable.
    *   **Régression** (LightGBM) : Estime le nombre de jours restants avant la panne.
4.  **Backend FastAPI** : Automatise le pipeline et sert les prédictions.
5.  **Base de Données** : Stockage automatique des résultats dans SQLite pour historisation.

---

## 📊 Performance des Modèles

### 🔹 Modèle de Classification (Type de Panne)
*   **Accuracy** : 90.60%
*   **F1-Score (macro)** : 90.68%
*   **Precision (macro)** : 90.68%
*   **Log Loss** : 0.2948

### 🔹 Modèle de Régression (Jours avant Panne)
*   **MAE** (Mean Absolute Error) : 0.0667
*   **RMSE** (Root Mean Squared Error) : 0.0886
*   **R² Score** : 0.5001

---

## 🛠️ Utilisation de l'API FastAPI

### Démarrage
```bash
python api/main.py
```

### Endpoints Principaux
*   `POST /predict/csv` : Envoyer un fichier CSV pour analyse massive.
*   `GET /predictions` : Consulter l'historique des prédictions stockées en base de données.
*   `GET /docs` : Accéder à l'interface interactive Swagger.

---

## 🛠️ Outils et Automatisation

### 1. Test Rapide de l'API
Pour envoyer un fichier CSV à l'API et voir les résultats directement dans votre terminal :
```bash
python scripts/test_upload.py data/raw/Pannes_moteurs_equilibre_Maroc.csv
```

### 2. Réentraînement Automatisé
Si vous avez de nouvelles données et souhaitez mettre à jour vos modèles (avec versionnement automatique) :
```bash
python scripts/retrain.py
```
*Note : Cette commande crée une version horodatée dans `models/versions/` et met à jour les modèles utilisés par l'API.*

---

## 📂 Structure du Projet
*   `data/` : Datasets bruts et traités.
*   `models/` : Modèles entraînés (`.joblib`) et fichiers de preprocessing (`.pkl`).
*   `preprocessing/` : Scripts de nettoyage et préparation.
*   `training/` : Scripts d'entraînement des modèles.
*   `inference/` : Logique de prédiction réutilisable.
*   `api/` : Application backend FastAPI et gestion de la base de données.

---

## ✅ Bonnes Pratiques Appliquées
1.  **Isolation** : Séparation stricte entre l'entraînement et l'inférence.
2.  **Robustesse** : Gestion automatique des encodages et du scaling lors des nouvelles prédictions.
3.  **Traçabilité** : Historisation de chaque prédiction avec timestamp et ID véhicule dans la base de données.
4.  **Pérennité** : Modèles versionnés et réutilisables via un service standardisé.

---
*Développé pour l'optimisation de la maintenance industrielle au Maroc.*
