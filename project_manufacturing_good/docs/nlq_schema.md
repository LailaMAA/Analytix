# Schéma de la Base de Données - Système de Prédiction de Maintenance

Ce document décrit le schéma de la table `predictions` utilisée pour stocker les prédictions de maintenance prédictive. Cette base de données est conçue pour être interrogée par un système NLQ (Natural Language Querying).

## Table : `predictions`

Cette table contient l'historique des prédictions effectuées par le modèle ML. Chaque ligne correspond à une requête de prédiction pour un véhicule donné.

### Colonnes

#### Identifiants
- **`id`** (`Integer`, Clé Primaire) : Identifiant unique de l'enregistrement de prédiction.
- **`vehicle_id`** (`String`) : Identifiant unique du véhicule (ex: "VEH001").

#### Caractéristiques du Véhicule (Inputs)
Ces colonnes correspondent aux données d'entrée fournies lors de la prédiction.

- **`Model_moteur`** (`String`) : Le modèle du moteur du véhicule (ex: "i4-1.6L").
- **`age_vehicule`** (`Float`) : L'âge du véhicule en années.
- **`kilometrage_total`** (`Float`) : Le kilométrage total parcouru par le véhicule.
- **`Garantie`** (`String`) : Statut de la garantie ("Oui" ou "Non").
- **`date_derniere_maintenance`** (`String`) : Date de la dernière maintenance effectuée.
- **`Date_mise_service`** (`String`) : Date de mise en service du véhicule.

#### Données Télémétriques (Inputs)
Données capteurs remontées par le véhicule.

- **`engine_rpm`** (`Float`) : Régime moteur (tours par minute).
- **`engine_load`** (`Float`) : Charge moteur (%).
- **`engine_temperature`** (`Float`) : Température du moteur (°C).
- **`oil_temperature`** (`Float`) : Température de l'huile (°C).
- **`oil_pressure`** (`Float`) : Pression de l'huile (psi/bar).
- **`fuel_pressure`** (`Float`) : Pression du carburant.

#### Localisation et Pièces (Inputs)
- **`region`** (`String`) : Région d'opération du véhicule.
- **`ville`** (`String`) : Ville d'opération.
- **`Piece_defectuee`** (`String`) : (Input) Pièce signalée comme défectueuse lors de l'inspection (peut être vide ou "unknown" pour une prédiction pure).
- **`piece_impacte`** (`String`) : (Input) Pièce impactée.

#### Résultats de la Prédiction (Outputs)
Ces colonnes contiennent les résultats générés par le modèle d'IA.

- **`type_panne_moteur`** (`String`) : **Type de panne prédit** par le modèle (ex: "Surchauffe", "Pression Huile"). *Note : Ceci est la prédiction, pas nécessairement une vérité terrain.*
- **`jours_avant_panne`** (`Integer`) : **Estimation du nombre de jours** restants avant la prochaine panne.
- **`probabilite_panne`** (`Float`) : Score de confiance ou probabilité associée à la prédiction de panne (valeur entre 0 et 1).

#### Métadonnées
- **`timestamp`** (`DateTime`) : Date et heure auxquelles la prédiction a été effectuée et enregistrée.

---
## Exemple de requêtes NLQ supportées

Aves ce schéma, le système peut répondre à des questions telles que :
- "Quels sont les véhicules qui risquent de tomber en panne dans moins de 10 jours ?" (Filtre sur `jours_avant_panne < 10`)
- "Montre-moi l'historique des prédictions pour le véhicule VEH001." (Filtre sur `vehicle_id`)
- "Quel est le type de panne le plus fréquent prédit à Casablanca ?" (Aggregation sur `type_panne_moteur` filtré par `ville = 'Casablanca'`)
