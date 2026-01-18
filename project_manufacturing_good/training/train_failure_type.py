import os
import sys
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    log_loss,
    confusion_matrix,
    classification_report
)
from joblib import dump

df = pd.read_csv("data/processed/dataset_pretraite.csv")
y = df["failure_type"]
X = df.drop(
    columns=["failure_type", "days_before_failure", "vehicle_id"],
    errors="ignore"
)

os.makedirs("models", exist_ok=True)
dump(list(X.columns), "models/features.joblib")


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml_logic.tracking import ExperimentTracker

tracker = ExperimentTracker("Failure_Type_Classification")


with tracker.start_run():

    params = {
        "n_estimators": 124,
        "learning_rate": 0.02895098757784187,
        "num_leaves": 128,
        "max_depth": 7,
        "min_child_samples": 73,
        "subsample": 0.8776926679755974,
        "colsample_bytree": 0.692362366298702,
        "random_state": 42,
        "n_jobs": -1
    }

    tracker.log_params(params)

    model_type = LGBMClassifier(
        verbose=-1,
        **params
    )

    model_type.fit(X_train, y_train)

    y_pred = model_type.predict(X_test)
    y_proba = model_type.predict_proba(X_test)

    
    tracker.log_metrics({
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        "precision_macro": precision_score(y_test, y_pred, average="macro"),
        "recall_macro": recall_score(y_test, y_pred, average="macro"),
        "f1_macro": f1_score(y_test, y_pred, average="macro"),
        "log_loss": log_loss(y_test, y_proba)
    })

    
    tracker.log_model(model_type, "failure_type_model")


print("\n===== TEST MODEL FAILURE TYPE =====")
print(f"Accuracy              : {accuracy_score(y_test, y_pred):.4f}")
print(f"Balanced Accuracy     : {balanced_accuracy_score(y_test, y_pred):.4f}")
print(f"Precision (macro)     : {precision_score(y_test, y_pred, average='macro'):.4f}")
print(f"Recall (macro)        : {recall_score(y_test, y_pred, average='macro'):.4f}")
print(f"F1-score (macro)      : {f1_score(y_test, y_pred, average='macro'):.4f}")
print(f"Log Loss              : {log_loss(y_test, y_proba):.4f}")

print("\nMatrice de confusion :")
print(confusion_matrix(y_test, y_pred))

print("\nRapport de classification :")
print(classification_report(y_test, y_pred))


dump(model_type, "models/failure_type_model.joblib")
print("[OK] Failure type model trained and saved")
