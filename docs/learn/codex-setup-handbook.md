# Codex Setup and Project Handbook

This handbook gives Codex and new developers enough context to work safely in this repository without first reverse-engineering every file. It combines local setup instructions, the current architecture, project rules, verification commands, and known limitations.

All commands assume the current directory is the repository root:

```text
predective-analysis-customer-feedback/
```

## 1. Project purpose and current status

This repository is an end-to-end machine-learning prototype for customer feedback analysis.

The implemented feature is **Phase 1: sentiment analysis**. Given a customer feedback sentence, the system predicts one of three labels:

- `positive`
- `negative`
- `neutral`

Phase 1 includes the full learning-to-deployment path:

```text
Labeled CSV dataset
        ↓
Explore and clean the data
        ↓
Convert text to TF-IDF features
        ↓
Train and compare classifiers
        ↓
Tune and save the winning model
        ↓
Serve predictions through FastAPI
        ↓
Display results in a static web page
        ↓
Deploy to Azure through GitHub Actions
```

**Phase 1 is implemented.** The current model is a tuned Multinomial Naive Bayes classifier trained on 149 usable feedback rows.

**Phase 2 is planned but not implemented.** Its intended goal is customer churn prediction using structured customer data and, potentially, sentiment-derived features.

This is a learning prototype. It demonstrates sound ML structure and deployment mechanics, but its small dataset and lack of operational safeguards mean it must not be described as production-grade.

For the public project overview, read [README.md](../README.md). For the original scope and decision history, read [PROJECT_SETUP.md](../PROJECT_SETUP.md).

## 2. Source-of-truth hierarchy

When repository documents disagree, use this order:

1. Executable code and passing tests
2. Current root [README.md](../README.md)
3. Decision history in [PROJECT_SETUP.md](../PROJECT_SETUP.md)
4. Historical plans and walkthrough documents

Some older passages in `PROJECT_SETUP.md` and the Phase 1 walkthrough still describe refactoring or deployment as planned. The repository now contains `src/train.py`, `src/app.py`, the frontend, Azure deployment documentation, and GitHub Actions configuration, so those features are implemented.

## 3. Codex working rules

Codex should read these files before proposing or implementing changes:

1. [CLAUDE.md](../CLAUDE.md) for the repository working agreement
2. [PROJECT_SETUP.md](../PROJECT_SETUP.md) for scope and historical decisions
3. [README.md](../README.md) for the current showcase view
4. The relevant source files and tests for the requested change

Important working rules:

- Explain a development step before implementing it.
- Do not begin a new implementation step until the user explicitly approves it.
- Keep the project simple, readable, and suitable for learning.
- Preserve notebook-first reasoning when experimenting with new ML behavior.
- Refactor proven notebook logic into focused `src/*.py` modules.
- Do not begin Phase 2 until the user explicitly approves it.
- Avoid unrelated refactoring.
- Preserve user changes and unrelated untracked files.
- Use the project virtual environment for Python commands.
- Run relevant tests before claiming a change is complete.
- Treat cross-validation macro-F1, not hand-picked prediction confidence, as the honest model-performance headline.

### Starting a Codex session

Open Codex with this repository as the working directory. A useful first instruction is:

```text
Read CLAUDE.md, PROJECT_SETUP.md, README.md, and
.learn/readme-codex-setup.md before making changes. Explain the relevant
project context and wait for my explicit approval before implementation.
```

The repository currently uses `CLAUDE.md` as its checked-in assistant guidance. There is no root `AGENTS.md`. If an `AGENTS.md` is added later, Codex should treat it as additional repository instruction and resolve conflicts in favor of the most specific applicable instruction.

## 4. Architecture and data flow

The runtime architecture is intentionally small:

```text
data/feedback_sample.csv
          │
          ▼
src/train.py
  ├─ remove missing and duplicate rows
  ├─ clean feedback text
  ├─ encode sentiment labels
  ├─ fit TF-IDF + MultinomialNB
  └─ save models/sentiment_model.joblib
          │
          ▼
src/app.py
  ├─ train automatically if the model file is absent
  ├─ load the model into process memory
  ├─ GET /health
  ├─ POST /predict
  └─ mount static/index.html at /
          │
          ▼
Browser or API client
```

### Training flow

1. `src/train.py` reads `data/feedback_sample.csv` with pandas.
2. Rows missing `text` or `sentiment` are removed.
3. Duplicate rows are removed.
4. `src.preprocessing.clean_text()` normalizes every sentence.
5. `LabelEncoder` converts sentiment strings to integer class values.
6. `src.model.build_pipeline()` creates TF-IDF followed by the classifier.
7. The pipeline fits all 149 usable rows for the final deployable model.
8. The pipeline and label encoder are saved together with joblib.

### Prediction flow

1. FastAPI validates that submitted text is not blank.
2. The shared cleaning function normalizes the input.
3. The fitted pipeline produces a probability for each sentiment class.
4. The highest-probability class is converted back to its label string.
5. The API returns the label, a convenience `is_positive` flag, and confidence.

