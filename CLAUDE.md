# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this project is

An **Intelligent Customer Feedback & Predictive Analytics** prototype. Long term it's an
enterprise platform (GenAI + Agentic AI + ML); **right now we build only the Machine
Learning part**, small and simple, as a learning prototype.

Two phases, built **one at a time**:

| Phase | Focus | Type | Status |
|-------|-------|------|--------|
| **Phase 1** | Sentiment analysis — classify feedback as positive / negative / neutral | Supervised, multi-class classification | In progress (build first) |
| **Phase 2** | Churn prediction — will a customer churn (yes/no) | Supervised, binary classification | Not started (build after Phase 1) |

The single source of truth for scope and decisions is **`PROJECT_SETUP.md`** — read it
before proposing work, and keep its decision log updated as things change.

## Working agreement (important)

- **Do not start coding a step until the user explicitly says "go"** for that step.
- Proceed **step by step**: explain → user approves → then implement that one step.
- Keep everything **simple and readable** — this is a learning prototype, not production.
- **Notebook-first.** Prototype in the Jupyter notebook so each step's output is visible;
  refactor good parts into `src/*.py` later.
- Do not jump ahead to Phase 2 while Phase 1 is unfinished.

## Layout

```
data/       feedback_sample.csv  (columns: text, sentiment)  — 90 balanced rows
notebooks/  01_sentiment_prototype.ipynb  — the Phase 1 pipeline
src/        (later) refactored reusable code
requirements.txt
PROJECT_SETUP.md   — living plan + decision log (authoritative)
```

## Phase 1 pipeline (the shape of the work)

Load → Explore → Clean text → Vectorize (TF-IDF) → Split (80/20) → Train several models →
Evaluate → Compare in one table → Diagnose with confusion matrix → Tune → Save (joblib).

Models are kept **swappable** (same fit/predict interface) so we can compare them fairly:
Logistic Regression, Multinomial Naive Bayes, Linear SVC, Random Forest, optional XGBoost.

## Environment & commands

- Python virtualenv lives in `.venv/` (gitignored). Activate with
  `source .venv/bin/activate`.
- Install deps: `pip install -r requirements.txt`
- Run the notebook: `jupyter notebook notebooks/01_sentiment_prototype.ipynb`
- Stack: pandas, scikit-learn, matplotlib, seaborn, joblib, jupyter (optional: xgboost).

## Conventions

- Notebook paths are **relative to `notebooks/`** (e.g. `../data/feedback_sample.csv`).
- Prefer scikit-learn's built-in metrics/plots over hand-rolled ones.
- Clear notebook outputs before committing to keep diffs readable.
- When adding a model, keep the identical train/evaluate interface so the comparison table
  stays apples-to-apples.
