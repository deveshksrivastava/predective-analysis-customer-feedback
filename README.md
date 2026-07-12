# Customer Feedback Sentiment Analysis — End-to-End ML Project

Classify customer feedback as **positive / negative / neutral**, served as a live web app.
This project covers the **full ML lifecycle**: data at two scales (a hand-built sample for
learning the mechanics, then **30,000 real Amazon product reviews**) → exploration →
cleaning → TF-IDF features → training & comparing 4 models → honest held-out evaluation →
a FastAPI prediction API with a web frontend → automated CI/CD deployment to Azure App
Service.

> 🔗 **Live demo:** https://feedback-sentiment-api.azurewebsites.net/ — type any feedback
> sentence and get the predicted sentiment with a confidence score.
> *(Prototype hosting — the first request after a deploy may take a few seconds while the
> model trains on startup.)*

Phase 1 (sentiment analysis) is complete. Phase 2 (customer churn prediction) is planned —
see [`PROJECT_SETUP.md`](PROJECT_SETUP.md) for the full plan and decision log.

---

## Data

| Dataset | Rows | What it is |
|---------|-----:|------------|
| `data/feedback_reviews.csv` | **30,000** | Real Amazon product reviews (English subset of the multilingual Amazon reviews corpus, Apache-2.0), balanced 10k per class. Star ratings mapped to sentiment: 1–2★ → negative, 3★ → neutral, 4–5★ → positive. **This is what the deployed model trains on.** |
| `data/feedback_sample.csv` | 149 | The original hand-built sample used to learn the pipeline mechanics in the notebook. Kept as project history. |

Scaling from 149 synthetic rows to 30k real, messy reviews changed the conclusions — see
the lessons below.

## Architecture

```
data/feedback_reviews.csv (30k labeled Amazon reviews)
        │
        ▼
src/train.py ──► TF-IDF + Logistic Regression (scikit-learn Pipeline)
        │            └── models/sentiment_model.joblib  (regenerated, not committed)
        ▼
src/app.py (FastAPI)
   ├── GET  /health              liveness check
   ├── POST /predict             {"text": ...} → {"sentiment", "is_positive", "confidence"}
   └── GET  /                    static/index.html — single-page frontend
        │
        ▼
GitHub Actions (.github/workflows/deploy.yml)
   push to master ──► pytest gate ──► deploy to Azure App Service (Linux, gunicorn+uvicorn)
```

Design choices worth noting:

- **Swappable models.** Every classifier is wrapped in the same `Pipeline([TF-IDF, clf])`
  interface, so models are compared apples-to-apples and swapping one is a one-line change.
- **No data leakage.** TF-IDF is fit inside the pipeline on training data only.
- **Self-training deploys.** The model artifact is gitignored; a fresh server trains it on
  startup (~5 s on 30k reviews), so no binary ships through git or CI.
- **Negations are kept.** TF-IDF does *not* strip English stopwords — "no"/"not" are
  stopwords, and removing them measurably hurt sentiment accuracy (see lessons).

## Results

Evaluated on a **held-out test set of 6,000 reviews** (stratified 80/20 split):

| Model | Accuracy | Macro-F1 |
|-------|---------:|---------:|
| **Logistic Regression (`class_weight="balanced"`, stopwords kept)** | **0.649** | **0.650** |
| Logistic Regression (stopwords stripped) | 0.617 | 0.615 |
| Linear SVC | 0.591 | 0.588 |
| Random Forest | 0.593 | 0.585 |
| Multinomial Naive Bayes (`alpha=0.1`) | 0.577 | 0.578 |

Per-class (winner): negative **0.677** F1, neutral **0.540**, positive **0.733**. Neutral is
by far the hardest class — 3-star reviews are genuinely mixed ("good but…") even for humans.

Sample predictions from the deployed model:

| Feedback | Prediction | Confidence |
|----------|-----------|-----------:|
| "Absolutely love this, it works perfectly and support was great!" | positive | 100% |
| "The item arrived broken and no one will respond to my emails." | negative | 81% |
| "It is fine, does the job but nothing special." | neutral | 73% |
| "The package was delivered on Tuesday as scheduled." | negative (wrong — should be neutral) | 46% |