Using the same cleaning function in training and inference prevents train/serve skew.

## 5. Repository map

```text
.
├── data/
│   └── feedback_sample.csv
├── notebooks/
│   └── 01_sentiment_prototype.ipynb
├── src/
│   ├── preprocessing.py
│   ├── model.py
│   ├── train.py
│   └── app.py
├── static/
│   └── index.html
├── tests/
│   ├── test_preprocessing.py
│   └── test_model.py
├── docs/
│   ├── phase1_walkthrough.md
│   ├── DEPLOYMENT.md
│   └── superpowers/
├── .github/workflows/
│   └── deploy.yml
├── models/                 # generated and gitignored
├── .learn/                 # local learning material; gitignored
├── requirements.txt
├── CLAUDE.md
├── PROJECT_SETUP.md
└── README.md
```

### File responsibilities

| File | Responsibility |
|---|---|
| `data/feedback_sample.csv` | Small labeled sentiment dataset |
| `notebooks/01_sentiment_prototype.ipynb` | Original research and model comparison workflow |
| `src/preprocessing.py` | Shared text-cleaning function |
| `src/model.py` | Pipeline construction, persistence, and reusable prediction helpers |
| `src/train.py` | Reproducible training entry point outside Jupyter |
| `src/app.py` | FastAPI lifecycle, validation, health route, prediction route, and static mount |
| `static/index.html` | Framework-free browser interface |
| `tests/test_preprocessing.py` | Text-cleaning unit tests |
| `tests/test_model.py` | Pipeline, prediction, probability, and persistence tests |
| `.github/workflows/deploy.yml` | Test-gated Azure deployment workflow |
| `docs/phase1_walkthrough.md` | Plain-language account of the ML experiment |
| `docs/DEPLOYMENT.md` | Azure provisioning and deployment runbook |

## 6. Local environment setup

### Existing checkout

The repository currently contains a `.venv` virtual environment. Activate it with:

```bash
source .venv/bin/activate
```

Confirm the interpreter:

```bash
python --version
```

The existing local environment uses Python 3.13. Azure deployment uses Python 3.12 because supported App Service runtimes may lag behind local versions.

### Fresh checkout

Create and populate a new virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The requirements include research, testing, and serving packages in one file:

- pandas and scikit-learn
- matplotlib and seaborn
- joblib and Jupyter
- optional XGBoost experimentation
- pytest
- FastAPI, Uvicorn, Gunicorn, and HTTPX

Do not use the shell's unrelated system Python when working on this project. Prefer either an activated environment or explicit `.venv/bin/...` commands.

## 7. Common development commands

### Run all tests

```bash
.venv/bin/pytest -q
```

Current verified baseline:

```text
15 passed
```

Joblib may emit NumPy deprecation warnings. They currently originate in dependencies and do not represent failing project tests.

### Train or regenerate the model

```bash
.venv/bin/python -m src.train
```

Expected output ends with:

```text
Model saved to .../models/sentiment_model.joblib
```

The `models/` directory is gitignored because this artifact is reproducible from the source dataset.

### Run the application

```bash
.venv/bin/uvicorn src.app:app --reload
```

Open:

- Frontend: `http://127.0.0.1:8000/`
- Interactive API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

If the saved model does not exist, application startup trains it automatically.

### Open the research notebook

```bash
.venv/bin/jupyter notebook notebooks/01_sentiment_prototype.ipynb
```

Notebook paths are relative to `notebooks/`; for example, the dataset path is `../data/feedback_sample.csv`.

## 8. API contract

### Health endpoint

```http
GET /health
```

Response:

```json
{"status": "ok"}
```

### Prediction endpoint

```http
POST /predict
Content-Type: application/json
```

Request body:

```json
{"text": "Support was quick and the product works great"}
```

Response shape:

```json
{
  "sentiment": "positive",
  "is_positive": true,
  "confidence": 0.91
}
```

Try it locally:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"Support was quick and the product works great"}'
```

A blank or whitespace-only `text` value returns FastAPI validation status `422`.

## 9. Model design and evaluation

### Text normalization

`clean_text()`:

- lowercases text;
- removes punctuation and symbols;
- preserves letters, digits, and spaces;
- collapses repeated whitespace;
- trims leading and trailing whitespace.

### Features and classifier

The final scikit-learn pipeline uses:

```text
TfidfVectorizer(stop_words="english")
        ↓
