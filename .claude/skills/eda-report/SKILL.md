---
name: eda-report
description: Use when the user wants an exploratory data analysis (EDA) report or a quick data-quality summary of a feedback CSV — row count, class balance, text-length stats, duplicates, and sample rows. Triggers on "eda", "explore the data", "data report", "class balance", "check the dataset".
---

# EDA Report for feedback data

Produce a compact, readable exploratory summary of a feedback dataset before any modelling.
Default file: `data/feedback_sample.csv` (columns `text`, `sentiment`). Ask which CSV if
another is meant.

## Steps

1. Load with pandas from the given CSV (relative paths are from the repo root; from the
   notebook they are from `notebooks/`).
2. Report, in this order:
   - **Shape** — number of rows and columns, and the column names.
   - **Class balance** — `value_counts()` on `sentiment`, both counts and percentages.
     Flag if any class is under ~20% of the data (imbalance affects accuracy later).
   - **Text length** — characters and word counts per row: min / median / max, and call
     out suspiciously short (< 3 words) or long outliers.
   - **Missing & duplicates** — null counts per column; number of exact-duplicate `text`
     rows.
   - **Samples** — 2–3 example rows per sentiment class so the labels can be sanity-checked.
3. Add one **bar chart** of class counts (`sns.countplot(data=df, x="sentiment")`) when
   producing notebook or image output; skip the chart for a plain-text summary.
4. End with a short **"watch-outs"** list: concrete data issues that could hurt Phase 1
   (imbalance, near-duplicate texts, mislabeled-looking samples), each with a one-line fix.

## Rules

- Keep it simple and readable — this is a learning prototype.
- Don't clean, resample, or modify the data here; only describe it. Cleaning is a separate,
  user-approved step.
- Prefer pandas/seaborn built-ins over hand-rolled loops.
