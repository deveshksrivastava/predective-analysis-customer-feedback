"""Train the Phase 2 churn model outside the notebook.

Winning recipe from ``notebooks/02_churn_prototype.ipynb``: a sigmoid-calibrated
Logistic Regression (class_weight="balanced", C=10) over scaled numerics +
one-hot categoricals. The saved bundle carries the model AND its decision
threshold, so the API can never load one without the other.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = PROJECT_ROOT / "data" / "telco_churn.csv"
DEFAULT_MODEL = PROJECT_ROOT / "models" / "churn_model.joblib"

NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod",
]

# Chosen in the notebook's cost sweep (retention offer ~$50 vs lost customer
# ~$500): with a 10:1 cost asymmetry the optimal threshold is the cost ratio.
CHURN_THRESHOLD = 0.10


def build_churn_pipeline(C=10.0):
    """Preprocessing + classifier, calibrated so probabilities are honest.

    Same swappable shape as Phase 1: everything (encoders included) fits inside
    the pipeline on training data only, so there is no leakage and a single
    object can be saved/loaded.
    """
    pipeline = Pipeline([
        ("pre", ColumnTransformer([
            ("num", StandardScaler(), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             CATEGORICAL),
        ])),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=C)),
    ])
    return CalibratedClassifierCV(pipeline, method="sigmoid", cv=5)


def load_churn_data(data_path=DEFAULT_DATA):
    """Load the Telco CSV and apply the notebook's cleaning. Returns (X, y)."""
    df = pd.read_csv(data_path)
    # 11 brand-new customers (tenure=0) have blank TotalCharges -> 0.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0.0)
    y = (df["Churn"] == "Yes").astype(int)
    X = df[NUMERIC + CATEGORICAL]
    return X, y


def train_churn(data_path=DEFAULT_DATA, model_path=DEFAULT_MODEL) -> Path:
    """Fit the winning recipe on the full dataset and save it. Returns the path."""
    X, y = load_churn_data(data_path)
    model = build_churn_pipeline()
    model.fit(X, y)

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "threshold": CHURN_THRESHOLD}, model_path)
    return model_path


def load_churn_model(path=DEFAULT_MODEL):
    """Load a bundle saved by :func:`train_churn`. Returns ``(model, threshold)``."""
    bundle = joblib.load(path)
    return bundle["model"], bundle["threshold"]


def churn_probability(model, customer: dict) -> float:
    """Churn probability for one customer given as a plain field dict."""
    row = pd.DataFrame([customer])[NUMERIC + CATEGORICAL]
    return float(model.predict_proba(row)[0, 1])


if __name__ == "__main__":
    path = train_churn()
    print(f"Churn model saved to {path}")
