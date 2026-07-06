---
name: add-model
description: Use when the user wants to add a new scikit-learn (or XGBoost) classifier to the sentiment model comparison, or try/swap a model in the Phase 1 pipeline. Keeps the swappable interface and the comparison table apples-to-apples. Triggers on "add a model", "try SVM/random forest/naive bayes", "compare another classifier", "swap the model".
---

# Add a model to the sentiment comparison

Add a new classifier to `notebooks/01_sentiment_prototype.ipynb` (or `src/` once
refactored) **without breaking the swappable interface** that makes model comparison fair.

## Contract every model must follow

All models share the same pipeline: the **same** TF-IDF features, the **same** train/test
split, and the **same** evaluation. Only the estimator changes. Concretely, register each
model as a name → estimator entry, e.g.:

```python
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Multinomial NB":      MultinomialNB(),
    "Linear SVC":          LinearSVC(),
    "Random Forest":       RandomForestClassifier(random_state=42),
    # add the new one here
}
```

Then train/evaluate every entry in one loop so the comparison table is generated the same
way for all.

## Steps

1. Confirm which model and any key hyperparameters the user wants.
2. Add the import and one entry to the `models` dict. Do **not** change the shared TF-IDF
   vectorizer or the split — that would make the comparison unfair.
3. If the model needs dense input (rare here) or extra deps (e.g. `xgboost`), note it and
   confirm it's in `requirements.txt` before running.
4. Re-run train → evaluate for all models, then regenerate the **one comparison table**
   (accuracy / precision / recall / F1, macro-averaged) ranked best-first.
5. Add the new model's **confusion matrix** so failure cases are visible.
6. Briefly summarize: did it beat the current best, and on which classes does it win/lose.

## Rules

- One shared vectorizer + one shared split for all models — never per-model.
- Keep hyperparameters explicit and simple; note any that were tuned.
- Set `random_state=42` where the estimator supports it, for reproducible comparisons.
- This is a step that changes code — only run it after the user says "go".