MultinomialNB(alpha=0.1)
```

The notebook compared Logistic Regression, Multinomial Naive Bayes, Linear SVC, and Random Forest through a shared pipeline interface.

Approximate five-fold cross-validation macro-F1 results:

| Model | CV macro-F1 |
|---|---:|
| Tuned Multinomial Naive Bayes | 0.74 |
| Logistic Regression | 0.72 |
| Linear SVC | 0.72 |
| Untuned Multinomial Naive Bayes | 0.71 |
| Random Forest | 0.59 |

Macro-F1 gives equal weight to positive, neutral, and negative performance. It is more useful here than relying on one tiny test split.

The first 38-row test split produced unstable scores of roughly 0.47 to 0.61. Five-fold cross-validation showed that much of this apparent weakness was measurement noise caused by the small test set.

Hyperparameter tuning improved Naive Bayes by only about 0.03 macro-F1. The main accuracy constraint is therefore data quantity and quality, not the tuning search space.

The API confidence is the maximum Naive Bayes class probability. Naive Bayes probabilities may be overconfident and are not calibrated guarantees.

## 10. Frontend, CI/CD, and Azure

### Frontend

`static/index.html` is plain HTML, CSS, and JavaScript. It sends feedback to `/predict` and displays:

- green `POSITIVE`;
- red `NEGATIVE`;
- gray `NEUTRAL`;
- the returned confidence percentage.

FastAPI serves the frontend and API from the same application. There is no separate frontend build, deployment, or CORS boundary.

### GitHub Actions

`.github/workflows/deploy.yml` runs on pushes to `master` and through manual workflow dispatch.

The workflow:

1. checks out the repository;
2. configures Python 3.12;
3. installs `requirements.txt`;
4. runs `pytest`;
5. packages `src`, `static`, `data`, and `requirements.txt`;
6. deploys only after the test job succeeds.

Deployment requires the `AZURE_WEBAPP_PUBLISH_PROFILE` GitHub secret.

### Azure runtime

Azure uses Gunicorn with Uvicorn workers:

```bash
gunicorn -w 2 -k uvicorn.workers.UvicornWorker src.app:app
```

For provisioning, verification, CI/CD setup, redeployment, and resource cleanup, follow [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md).

## 11. Known limitations and gaps

The most important limitations are:

1. Only 149 usable labeled examples
2. Learning-scale data rather than real production feedback
3. Approximately 0.74 cross-validation macro-F1
4. Uncalibrated Naive Bayes probability scores
5. No authentication or authorization
6. No request rate limiting or input-size limit
7. No structured prediction logging
8. No data-drift or model-performance monitoring
9. No model registry or experiment tracking
10. No automated FastAPI or `train.py` integration tests
11. Research and runtime dependencies share one large requirements file
12. Startup training is convenient for the prototype but is not an ideal production artifact strategy

Do not hide these constraints in project descriptions. The project's strength is demonstrating the complete ML lifecycle with production awareness, not claiming production readiness.

### Documentation inconsistency

Some historical text still says deployment or source refactoring is planned. Current code and recent project documentation show both are implemented. When editing documentation, update stale statements carefully without deleting valuable decision history.

## 12. Safe change workflow

When the user requests a change, Codex should follow this sequence:

1. Read the relevant guidance, code, tests, and decision history.
2. Explain the proposed step and its scope.
3. Wait for explicit approval when required by the working agreement.
4. Preserve unrelated working-tree changes.
5. Add or update focused tests for behavioral changes.
6. Implement the smallest coherent change.
7. Run targeted tests, followed by the full suite when appropriate.
8. Verify training or application startup if the changed path affects them.
9. Review `git diff --check` and the final diff.
10. Report what changed, the evidence from verification, and remaining limitations.

### Verification checklist

Use the checks relevant to the change:

```bash
# Repository state
git status --short

# Formatting and conflict-marker problems
git diff --check

# Full automated suite
.venv/bin/pytest -q

# Rebuild model when training/model behavior changes
.venv/bin/python -m src.train

# Run service when API, lifecycle, or frontend behavior changes
.venv/bin/uvicorn src.app:app --reload
```

For API work, verify at minimum:

- `GET /health` returns `200` and `{"status":"ok"}`;
- valid positive, negative, and neutral text returns the response schema;
- blank text returns `422`;
- `/` serves the frontend;
- cold startup works when the model artifact is absent.

For ML changes, compare models using the same preprocessing and cross-validation protocol. Do not compare a new model's best test split against an older model's cross-validation average.

## 13. Sensible future work

Within Phase 1, the highest-value improvements are:

1. Collect thousands of representative, correctly labeled feedback examples.
2. Add API and training integration tests.
3. Separate runtime and development dependencies.
4. Add probability calibration and honest uncertainty handling.
5. Add structured logging, monitoring, and a labeled-feedback loop.
6. Add experiment tracking and versioned model artifacts.
7. Benchmark transformer and zero-shot baselines using the same evaluation protocol.

Phase 2 churn prediction should begin only after explicit approval and its own data and evaluation design are agreed.

## 14. Quick orientation checklist

For a new Codex session:

```text
[ ] Read CLAUDE.md
[ ] Read PROJECT_SETUP.md and identify stale historical status text
[ ] Read README.md
[ ] Read this handbook
[ ] Inspect the files directly related to the request
[ ] Check git status without modifying unrelated files
[ ] Activate or explicitly use .venv
[ ] Run the relevant baseline tests
[ ] Explain the next step and obtain required approval
[ ] Implement, verify, and report evidence
```

The core idea to retain is simple: this repository teaches an honest, end-to-end sentiment-analysis workflow. Protect that clarity when extending it.
