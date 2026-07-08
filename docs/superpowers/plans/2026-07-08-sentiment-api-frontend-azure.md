# Sentiment API + Frontend + Azure Deployment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the completed Phase 1 notebook into deployable Python (training script + FastAPI prediction API), add a minimal web frontend that sends feedback text to the server and shows whether the sentiment is positive, and document how to deploy the whole thing to Azure App Service.

**Architecture:** The notebook's reusable logic already lives in `src/preprocessing.py` and `src/model.py` (with 15 passing tests). We add three thin layers on top: `src/train.py` (reproduces notebook Steps 1–11 as one script that writes `models/sentiment_model.joblib`), `src/app.py` (FastAPI app that loads the model — training it on startup if the artifact is missing — and exposes `POST /predict` + `GET /health`), and `static/index.html` (a single plain-HTML/JS page served by the same FastAPI app, so there is exactly one deployable and no CORS setup). Azure deployment is one App Service (Linux, Python) started with gunicorn/uvicorn.

**Tech Stack:** Python 3.13, scikit-learn, joblib, FastAPI, uvicorn, gunicorn, plain HTML + fetch() (no JS framework), pytest + httpx (FastAPI TestClient), Azure App Service via `az webapp up`.

## Global Constraints

- This is a **learning prototype**: keep every file simple and readable; no production hardening beyond what the tasks specify.
- **Do not start coding until the user explicitly says "go"** (project working agreement).
- Reuse `src/preprocessing.clean_text` and `src/model.build_pipeline/save_model/load_model/predict_sentiment` — do not duplicate their logic.
- Keep `models/` gitignored (regenerable artifact); the API must self-train if the artifact is missing.
- Data file: `data/feedback_sample.csv` with columns `text`, `sentiment` (149 clean rows).
- Notebook stays untouched — it remains the Phase 1 learning record.
- All commands run inside the project venv: `source .venv/bin/activate`.
- Tests must keep passing: `python -m pytest` (15 existing tests + new ones).

## Approaches considered (decisions locked in)

| Decision | Chosen | Alternatives rejected |
|----------|--------|----------------------|
| Serving framework | **FastAPI** — matches the long-term stack in PROJECT_SETUP.md §1, auto-generates `/docs`, trivial JSON validation | Flask (no typed validation, not in target stack); Azure ML managed endpoint (heavyweight for a prototype) |
| Frontend | **Single static HTML+JS page served by FastAPI** — one deployable, no CORS, no build toolchain | React (build tooling overkill for one form); Streamlit (second server process to deploy) |
| Model artifact on Azure | **Train on startup if `models/sentiment_model.joblib` is missing** — dataset is tiny (149 rows, trains in seconds), keeps `models/` gitignored | Committing the binary artifact (binary diffs in git); Azure Blob Storage (extra service to learn later) |
| Azure compute | **App Service (Linux, Python) via `az webapp up`** — simplest path from repo to URL | Container Apps (requires Dockerfile + registry); Functions (cold-start + awkward for serving a loaded model); Azure ML endpoints (Phase-later) |

---

### Task 1: Training script `src/train.py`

Reproduces the notebook's final training recipe (tuned Naive Bayes pipeline refit on all data, Step 10–11) as a callable function + CLI, so the model artifact can be regenerated anywhere (locally, CI, Azure startup).

**Files:**
- Create: `src/train.py`
- Test: `tests/test_train.py`
- Modify: none

**Interfaces:**
- Consumes: `src.preprocessing.clean_text(text: str) -> str`; `src.model.build_pipeline() -> Pipeline`; `src.model.save_model(model, label_encoder, path) -> Path`; `src.model.load_model(path) -> (model, label_encoder)`
- Produces: `train(data_path="data/feedback_sample.csv", model_path="models/sentiment_model.joblib") -> Path` — loads the CSV, drops missing labels/duplicates, cleans text, label-encodes, fits the default (tuned NB) pipeline on **all** rows, saves the bundle, returns the saved path. Also runnable as `python -m src.train`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_train.py
"""train() should produce a loadable model bundle that predicts sensible labels."""

from src.model import load_model, predict_sentiment
from src.train import train


