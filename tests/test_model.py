"""Tests for src.model: pipeline build, save/load, and prediction.

We train on a tiny hand-made dataset so the tests are fast and deterministic.
We assert *invariants* (valid labels, probabilities sum to 1, round-trip equality)
rather than exact predicted labels, which would be flaky on so little data.
"""

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

from src.model import build_pipeline, load_model, predict_sentiment, save_model
from src.preprocessing import clean_text

# Tiny, clearly-separated training set (distinct content words per class).
TRAIN = [
    ("love this product amazing wonderful", "positive"),
    ("excellent fantastic service brilliant", "positive"),
    ("great quality delighted happy", "positive"),
    ("perfect experience superb recommend", "positive"),
    ("terrible product broke useless", "negative"),
    ("awful horrible service disappointing", "negative"),
    ("worst quality defective refund", "negative"),
    ("hate this nightmare frustrating", "negative"),
    ("product arrived tuesday scheduled delivery", "neutral"),
    ("order confirmed email received account", "neutral"),
    ("package delivered afternoon standard shipping", "neutral"),
    ("subscription renews monthly billing date", "neutral"),
]

LABELS = ["negative", "neutral", "positive"]


@pytest.fixture
def trained():
    """Return (model, label_encoder) trained on the tiny dataset."""
    texts = [clean_text(t) for t, _ in TRAIN]
    le = LabelEncoder()
    y = le.fit_transform([label for _, label in TRAIN])
    model = build_pipeline()
    model.fit(texts, y)
    return model, le


def test_build_pipeline_has_tfidf_and_clf():
    pipe = build_pipeline()
    assert list(pipe.named_steps) == ["tfidf", "clf"]


def test_build_pipeline_accepts_custom_classifier():
    pipe = build_pipeline(LogisticRegression())
    assert isinstance(pipe.named_steps["clf"], LogisticRegression)


def test_predict_returns_valid_labels(trained):
    model, le = trained
    preds = predict_sentiment(model, le, [
        "I absolutely love it, amazing quality!",
        "Broke immediately, terrible and useless.",
        "The order was delivered on the scheduled date.",
    ])
    assert len(preds) == 3
    assert all(p in LABELS for p in preds)


def test_predict_handles_empty_list(trained):
    model, le = trained
    assert predict_sentiment(model, le, []) == []


def test_probabilities_sum_to_one(trained):
    model, le = trained
    proba = model.predict_proba([clean_text("love this amazing product")])
    assert proba.shape == (1, len(LABELS))
    assert np.isclose(proba.sum(), 1.0)


def test_save_load_roundtrip_gives_identical_predictions(trained, tmp_path):
    model, le = trained
    path = save_model(model, le, tmp_path / "models" / "m.joblib")
    assert path.exists()

    reloaded_model, reloaded_le = load_model(path)
    samples = ["fantastic and excellent", "worst defective refund", "delivered on tuesday"]
    before = predict_sentiment(model, le, samples)
    after = predict_sentiment(reloaded_model, reloaded_le, samples)
    assert before == after


def test_positive_and_negative_are_distinguished(trained):
    # A soft sanity check: an obviously positive vs obviously negative sentence
    # should not receive the same label. (Structural, not asserting which is which.)
    model, le = trained
    pos, neg = predict_sentiment(model, le, [
        "love it, amazing, excellent, wonderful, fantastic",
        "hate it, awful, terrible, horrible, worst, useless",
    ])
    assert pos != neg
