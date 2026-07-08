# Project Setup & Plan — Intelligent Customer Feedback & Predictive Analytics

> Living document. We update this as we discuss and make decisions.
> **Rule: No coding until the user explicitly says "go" for a step.**

_Last updated: 2026-07-08_

---

## 1. Vision (long term)

An enterprise AI platform combining **Generative AI, Agentic AI, and Machine Learning**
to analyse customer feedback, classify sentiment, detect product issues, and predict &
recommend resolutions.

**Eventual tech stack (aspirational, NOT for the prototype):** Azure AI Foundry, Azure
OpenAI, LangGraph, LangChain, Databricks, MLflow, Scikit-learn, XGBoost, Azure AI Search,
FastAPI, React, Power BI.

## 2. What we are building RIGHT NOW

Start **small and simple**. Build **only the Machine Learning part** as an easy-to-understand
**prototype**. Goal: learn how an ML project is structured and be able to try different models,
compare their results, spot problems, and fix them.

We build in **two phases, one at a time**:

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | **Sentiment analysis** — classify feedback text as positive / negative / neutral | Planned (build first) |
| **Phase 2** | **Predictive analysis** — predict customer churn | Planned (build after Phase 1) |

```
   For a production-ready Phase 1 pipeline, use this stack:

   1. pandas – Load and clean review data.
   2. scikit-learn – Split data, vectorize text (e.g., TF-IDF), train a baseline model like Logistic Regression, and evaluate it.
   3. matplotlib and seaborn – Visualize class distribution, confusion matrix, and performance metrics.
   4. joblib – Save both the trained model and the preprocessing pipeline (such as the TF-IDF vectorizer) for consistent inference.
   5. Jupyter – Prototype and experiment during development.
   6. XGBoost – Try it as a stronger baseline if your features are tabular or engineered; for raw text sentiment, traditional TF-IDF + Logistic Regression or modern transformer models are often more suitable than XGBoost alone.

```


```
Chart

Purpose

Code

1. Bar Chart

Compare category counts

sns.countplot(data=df, x="sentiment")

2. Histogram

Show distribution of numeric values

sns.histplot(data=df, x="age")

3. Box Plot

Detect outliers and spread

sns.boxplot(data=df, y="salary")

4. Scatter Plot

Show relationship between two variables

sns.scatterplot(data=df, x="age", y="salary")

5. Line Chart

Show trends over time

plt.plot(df["date"], df["sales"])

Links:

https://chatgpt.com/g/g-p-6a4c1339dbe4819184750211fe44f89e

Both are in scope. We do **not** build them at the same time. Phase 2 starts only after
Phase 1 works and is understood.

Phase 1 — Sentiment Analysis
Supervised (classification)

You're mapping feedback text → one of three known labels (positive / negative / neutral). To train this, you need feedback examples that are already labeled with the correct sentiment. The model learns the mapping from labeled data. That's the definition of supervised learning — specifically multi-class classification.

Phase 2 — Churn Prediction
Supervised (classification)

You're predicting a known target: will this customer churn or not (churn = yes/no). You train on historical customers where you already know the outcome (who actually churned). Again, labeled target → supervised, and it's binary classification.

So where does unsupervised fit?
Neither phase is unsupervised as written. Unsupervised learning has no labeled target — the model finds structure on its own. It would show up if you reframed a task like:

Task	Type
Classify sentiment into predefined pos/neg/neutral	Supervised
Discover natural topics/themes in feedback without predefining them (topic modeling, clustering)	Unsupervised
Predict churn (yes/no) from historical outcomes	Supervised
Segment customers into behavioral groups without knowing labels first	Unsupervised
```

## 3. Working agreement

- Proceed **step by step**. I explain, you approve, then we do that step.
- **Do not start coding until the user says so.**
- Keep everything **simple and readable** — this is a learning prototype.
- Keep this `PROJECT_SETUP.md` updated with decisions as we go.

---

## 4. Phase 1 — Sentiment Analysis (build first)

### 4.1 Goal
Given a piece of customer feedback (free text) → predict its **sentiment**:
`positive`, `negative`, or `neutral`.
The core value: an easy pipeline where we can **plug in different models, compare their
scores, see where they fail, and improve**.

### 4.2 Data
- A small sample **CSV**: `feedback_sample.csv`
- Columns:
  - `text` — the customer feedback sentence
  - `sentiment` — the label (`positive` / `negative` / `neutral`)
- Start with ~50–150 rows to learn the flow; swap in a larger/real dataset later.

