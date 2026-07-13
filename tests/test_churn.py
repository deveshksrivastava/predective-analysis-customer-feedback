"""Tests for the Phase 2 churn pipeline (src/churn.py)."""

import pandas as pd
import pytest

from src.churn import (
    CATEGORICAL,
    CHURN_THRESHOLD,
    DEFAULT_DATA,
    NUMERIC,
    build_churn_pipeline,
    churn_probability,
    load_churn_data,
    load_churn_model,
    train_churn,
)

HIGH_RISK = {
    "gender": "Female", "SeniorCitizen": 0, "Partner": "No", "Dependents": "No",
    "tenure": 2, "PhoneService": "Yes", "MultipleLines": "No",
    "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No",
    "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
    "StreamingMovies": "Yes", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check", "MonthlyCharges": 95.0, "TotalCharges": 190.0,
}
LOW_RISK = {
    "gender": "Male", "SeniorCitizen": 0, "Partner": "Yes", "Dependents": "Yes",
    "tenure": 68, "PhoneService": "Yes", "MultipleLines": "Yes",
    "InternetService": "DSL", "OnlineSecurity": "Yes", "OnlineBackup": "Yes",
    "DeviceProtection": "Yes", "TechSupport": "Yes", "StreamingTV": "No",
    "StreamingMovies": "No", "Contract": "Two year", "PaperlessBilling": "No",
    "PaymentMethod": "Bank transfer (automatic)", "MonthlyCharges": 60.0,
    "TotalCharges": 4080.0,
}


@pytest.fixture(scope="module")
def sample_csv(tmp_path_factory):
    """A small stratified slice of the real dataset, for fast training in tests."""
    df = pd.read_csv(DEFAULT_DATA)
    sample = (
        df.groupby("Churn", group_keys=False)
        .apply(lambda g: g.sample(400, random_state=42), include_groups=False)
        .assign(Churn=lambda d: df.loc[d.index, "Churn"])
    )
    path = tmp_path_factory.mktemp("data") / "telco_sample.csv"
    sample.to_csv(path, index=False)
    return path


@pytest.fixture(scope="module")
def trained_bundle(sample_csv, tmp_path_factory):
    model_path = tmp_path_factory.mktemp("models") / "churn_model.joblib"
    train_churn(sample_csv, model_path)
    return model_path


def test_load_churn_data_cleans_total_charges():
    X, y = load_churn_data()
    assert X["TotalCharges"].dtype.kind == "f"      # coerced to numeric
    assert not X["TotalCharges"].isna().any()       # blanks imputed
    assert set(y.unique()) <= {0, 1}
    assert list(X.columns) == NUMERIC + CATEGORICAL


def test_pipeline_probabilities_are_valid(sample_csv):
    X, y = load_churn_data(sample_csv)
    model = build_churn_pipeline()
    model.fit(X, y)
    proba = model.predict_proba(X)[:, 1]
    assert proba.min() >= 0.0 and proba.max() <= 1.0


def test_saved_bundle_roundtrip(trained_bundle):
    model, threshold = load_churn_model(trained_bundle)
    assert threshold == CHURN_THRESHOLD
    assert 0.0 < threshold < 1.0
    p = churn_probability(model, HIGH_RISK)
    assert 0.0 <= p <= 1.0


def test_risk_ordering_makes_sense(trained_bundle):
    """A short-tenure month-to-month customer must score above a loyal two-year one."""
    model, _ = load_churn_model(trained_bundle)
    assert churn_probability(model, HIGH_RISK) > churn_probability(model, LOW_RISK)


def test_unseen_category_does_not_crash(trained_bundle):
    """handle_unknown="ignore" keeps serving even if a new category value appears."""
    model, _ = load_churn_model(trained_bundle)
    odd = dict(HIGH_RISK, PaymentMethod="Crypto wallet")
    assert 0.0 <= churn_probability(model, odd) <= 1.0
