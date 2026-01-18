import os
import sys
import pandas as pd
import numpy as np
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    explained_variance_score
)
from joblib import dump

df = pd.read_csv("data/processed/dataset_pretraite.csv")


target_col = "days_before_failure"
if target_col not in df.columns:
    raise ValueError(f"Target '{target_col}' not found in dataset")

y = df[target_col]
X = df.drop(
    columns=[
        target_col,
    ],
    errors="ignore"
)


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml_logic.tracking import ExperimentTracker

tracker = ExperimentTracker("days_before_failure_Regression")


with tracker.start_run():

    params = {
    "n_estimators":500,
    "learning_rate":0.05,
    "num_leaves":31,
    "max_depth":-1,
    "subsample":0.8,
    "colsample_bytree":0.8,
    "random_state":42,
    "n_jobs":-1
}


    tracker.log_params(params)

    model_days = LGBMRegressor(
        verbose=-1,
        **params
    )

    model_days.fit(X_train, y_train)

    
    y_pred = model_days.predict(X_test)

    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    explained_var = explained_variance_score(y_test, y_pred)

    tracker.log_metrics({
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "explained_variance": explained_var
    })

    tracker.log_model(model_days, "days_before_failure_model")


print("\n===== TEST MODEL DAYS BEFORE FAILURE =====")
print(f"MAE                : {mae:.4f}")
print(f"RMSE               : {rmse:.4f}")
print(f"R²                 : {r2:.4f}")
print(f"Explained Variance : {explained_var:.4f}")


os.makedirs("models", exist_ok=True)
dump(model_days, "models/days_before_failure_model.joblib")
print("[OK] DAYS BEFORE FAILURE model trained and saved")