That last row is left in deliberately: delivery-focused reviews skew negative in the
training data, so purely factual logistics statements get pulled toward negative — a known
failure mode, at low confidence. Full analysis in
[`docs/phase1_walkthrough.md`](docs/phase1_walkthrough.md).

### What building this actually taught me

1. **Explore before modelling.** Basic EDA on the first sample caught a missing label and a
   duplicate row before they polluted training.
2. **Trust the right ruler.** At 149 rows, a single 38-row test split made the models look
   broken (~0.47–0.61 F1); 5-fold cross-validation revealed their true level. At 30k rows,
   a 6,000-review held-out set is statistically sound on its own.
3. **Small-data winners don't survive scale.** Tuned Naive Bayes won on 149 rows (~0.74 CV
   macro-F1) — on 30k real reviews it came **last**, and Logistic Regression won. Model
   rankings are dataset-dependent; re-benchmark when the data changes.
4. **Domain match matters.** A first attempt used 60k labeled tweets: benchmark scores
   looked fine, but the model called *"The item arrived broken and no one will respond to my
   emails"* **neutral** — tweet negativity (politics, insults) doesn't transfer to product
   complaints. Switching to Amazon reviews fixed it.
5. **Don't strip negations.** Removing English stopwords deletes "no"/"not" and cost
   0.035 macro-F1. Preprocessing defaults are not free.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.app:app --reload        # open http://127.0.0.1:8000
```

The model trains automatically on first startup (~5 s). To regenerate it explicitly:

```bash
python -m src.train
```

Try the API directly:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Support was quick and the product works great"}'
# → {"sentiment":"positive","is_positive":true,"confidence":0.9...}
```

Interactive API docs (FastAPI auto-generated): http://127.0.0.1:8000/docs

Run the tests:

```bash
pytest
```

Explore the original research notebook (built on the 149-row sample):

```bash
jupyter notebook notebooks/01_sentiment_prototype.ipynb
```

## Project structure

```
data/       feedback_reviews.csv — 30k labeled Amazon reviews (training data)
            feedback_sample.csv — original 149-row learning sample
notebooks/  01_sentiment_prototype.ipynb — the full Phase 1 research pipeline
src/        preprocessing.py, model.py, train.py, app.py — refactored production code
static/     index.html — single-page frontend served by the API
tests/      pytest suite for preprocessing and model code
docs/       phase1_walkthrough.md (step-by-step write-up), DEPLOYMENT.md (Azure runbook)
.github/    workflows/deploy.yml — test-gated deploy to Azure on push to master
```

## Tech stack

Python · pandas · scikit-learn · FastAPI · uvicorn/gunicorn · pytest · joblib ·
GitHub Actions · Azure App Service · Jupyter/matplotlib/seaborn (research)

## Roadmap to production

This is deliberately a prototype. The gaps I'd close to make it production-grade, roughly in
order of impact:

1. **Stronger baselines.** ~0.65 macro-F1 is a solid linear-model result on 3-class reviews,
   but a fine-tuned transformer (e.g. DistilBERT) or an LLM zero-shot classifier should beat
   it — benchmark them on the same held-out protocol.
2. **Better neutral handling.** Neutral F1 (0.54) drags the average; options include
   ordinal-aware labeling from star ratings, more granular classes, or calibrated abstention
   on low-confidence predictions.
3. **Experiment tracking & model registry.** MLflow for runs, params, metrics, and versioned
   model artifacts instead of a single joblib file.
4. **Serving hardening.** Request logging, rate limiting, auth, input-size limits, structured
   error handling, and probability calibration.
5. **Monitoring.** Log predictions, track class-distribution drift and confidence drift,
   alert on degradation, and build a labeled-feedback loop for retraining.
6. **Phase 2 — churn prediction.** Binary classifier on structured customer data, using
   Phase 1 sentiment as an input feature (planned in `PROJECT_SETUP.md`).