### 4.3 The ML pipeline (step by step)
1. **Load** the CSV with pandas.
2. **Explore** — row count, class balance, look at sample rows.
3. **Clean text** — lowercase, remove punctuation, (optional) remove stopwords.
4. **Vectorize** — convert text to numbers with **TF-IDF**.
5. **Split** — train set vs test set (e.g. 80/20).
6. **Train several models** and keep the interface identical so they're swappable:
   - Logistic Regression
   - Multinomial Naive Bayes
   - **Linear SVC (Support Vector Classifier)**
   - Random Forest
   - _(optional)_ XGBoost
7. **Evaluate** each model — accuracy, precision, recall, F1, confusion matrix.
8. **Compare** — one results table, all models ranked.
9. **Diagnose & fix** — use confusion matrix to see failure cases; address class
   imbalance, add data, adjust preprocessing.
10. **Tune** — hyperparameter tuning on the best model.
11. **Save & predict** — save the winning model (joblib) and run it on new feedback.

### 4.4 Tech stack (minimal, for the prototype only)
- **Python 3**
- **pandas** — data loading/exploration
- **scikit-learn** — vectorizer, models, metrics
- **matplotlib / seaborn** — simple charts (confusion matrix)
- **joblib** — save/load model
- **Jupyter notebook** — run and see each step
- _(optional)_ **xgboost**

### 4.5 How we build it — recommended approach
**Notebook-first.** Start in a single Jupyter notebook so every step's output is visible
while learning, then later refactor the good parts into reusable `.py` files.

_Alternatives considered:_
- Straight to `.py` scripts — cleaner, but less visual for learning. (Do this later.)
- Streamlit demo app — nice UI, but premature for a first prototype.

### 4.6 Proposed project structure
```
predective-analysis-customer-feedback/
├── data/
│   └── feedback_sample.csv        # sample dataset
├── notebooks/
│   └── 01_sentiment_prototype.ipynb
├── src/                           # (later) refactored reusable code
├── requirements.txt
├── README.md
└── PROJECT_SETUP.md               # this file
```

### 4.7 How we compare models & fix problems
- A **metrics comparison table** (accuracy / precision / recall / F1 per model).
- **Confusion matrix** per model to see exactly which classes get confused.
- Improvement levers: more/better data, fix class imbalance, tweak text cleaning,
  tune TF-IDF settings, tune model hyperparameters.

### 4.8 Phase 1 "done" criteria
- Pipeline runs end to end on the sample CSV.
- At least 3 models trained and compared in one table.
- We can explain why the best model wins and predict on a new sentence.

---

## 4B. Phase 1 deployment — API + Frontend + Azure (PLANNED, awaiting "go")

> Full step-by-step plan (with code, tests, and commands):
> **`docs/superpowers/plans/2026-07-08-sentiment-api-frontend-azure.md`**
> Nothing below is implemented yet — coding starts only on explicit "go".

### 4B.1 Goal
Turn the finished Phase 1 model into a small deployable service: send feedback text to a
server, get back whether it is **positive** (plus the full sentiment and a confidence
score), with a minimal web page to try it — deployed to **Azure App Service**.

### 4B.2 Starting point
The notebook's reusable logic is already refactored into `src/preprocessing.py` and
`src/model.py` (15 passing tests), so this plan builds on those modules rather than
re-converting the notebook.

### 4B.3 The four tasks
1. **`src/train.py`** — script reproducing the notebook's final recipe (tuned Naive Bayes,
   refit on all 149 rows) → writes `models/sentiment_model.joblib`. Model becomes
   regenerable anywhere without Jupyter.
2. **`src/app.py`** — FastAPI server: `GET /health` and `POST /predict`
   (`{"text": "..."}` → `{"sentiment", "is_positive", "confidence"}`). If the model file
   is missing (fresh clone / fresh Azure instance) it trains on startup (seconds), so
   `models/` stays gitignored.
3. **`static/index.html`** — one plain HTML+JS page served by the same app at `/`:
   textarea → Analyze → green ✓ POSITIVE / red ✗ NEGATIVE / gray – NEUTRAL with
   confidence %. No framework, no build step, no CORS.
4. **Azure** — deploy the single app to App Service (Linux, Python) via `az webapp up`,
   startup command `gunicorn -k uvicorn.workers.UvicornWorker src.app:app`, documented in
   `docs/DEPLOYMENT.md`. The live deploy runs together with the user (`az login` needed).

