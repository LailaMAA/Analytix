# Documentation Détaillée du Système de Maintenance Prédictive

Ce document fournit une vue d'ensemble détaillée du fonctionnement de l'application et la description de chaque fichier clès.

## 1. Fonctionnement de l'Application

Le système fonctionne comme un pipeline intelligent qui transforme des données brutes de véhicules en prédictions actionnables.

### Le Flux de Données
1.  **Entrée** : Un utilisateur ou un système tiers envoie un fichier CSV contenant des données de véhicules (kilométrage, températures, pression, etc.) à l'API.
2.  **Traitement (Le Cerveau)** :
    *   L'application lit ce fichier.
    *   Elle "habille" les données (prétraitement) pour qu'elles ressemblent exactement à celles utilisées lors de l'apprentissage (même mise à l'échelle, mêmes codes).
    *   Elle interroge deux experts (modèles IA) :
        *   **Expert 1 (Classification)** : "Quel genre de panne va arriver ?" (ex: Surchauffe, Pression Huile, ou *Aucune panne*).
        *   **Expert 2 (Régression)** : "Dans combien de jours ?"
    *   **Règle Métier** : Si l'Expert 1 dit "Aucune panne", on force l'Expert 2 à dire "0 jours" (ou on ignore sa réponse), pour éviter des contradictions.
3.  **Sortie & Mémoire** :
    *   Le système renvoie la réponse en format JSON immédiat.
    *   Il archive également cette "consultation" dans sa base de données (`predictions.db`) pour que vous puissiez plus tard poser des questions comme "Combien de surchauffes avons-nous prédites cette semaine ?".

---

## 2. Description Détaillée des Fichiers

Voici le rôle précis de chaque fichier dans votre projet `project_manufacturing`.

### 📂 Dossier Racine
*   **`README.md`** : Le guide de démarrage rapide. Contient les commandes pour lancer le serveur et tester.
*   **`requirements.txt`** (supposé présent) : Liste des librairies Python nécessaires (pandas, fastapi, lightgbm, etc.).

### 📂 `api/` (Le Serveur)
*   **`main.py`** : **Le point d'entrée du serveur web**.
    *   Définit les "routes" (URL) comme `/predict/csv`.
    *   Reçoit les fichiers, appelle le service de prédiction, et gère la sauvegarde en base de données.
*   **`database.py`** : **Gestion de la Base de Données**.
    *   Définit la structure de la table `predictions` (colonnes, types).
    *   Gère la connexion au fichier `predictions.db`.

### 📂 `inference/` (Le Cerveau)
*   **`prediction_service.py`** : **Le cœur de la logique**.
    *   Charge les modèles IA (`.joblib`) au démarrage.
    *   Contient la fonction `preprocess()` qui transforme les données brutes (nettoyage, scaling).
    *   Contient la fonction `predict()` qui interroge les modèles et applique vos règles métier (comme forcer les jours à 0 si "Aucune panne").

### 📂 `scripts/` (Les Outils)
*   **`test_upload.py`** : **Script de test manuel**. Permet d'envoyer un fichier CSV à l'API depuis la ligne de commande pour voir si tout marche sans utiliser un navigateur.
*   **`retrain.py`** : **Script de mise à jour automatique**.
    *   Relance tout le processus d'apprentissage sur de nouvelles données.
    *   Sauvegarde de nouvelles versions des modèles dans `models/versions/` et met à jour les modèles actifs.

### 📂 `training/` (L'École des IA)
*   **`train_type_panne.py`** : Script dédié à l'entraînement du modèle de **Classification** (Type de panne).
*   **`train_jours_avant_panne.py`** : Script dédié à l'entraînement du modèle de **Régression** (Jours restants).

### 📂 `preprocessing/`
*   **`preprocess.py`** : **L'usine de traitement**.
    *   Prend les données brutes (`data/raw/`).
    *   Génère les données propres (`dataset_pretraite.csv`).
    *   Crée les "outils" de traduction (`scaler.pkl`, `label_encoders.pkl`) qui seront réutilisés par l'API.

### 📂 `models/` (Le Coffre-fort)
Contient les fichiers binaires générés par l'entraînement. Ne pas modifier manuellement.
*   `type_panne_model.joblib` : Le cerveau "Classification".
*   `jours_avant_panne_model.joblib` : Le cerveau "Régression".
*   `scaler.pkl`, `label_encoders.pkl` : Les dictionnaires de traduction pour les données.

### 📂 `docs/`
*   `schema_fonctionnement.md` : Schéma technique et visuel (Mermaid).
*   `nlq_schema.md` : Documentation pour l'agent NLQ, expliquant le sens des données.
*   `documentation_detaillee_projet.md` : Ce fichier.

---
Ce projet est structuré pour être **modulaire** : vous pouvez améliorer l'entraînement (`training/`) sans casser l'API (`api/`), ou changer la base de données (`api/database.py`) sans toucher aux modèles.
