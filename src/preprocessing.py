"""Text preprocessing for the sentiment pipeline.

Refactored from Step 3 of ``notebooks/01_sentiment_prototype.ipynb`` so it can be
imported and tested. Keep this identical to what the notebook uses, so training and
inference clean text the same way (no train/serve skew).
"""

import re


def clean_text(text: str) -> str:
    """Normalise a feedback string for TF-IDF.

    Steps (same as the notebook):
      1. lowercase
      2. remove punctuation / symbols (keep letters, digits, spaces)
      3. collapse repeated whitespace and trim the ends
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
