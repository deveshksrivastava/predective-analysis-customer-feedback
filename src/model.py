"""Model helpers for the sentiment pipeline.

Refactored from Steps 6, 10 and 11 of ``notebooks/01_sentiment_prototype.ipynb``:
build the swappable TF-IDF -> classifier pipeline, save/load it with joblib, and
predict sentiment on raw feedback text.
"""

from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from .preprocessing import clean_text


def build_pipeline(classifier=None, **tfidf_kwargs) -> Pipeline:
    """TF-IDF -> classifier. Same recipe for every model, so they stay swappable.

    Defaults to the Phase 1 winner (tuned Naive Bayes, unigram + English stopwords).
    Pass a different ``classifier`` and/or TF-IDF keyword args to compare others.
    """
    if classifier is None:
        classifier = MultinomialNB(alpha=0.1)
    tfidf_kwargs.setdefault("stop_words", "english")
    return Pipeline([
        ("tfidf", TfidfVectorizer(**tfidf_kwargs)),
        ("clf", classifier),
    ])


def save_model(model, label_encoder, path) -> Path:
    """Persist the fitted pipeline together with its label encoder."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "label_encoder": label_encoder}, path)
    return path


def load_model(path):
    """Load a bundle saved by :func:`save_model`. Returns ``(model, label_encoder)``."""
    bundle = joblib.load(path)
    return bundle["model"], bundle["label_encoder"]


def predict_sentiment(model, label_encoder, texts):
    """Predict sentiment labels for raw (uncleaned) feedback strings.

    Cleans each text the same way as training, predicts, and maps the integer
    codes back to label strings (e.g. ``"positive"``). Returns a list of strings.
    """
    cleaned = [clean_text(t) for t in texts]
    if not cleaned:                       # nothing to predict; avoid an empty-transform error
        return []
    codes = model.predict(cleaned)
    return list(label_encoder.inverse_transform(codes))