### 4B.4 Key decisions (alternatives in the plan file)
| Decision | Chosen | Why |
|----------|--------|-----|
| Serving framework | **FastAPI** | In the long-term target stack; typed JSON validation; auto `/docs` |
| Frontend | **Single static HTML+JS page served by FastAPI** | One deployable; React/Streamlit overkill for one form |
| Model artifact on Azure | **Train on startup if missing** | 149 rows trains in seconds; keeps binary out of git |
| Azure compute | **App Service via `az webapp up`** | Shortest repo → public URL path for a prototype |

New dependencies: `fastapi`, `uvicorn`, `gunicorn`, `httpx`. Every task is TDD
(failing test → implement → pass → commit). Out of scope: auth, CI/CD, Docker, Phase 2.

---

## 5. Phase 2 — Predictive Analysis / Churn (build later)

_Only start after Phase 1 is complete and understood._

- **Goal:** predict whether a customer is likely to **churn**.
- **Inputs:** structured customer data + signals derived from Phase 1 (e.g. sentiment).
- **Likely models:** Logistic Regression, Random Forest, XGBoost.
- **Same discipline:** train several models, compare, diagnose, tune.
- Details to be brainstormed when we get there.

---

## 6. Open questions / decisions log

| Date | Decision / Question | Outcome |
|------|--------------------|---------|
| 2026-07-06 | "svc file" meaning | Meant a sample **CSV** dataset |
| 2026-07-06 | Scope order | **Sentiment first**, then predictive/churn |
| 2026-07-06 | Build style | **Confirmed: Notebook-first** |
| 2026-07-06 | Number of sentiment classes | **Confirmed: 3 classes** (positive / negative / neutral) |
| 2026-07-06 | Step 1 (dataset) | **Done** — `data/feedback_sample.csv` created (90 rows, balanced) |
| 2026-07-06 | Environment | Python 3.13 venv (`.venv`) + Jupyter kernel `feedback-prototype`; deps installed |
| 2026-07-06 | Step 2 (load & explore) | **Done** — notebook `notebooks/01_sentiment_prototype.ipynb` runs clean |
| 2026-07-06 | Data-quality issues found | 1 missing label, 1 duplicate row, ~2 suspected mislabels; now 32/30/28. **To fix in Step 3.** |
| 2026-07-06 | Step 3 (clean data & text) | **Done** — dropped missing-label + duplicate (91→89 rows); added `clean_text`. Mislabels left for confusion-matrix diagnosis. |
| 2026-07-06 | Step 4 (TF-IDF + labels) | **Done** — labels encoded (neg/neu/pos → 0/1/2); demo TF-IDF 89×313 with `stop_words="english"`. Real TF-IDF fits on train split via Pipeline (Step 6). |
| 2026-07-06 | Step 5 (train/test split) | **Done** — stratified 75/25, `random_state=42` → 66 train / 23 test. |
| 2026-07-06 | Step 6 (train models) | **Done** — 4 Pipelines (TF-IDF→clf) in a `models` dict: LogReg, NaiveBayes, LinearSVC, RandomForest. All trained. |
| 2026-07-06 | Step 7–8 (evaluate + compare) | **Done** — ranked table + reports + confusion matrices. Scores poor (acc 39–48%); `positive` class collapsing (RF recall 0.00). Root cause: 2 mislabels + tiny data. **Fix in Step 9.** |
| 2026-07-07 | Dataset size correction | CSV had been regenerated to **151 rows → 149 after cleaning** (positive 50 / neutral 50 / negative 49). Earlier "90 rows / 2 mislabels" notes are stale. |
| 2026-07-07 | Step 9 (diagnose & fix) | **Done** — printed misclassified test rows + scanned whole CSV: **no genuine mislabels** (nothing to override; did not fabricate one). Real issue = tiny 38-row single split is high-variance. **Fix: added 5-fold cross-validation** → linear models ~0.72 macro-F1 (vs ~0.47–0.61 on the noisy split); NB/LogReg/LinearSVC lead, RF trails. Bigrams/keeping stopwords didn't help. Biggest lever = more data (esp. neutral). |
| 2026-07-07 | Step 10 (tune) | **Done** — `GridSearchCV` (5-fold macro-F1) on Naive Bayes over TF-IDF + `alpha`. Best = unigram + English stopwords, `alpha=0.1` → CV macro-F1 ~**0.74** vs ~0.72 untuned (**+~0.02**, marginal). Tuned pipeline stored as `best_model`, refit on all data. Confirms data — not hyperparameters — is the bottleneck. |
| 2026-07-07 | Step 11 (save & predict) | **Done** — saved tuned pipeline + label encoder to `models/sentiment_model.joblib` (joblib); reloaded from disk and predicted on 4 new sentences (all sensible, 79–97% confidence). `models/` **gitignored** as a regenerable artifact. **Phase 1 complete** — all "done" criteria met. |
| 2026-07-07 | Phase 1 sign-off | **Awaiting user sign-off.** Phase 2 (churn) not to start without explicit go. Likely follow-ups: refactor notebook → `src/*.py`; gather more/better data (esp. neutral). |
| 2026-07-07 | Refactor + tests | **Done** — extracted reusable code to `src/preprocessing.py` (`clean_text`) and `src/model.py` (`build_pipeline`, `save_model`, `load_model`, `predict_sentiment`). Added pytest suite in `tests/` (**15 tests, all passing**). Tests found a real bug: `predict_sentiment([])` errored on empty TF-IDF transform → guarded with an early return. Added `pytest` to `requirements.txt`. |
| 2026-07-08 | Deployment + frontend plan | **Plan drafted, awaiting "go"** — see §4B and `docs/superpowers/plans/2026-07-08-sentiment-api-frontend-azure.md`. FastAPI API (`/health`, `/predict` with `is_positive` flag) + `src/train.py` + static HTML frontend, one Azure App Service; model self-trains on startup since `models/` is gitignored. No code written yet. |

