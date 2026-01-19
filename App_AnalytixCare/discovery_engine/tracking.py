import mlflow
import os
from typing import Dict, Any, Optional
from core.config import settings
from core.logging import logger


class ExperimentTracker:
    """
    Wrapper around MLflow for experiment tracking.
    """

    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.tracking_uri = settings.MLFLOW_TRACKING_URI

        if not self.tracking_uri.startswith("http") and not self.tracking_uri.startswith("sqlite"):
            os.makedirs(self.tracking_uri, exist_ok=True)

        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(experiment_name)

        logger.info(
            f"MLflow Initialized. Experiment: {experiment_name}, URI: {self.tracking_uri}"
        )

    def start_run(self, run_name: Optional[str] = None):
        """Start a new MLflow run."""
        return mlflow.start_run(run_name=run_name)

    def log_params(self, params: Dict[str, Any]):
        """Log parameters."""
        mlflow.log_params(params)

    def log_metrics(self, metrics: Dict[str, float]):
        """Log metrics."""
        mlflow.log_metrics(metrics)

    def log_model(self, model: Any, name: str):
        """
        Log sklearn/lightgbm model using the new MLflow API.
        `name` is the logical name of the model inside MLflow.
        """
        mlflow.sklearn.log_model(
            sk_model=model,
            name=name
        )

    def log_artifact(self, local_path: str):
        """Log a local file as artifact."""
        mlflow.log_artifact(local_path)