def test_train_creates_loadable_model(tmp_path):
    model_path = tmp_path / "sentiment_model.joblib"

    saved = train(model_path=model_path)

    assert saved == model_path
    assert model_path.exists()

    model, label_encoder = load_model(model_path)
    preds = predict_sentiment(model, label_encoder, ["I love this product!"])
    assert preds[0] in {"positive", "negative", "neutral"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_train.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.train'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/train.py
"""Train the Phase 1 sentiment model outside the notebook.

Reproduces notebook Steps 1-11 end state: load the CSV, clean it, fit the
tuned Naive Bayes pipeline on ALL rows (final refit), and save the bundle
with joblib so the API can load it.
"""

from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder

from .model import build_pipeline, save_model
from .preprocessing import clean_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = PROJECT_ROOT / "data" / "feedback_sample.csv"
DEFAULT_MODEL = PROJECT_ROOT / "models" / "sentiment_model.joblib"


def train(data_path=DEFAULT_DATA, model_path=DEFAULT_MODEL) -> Path:
    """Fit the tuned pipeline on the full dataset and save it. Returns the path."""
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["text", "sentiment"]).drop_duplicates()

    texts = df["text"].map(clean_text)
    label_encoder = LabelEncoder()
    labels = label_encoder.fit_transform(df["sentiment"])

    model = build_pipeline()          # tuned NB: unigrams + English stopwords, alpha=0.1
    model.fit(texts, labels)

    return save_model(model, label_encoder, model_path)


