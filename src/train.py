"""Train the Phase 1 sentiment model outside the notebook.

Loads the real dataset (30k Amazon product reviews, balanced across
negative/neutral/positive), cleans it, fits the winning pipeline on ALL rows
(final refit), and saves the bundle with joblib so the API can load it.
"""

from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder

from .model import build_pipeline, save_model
from .preprocessing import clean_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = PROJECT_ROOT / "data" / "feedback_reviews.csv"
DEFAULT_MODEL = PROJECT_ROOT / "models" / "sentiment_model.joblib"


def train(data_path=DEFAULT_DATA, model_path=DEFAULT_MODEL) -> Path:
    """Fit the tuned pipeline on the full dataset and save it. Returns the path."""
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["text", "sentiment"]).drop_duplicates()

    texts = df["text"].map(clean_text)
    label_encoder = LabelEncoder()
    labels = label_encoder.fit_transform(df["sentiment"])

    model = build_pipeline()          # LogReg (balanced): unigrams, stopwords kept
    model.fit(texts, labels)

    return save_model(model, label_encoder, model_path)


if __name__ == "__main__":
    path = train()
    print(f"Model saved to {path}")