---

## 7. Next step

Review this plan. When you're happy, say **"go"** and we'll start with **Step 1 of Phase 1**:
creating the sample `feedback_sample.csv` dataset. Nothing gets coded before then.

---

## 8. Claude Code configuration (tooling setup)

The repo is set up for Claude Code with project-level configuration so the assistant follows
our working agreement and has helpful, repeatable tools. Files:

```
CLAUDE.md                     # project guidance loaded into every Claude Code session
.claude/settings.json         # hooks (team-wide, committed)
.claude/skills/eda-report/    # custom skill: /eda-report
.claude/skills/add-model/     # custom skill: /add-model
.mcp.json                     # MCP servers (filesystem, fetch)
```

### 8.1 CLAUDE.md
Project guidance derived from this document: the two-phase scope, the **"don't code until the
user says go"** rule, repo layout, the Phase 1 pipeline shape, env/commands, and conventions
(notebook-relative paths, swappable-model interface). `PROJECT_SETUP.md` stays the
authoritative source; `CLAUDE.md` is the short always-loaded summary.

### 8.2 Skills (2)
| Skill | Purpose |
|-------|---------|
| **`/eda-report`** | Exploratory data-analysis / data-quality summary of a feedback CSV — shape, class balance, text-length stats, duplicates, sample rows, and watch-outs. Describes only; never modifies data. |
| **`/add-model`** | Add a new scikit-learn / XGBoost classifier to the Phase 1 comparison while keeping the shared TF-IDF features + train/test split so the comparison stays apples-to-apples. |

### 8.3 Hooks (2) — in `.claude/settings.json`
| Event | What it does |
|-------|--------------|
| **SessionStart** | Injects project context (Phase 1 sentiment, "don't code until go", points at `PROJECT_SETUP.md`) into every session. |
| **PostToolUse** (`Write\|Edit`) | Runs `python -m py_compile` on any `.py` file that is written/edited and surfaces syntax errors immediately. Uses the project `.venv` python; non-Python files are skipped. |

> Hooks in a newly created `.claude/` only become live after opening `/hooks` once (reloads
> config) or restarting Claude Code.

### 8.4 MCP servers (2) — in `.mcp.json`
| Server | Command | Use |
|--------|---------|-----|
| **filesystem** | `npx -y @modelcontextprotocol/server-filesystem <project>` | Structured file access scoped to this repo. |
| **fetch** | `uvx mcp-server-fetch` | Fetch web content (e.g. pulling datasets/docs). |

> MCP servers prompt for approval on next start; manage them with `/mcp`. Both runtimes
> (`npx`, `uvx`) are already installed.

### 8.5 Decisions log addition
| Date | Decision / Question | Outcome |
|------|--------------------|---------|
| 2026-07-06 | Claude Code tooling | Added `CLAUDE.md`, 2 skills (`/eda-report`, `/add-model`), 2 hooks (SessionStart context, Python syntax check), 2 MCP servers (filesystem, fetch) |
