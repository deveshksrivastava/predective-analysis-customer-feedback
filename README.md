# Customer Feedback Sentiment Analysis — End-to-End ML Project

Classify customer feedback as **positive / negative / neutral**, served as a live web app.
This project covers the **full ML lifecycle**: dataset creation → exploration → cleaning →
TF-IDF features → training & comparing 4 models → honest evaluation with cross-validation →
hyperparameter tuning → a FastAPI prediction API with a web frontend → automated CI/CD
deployment to Azure App Service.

> 🔗 **Live demo:** https://feedback-sentiment-api.azurewebsites.net/ — type any feedback
> sentence and get the predicted sentiment with a confidence score.
> *(Prototype hosting — the first request after a deploy may take a few seconds while the
> model trains on startup.)*

Phase 1 (sentiment analysis) is complete. Phase 2 (customer churn prediction) is planned —
see [`PROJECT_SETUP.md`](PROJECT_SETUP.md) for the full plan and decision log.

---

## Architecture

```
data/feedback_sample.csv (149 labeled rows)
        │
        ▼
src/train.py ──► TF-IDF + tuned Multinomial Naive Bayes (scikit-learn Pipeline)
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
- **No data leakage.** TF-IDF is fit inside the pipeline on training folds only.
- **Self-training deploys.** The model artifact is gitignored; a fresh server trains it on
  startup in seconds (149 rows), so no binary ships through git or CI.

## Results

Evaluated with **5-fold cross-validation, macro-F1** (a single 25% test split proved far too
noisy at this data size — see the lessons below):

| Model | CV macro-F1 |
|-------|------------:|
| **Multinomial Naive Bayes (tuned: `alpha=0.1`, unigrams, English stopwords)** | **~0.74** |
| Logistic Regression | ~0.72 |
| Linear SVC | ~0.72 |
| Multinomial Naive Bayes (untuned) | ~0.71 |
| Random Forest | ~0.59 |

Sample predictions from the saved model:

| Feedback | Prediction | Confidence |
|----------|-----------|-----------:|
| "Absolutely love this, it works perfectly and support was great!" | positive | 97% |
| "The item arrived broken and no one will respond to my emails." | negative | 79% |
| "The package was delivered on Tuesday as scheduled." | neutral | 91% |

**Honest headline:** ~0.74 macro-F1 on 149 rows is a *learning-scale* result, not production
quality. The full step-by-step analysis lives in
[`docs/phase1_walkthrough.md`](docs/phase1_walkthrough.md).

### What building this actually taught me

1. **Explore before modelling.** Basic EDA caught a missing label and a duplicate row before
   they polluted training.
2. **Trust the right ruler.** On one small 38-row test split the models scored ~0.47–0.61 and
   looked broken. 5-fold cross-validation revealed their true level (~0.72) — the "bad
   models" were mostly measurement noise.
3. **Data beats tuning at this scale.** A full `GridSearchCV` over TF-IDF settings and NB
   smoothing bought only ~+0.03 F1. The real bottleneck is 149 rows of data, not
   hyperparameters.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.app:app --reload        # open http://127.0.0.1:8000
```

The model trains automatically on first startup. To regenerate it explicitly:

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

Explore the original research notebook:

```bash
jupyter notebook notebooks/01_sentiment_prototype.ipynb
```

## Project structure

```
data/       feedback_sample.csv — 149 labeled rows (text, sentiment)
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

1. **Real data at scale.** Replace the 149-row sample with thousands of real reviews
   (e.g. a public Amazon/Yelp dataset); this is the single biggest accuracy lever.
2. **Stronger baselines.** Benchmark a fine-tuned transformer (e.g. DistilBERT) and an LLM
   zero-shot classifier against the TF-IDF models on the same CV protocol.
3. **Experiment tracking & model registry.** MLflow for runs, params, metrics, and versioned
   model artifacts instead of a single joblib file.
4. **Serving hardening.** Request logging, rate limiting, auth, input-size limits, structured
   error handling, and probability calibration (Naive Bayes confidences are over-confident).
5. **Monitoring.** Log predictions, track class-distribution drift and confidence drift,
   alert on degradation, and build a labeled-feedback loop for retraining.
6. **Phase 2 — churn prediction.** Binary classifier on structured customer data, using
   Phase 1 sentiment as an input feature (planned in `PROJECT_SETUP.md`).