if __name__ == "__main__":
    path = train()
    print(f"Model saved to {path}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_train.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Run the full suite + the CLI once**

Run: `python -m pytest && python -m src.train`
Expected: all tests pass; prints `Model saved to .../models/sentiment_model.joblib`

- [ ] **Step 6: Commit**

```bash
git add src/train.py tests/test_train.py
git commit -m "feat: add train.py to regenerate the sentiment model outside the notebook"
```

---

### Task 2: FastAPI prediction API `src/app.py`

One small app: health check + predict endpoint. Loads the joblib bundle at startup; if the artifact is missing (fresh clone, fresh Azure instance) it calls `train()` — the dataset is tiny so this takes seconds.

**Files:**
- Create: `src/app.py`
- Test: `tests/test_app.py`
- Modify: `requirements.txt` (add web/serving deps)

**Interfaces:**
- Consumes: `src.train.train(model_path=...) -> Path`; `src.model.load_model(path)`; `src.model.predict_sentiment(model, label_encoder, texts) -> list[str]`
- Produces: FastAPI instance named `app` in `src.app` (gunicorn target `src.app:app`). `GET /health` → `{"status": "ok"}`. `POST /predict` with body `{"text": "..."}` → `{"sentiment": "positive|negative|neutral", "is_positive": bool, "confidence": float}`. Empty/whitespace text → HTTP 422.

- [ ] **Step 1: Add serving dependencies**

Append to `requirements.txt`:

```
# Serving (Phase 1 deployment)
fastapi
uvicorn
gunicorn
httpx
```

Run: `pip install -r requirements.txt`
Expected: installs cleanly (httpx is needed by FastAPI's TestClient).

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_app.py
"""API contract: /health, /predict happy path, /predict validation."""

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_predict_positive_text():
    resp = client.post("/predict", json={"text": "Absolutely love it, works great!"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sentiment"] in {"positive", "negative", "neutral"}
    assert body["is_positive"] == (body["sentiment"] == "positive")
    assert 0.0 <= body["confidence"] <= 1.0


def test_predict_rejects_blank_text():
    resp = client.post("/predict", json={"text": "   "})
    assert resp.status_code == 422
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_app.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.app'`

- [ ] **Step 4: Write minimal implementation**

```python
# src/app.py
"""FastAPI app serving the Phase 1 sentiment model.

Run locally:  uvicorn src.app:app --reload
On Azure:     gunicorn -w 2 -k uvicorn.workers.UvicornWorker src.app:app
"""

from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from .model import load_model
from .preprocessing import clean_text
from .train import DEFAULT_MODEL, PROJECT_ROOT, train

_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DEFAULT_MODEL.exists():          # fresh clone / fresh Azure instance
        train()
    _state["model"], _state["label_encoder"] = load_model(DEFAULT_MODEL)
    yield
    _state.clear()


app = FastAPI(title="Customer Feedback Sentiment API", lifespan=lifespan)


class FeedbackIn(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank")
        return v


class PredictionOut(BaseModel):
    sentiment: str
    is_positive: bool
    confidence: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionOut)
def predict(feedback: FeedbackIn):
    model, label_encoder = _state["model"], _state["label_encoder"]
    cleaned = clean_text(feedback.text)
    probs = model.predict_proba([cleaned])[0]
    best = int(np.argmax(probs))
    sentiment = label_encoder.inverse_transform([best])[0]
    return PredictionOut(
        sentiment=sentiment,
        is_positive=(sentiment == "positive"),
        confidence=float(probs[best]),
    )
```

Note: we use `predict_proba` directly (instead of `predict_sentiment`) because the frontend wants a confidence score; `clean_text` keeps preprocessing identical to training.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_app.py -v`
Expected: PASS (3 tests). First run may take a few extra seconds if it trains the model.

- [ ] **Step 6: Smoke-test the live server**

Run: `uvicorn src.app:app --port 8000 &` then
`curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' -d '{"text": "great product"}'`
Expected: JSON like `{"sentiment":"positive","is_positive":true,"confidence":0.9...}`. Stop the server afterwards.

- [ ] **Step 7: Commit**

```bash
git add src/app.py tests/test_app.py requirements.txt
git commit -m "feat: add FastAPI sentiment prediction API (/health, /predict)"
```

---

### Task 3: Frontend `static/index.html`

One self-contained page (inline CSS + JS, no framework, no build step): textarea → "Analyze" button → calls `POST /predict` with `fetch()` → shows a large color-coded verdict (green POSITIVE ✓ / red NEGATIVE ✗ / gray NEUTRAL) plus the confidence. Served by the same FastAPI app at `/`.

**Files:**
- Create: `static/index.html`
- Modify: `src/app.py` (mount static dir — one line, shown below)
- Test: `tests/test_app.py` (add one test)

**Interfaces:**
- Consumes: `POST /predict` contract from Task 2 (`{"text"}` → `{"sentiment", "is_positive", "confidence"}`).
- Produces: `GET /` returns the HTML page (StaticFiles mount with `html=True`).

- [ ] **Step 1: Write the failing test** (append to `tests/test_app.py`)

```python
def test_root_serves_frontend():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Sentiment" in resp.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_app.py::test_root_serves_frontend -v`
Expected: FAIL with 404

- [ ] **Step 3: Create the page**

```html
<!-- static/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Feedback Sentiment Checker</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 40rem; margin: 4rem auto; padding: 0 1rem; }
    textarea { width: 100%; min-height: 6rem; font: inherit; padding: .5rem; }
    button { font: inherit; padding: .5rem 1.5rem; margin-top: .5rem; cursor: pointer; }
    #result { margin-top: 1.5rem; font-size: 1.5rem; font-weight: bold; }
    .positive { color: #1a7f37; }
    .negative { color: #cf222e; }
    .neutral  { color: #57606a; }
    .error    { color: #cf222e; font-size: 1rem; font-weight: normal; }
  </style>
</head>
<body>
  <h1>Feedback Sentiment Checker</h1>
  <p>Paste customer feedback and check whether it is positive.</p>
  <textarea id="feedback" placeholder="e.g. The product arrived quickly and works perfectly!"></textarea>
  <br>
  <button id="analyze">Analyze</button>
  <div id="result"></div>

  <script>
    const result = document.getElementById("result");
    document.getElementById("analyze").addEventListener("click", async () => {
      const text = document.getElementById("feedback").value;
      result.textContent = "Analyzing…";
      result.className = "";
      try {
        const resp = await fetch("/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
        if (!resp.ok) throw new Error((await resp.json()).detail?.[0]?.msg || resp.statusText);
        const data = await resp.json();
        const pct = (data.confidence * 100).toFixed(0);
        const mark = data.is_positive ? "✓ POSITIVE" : data.sentiment === "negative" ? "✗ NEGATIVE" : "– NEUTRAL";
        result.textContent = `${mark} (${pct}% confident)`;
        result.className = data.sentiment;
      } catch (err) {
        result.textContent = `Error: ${err.message}`;
        result.className = "error";
      }
    });
  </script>
</body>
</html>
```

- [ ] **Step 4: Mount it in the app** (append as the LAST route registration in `src/app.py`, after the `/predict` handler, so API routes win)

```python
app.mount("/", StaticFiles(directory=PROJECT_ROOT / "static", html=True), name="static")
```

(`StaticFiles` and `PROJECT_ROOT` are already imported in Task 2's `src/app.py`.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest -v`
Expected: full suite passes (existing 15 + Task 1's 1 + Task 2's 3 + this 1 = 20).

- [ ] **Step 6: Try it in a browser**

Run: `uvicorn src.app:app --port 8000`, open `http://localhost:8000/`, submit one clearly positive and one clearly negative sentence.
Expected: green "✓ POSITIVE (…% confident)" and red "✗ NEGATIVE (…)" respectively. Stop the server.

- [ ] **Step 7: Commit**

```bash
git add static/index.html src/app.py tests/test_app.py
git commit -m "feat: add single-page frontend for sentiment checks"
```

---

### Task 4: Azure deployment files + docs

No new app code — just what Azure App Service needs (a startup command) and a short runbook. `az webapp up` zips the working directory, installs `requirements.txt` via Oryx, and runs the startup command; the model artifact is NOT shipped (gitignored) and gets trained on first startup by Task 2's lifespan hook.

**Files:**
- Create: `docs/DEPLOYMENT.md`
- Modify: `PROJECT_SETUP.md` (decision-log rows)

**Interfaces:**
- Consumes: `src.app:app` gunicorn target from Task 2.
- Produces: a documented, repeatable deploy procedure; no code contracts.

- [ ] **Step 1: Write `docs/DEPLOYMENT.md`**

```markdown
# Deploying the Sentiment API to Azure App Service

One App Service (Linux, Python) serves both the API and the frontend.

## Prerequisites
- Azure CLI (`brew install azure-cli`), logged in: `az login`
- An Azure subscription

## First deploy

    cd <repo root>
    az webapp up \
      --name feedback-sentiment-api \        # must be globally unique — change it
      --resource-group rg-feedback-prototype \
      --location <nearest-region> \
      --sku B1 \
      --runtime "PYTHON:3.12"

Then set the startup command (once):

    az webapp config set \
      --name feedback-sentiment-api \
      --resource-group rg-feedback-prototype \
      --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker src.app:app"

## Verify

    curl https://feedback-sentiment-api.azurewebsites.net/health
    # → {"status":"ok"}

Open `https://feedback-sentiment-api.azurewebsites.net/` for the frontend.
First request after a deploy may be slow: the app trains the model
(seconds — the dataset is 149 rows) because `models/` is not shipped.

## Redeploy after changes

    az webapp up --name feedback-sentiment-api --resource-group rg-feedback-prototype

## Tear down (stops billing)

    az group delete --name rg-feedback-prototype

## Notes
- Runtime is `PYTHON:3.12` because App Service may lag behind local 3.13;
  check `az webapp list-runtimes --os linux | grep -i python` and use the
  newest available.
- `jupyter`, `matplotlib`, `seaborn`, `xgboost` in requirements.txt are
  dev/notebook-only; fine for a prototype, trim into a separate
  `requirements-dev.txt` later if deploys feel slow.
```

- [ ] **Step 2: Add decision-log rows to `PROJECT_SETUP.md` §6**

| Date | Decision / Question | Outcome |
|------|--------------------|---------|
| 2026-07-08 | Deployment shape | FastAPI app (`src/app.py`) + static HTML frontend, single Azure App Service; model self-trains on startup since `models/` is gitignored |
| 2026-07-08 | Frontend | Plain HTML+JS page served by FastAPI at `/` — no framework, no CORS |

- [ ] **Step 3: Commit**

```bash
git add docs/DEPLOYMENT.md PROJECT_SETUP.md
git commit -m "docs: add Azure App Service deployment runbook"
```

- [ ] **Step 4 (with the user, when they're ready): run the actual deploy**

Requires `az login` (interactive) and a subscription choice — done together with the user, following `docs/DEPLOYMENT.md`. Verify `/health` and the frontend on the live URL.

---

## Out of scope (YAGNI — revisit only if asked)

- Authentication, rate limiting, HTTPS config (App Service gives HTTPS by default)
- CI/CD pipeline (GitHub Actions) — manual `az webapp up` is enough for a prototype
- Docker/Container Apps, Azure ML endpoints, Blob Storage for the model
- Batch prediction endpoint, logging/monitoring dashboards
- Phase 2 (churn) — untouched
