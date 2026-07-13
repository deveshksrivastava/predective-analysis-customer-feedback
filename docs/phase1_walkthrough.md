# Phase 1 — Sentiment Analysis: Full Walkthrough (Steps 1–11)

> A self-contained, plain-language write-up of the entire Phase 1 pipeline. Every step has its
> **name**, **what we did & why**, the **outcome**, and a short **analysis**. This mirrors the
> notebook `notebooks/01_sentiment_prototype.ipynb` so the whole journey can be understood in
> one place.

_Last updated: 2026-07-07_

> **Update 2026-07-12:** this walkthrough describes the original 149-row learning sample.
> The project has since scaled to **30k real Amazon reviews** (`data/feedback_reviews.csv`),
> where the model ranking flipped: Logistic Regression (balanced, stopwords kept) now wins
> with ~0.65 macro-F1 and Naive Bayes comes last. See the README and `PROJECT_SETUP.md`
> decision log (2026-07-12) for the re-benchmark.

**Problem type:** supervised, multi-class classification — map feedback text → one of
`positive` / `neutral` / `negative`.

**Pipeline shape:** Load → Explore → Clean → Vectorize (TF-IDF) → Split → Train models →
Evaluate → Compare → Diagnose → Tune → Save & predict.

---

## Step 1 — Create the dataset

**Goal:** have a small, labeled sample to learn the ML flow on.

**What we did:** created `data/feedback_sample.csv` with two columns — `text` (the feedback
sentence) and `sentiment` (the label). Roughly balanced across the three classes.

**Outcome:** a CSV of **151 rows** (later cleaned to 149 — see Step 3).

**Analysis:** a small, balanced set is ideal for *learning the mechanics*. It is far too small
for a strong model — a fact that becomes the recurring theme of Steps 9–11.

---

## Step 2 — Load & explore

**Goal:** look at the data before modelling — "garbage in, garbage out."

**What we did:** loaded the CSV with pandas; checked shape, missing values, duplicates, class
balance (bar chart), sample rows per class, and average text length per class.

**Outcome:**
- Shape: **151 rows × 2 columns**.
- **1 missing label** and **1 duplicate row** found.
- Class balance slightly off because of those two bad rows.
- Text length was similar across classes (~9 words avg) — no easy shortcut there.

**Analysis:** exploring first paid off immediately — it surfaced two concrete data-quality
problems (a null-check can catch these) *before* we wasted time modelling on dirty data.

---

## Step 3 — Clean the data & text

**Goal:** fix what Step 2 found, and normalise text for TF-IDF.

**What we did:**
- **Row-level:** dropped the missing-label row and the duplicate row.
- **Text-level:** added a `clean_text()` function — lowercase, strip punctuation/symbols,
  collapse whitespace — stored as a new `clean_text` column.
- **Deliberately did NOT** "fix" suspected mislabels by eye (risky; the confusion matrix is the
  honest way to find them later).

**Outcome:** **151 → 149 rows**, cleanly balanced: **positive 50 / neutral 50 / negative 49**.

**Analysis:** cleaning makes `"Great!"` and `"great"` the same token so TF-IDF isn't fooled by
capitalisation or punctuation. Leaving labels untouched here was the principled choice — and
Step 9 later proved there were no mislabels to fix anyway.

---

## Step 4 — Turn text into numbers (TF-IDF) + encode labels

**Goal:** models need numbers, not words.

**What we did:**
- **Encoded labels** to integers: `negative → 0`, `neutral → 1`, `positive → 2`.
- **TF-IDF** (Term Frequency – Inverse Document Frequency) scores each word high if it's
  frequent in *one* feedback but rare across *all* feedback. Ran a **demo** vectorizer on all
  rows *only to illustrate* the output.

**Outcome:** demo TF-IDF matrix **149 × 453** (documents × vocabulary), sparse.

**Analysis:** we fit the demo on all data purely to *see* it. The **real** models fit TF-IDF on
the **training split only** (inside a Pipeline, Step 6) to avoid **data leakage** — letting the
model peek at test-set vocabulary would inflate scores dishonestly.

---

## Step 5 — Train / test split

**Goal:** measure performance on **unseen** data, not memorisation.

**What we did:** `train_test_split` with `test_size=0.25`, `stratify=y` (keeps class ratios),
`random_state=42` (reproducible).

**Outcome:** **111 train / 38 test** rows, with neg/neu/pos proportions preserved in both.

**Analysis:** stratification matters on a small, slightly imbalanced set. Note the test set is
**only 38 rows** — this smallness becomes the key issue diagnosed in Step 9.

---

## Step 6 — Train multiple models

**Goal:** the heart of the prototype — try several models the **same way** so comparison is fair.

**What we did:** wrapped each classifier in a `Pipeline([TF-IDF, classifier])`, stored them in a
`models` dict, and trained in a loop. Swapping a model is a one-line change.

| Model | Why it's here |
|-------|---------------|
| Logistic Regression | Strong, simple baseline for text |
| Multinomial Naive Bayes | Classic, fast text classifier |
| Linear SVC | Support Vector Classifier — great on sparse text |
| Random Forest | Non-linear, different family for contrast |

**Outcome:** all four trained without error; each fits TF-IDF on `X_train` only (no leakage).

**Analysis:** the shared interface is what makes the later comparison "apples-to-apples." This
is the reusable pattern the whole project is built to teach.

---

## Steps 7–8 — Evaluate & compare

**Goal:** score every model on the held-out test set and rank them.

**What we did:** computed accuracy + macro precision/recall/F1 per model, a per-class report, and
a confusion matrix grid.

**Outcome (single 38-row test split):**

| Model | Accuracy | F1 (macro) |
|-------|---------:|-----------:|
| Naive Bayes | 0.61 | 0.61 |
| Random Forest | 0.50 | 0.50 |
| Linear SVC | 0.47 | 0.47 |
| Logistic Regression | 0.47 | 0.47 |

**Analysis:** scores looked *worryingly low*, and `negative`/`neutral` got confused a lot. The
tempting-but-wrong reaction is to immediately tune hyperparameters. Instead we stopped to
**diagnose** — which turned out to be the most important decision in Phase 1.

---

## Step 9 — Diagnose the errors (& fix the evaluation)

**Goal:** understand *why* scores are low before changing anything.

**What we did:**
1. Printed the **misclassified test rows** and read them by eye.
2. Scanned the **whole CSV** for text whose tone contradicts its label.
3. Added **5-fold cross-validation** as a steadier measuring stick than one small split.

**Outcome:**
- **No genuine mislabels** — the plan's old "2 deliberate mislabels" assumption was stale (the
  dataset had been regenerated). We did **not** fabricate a fix.
- The scary low scores were mostly **noise from a tiny 38-row test set**.

| Model | Single-split F1 | 5-fold CV F1 |
|-------|----------------:|-------------:|
| Logistic Regression | 0.47 | **0.72** |
| Naive Bayes | 0.61 | **0.71** |
| Linear SVC | 0.47 | **0.72** |
| Random Forest | 0.50 | 0.59 |

**Analysis:** this is the standout lesson. One small split is a **noisy ruler** — a few unlucky
misses swing accuracy several points. Cross-validation revealed the models are genuinely
~0.72 macro-F1, not ~0.50. The hardest real cases are **neutral factual sentences**
("The return window is thirty days") that TF-IDF reads as negative. The biggest lever is **more
data**, not tuning.

---

## Step 10 — Tune the leading model

**Goal:** squeeze out more from the front-runner.

**What we did:** `GridSearchCV` over **Naive Bayes** (chosen for its CV lead + it gives
probabilities), searching TF-IDF settings (n-grams, `min_df`, sublinear scaling, stopwords) and
the NB smoothing `alpha`, scored by 5-fold macro-F1.

**Outcome:**

| | CV macro-F1 |
|---|---:|
| Untuned Naive Bayes | ~0.71 |
| **Tuned** Naive Bayes (`alpha=0.1`, unigram + English stopwords) | ~**0.74** |
| Gain from tuning | **+~0.03** |

**Analysis:** tuning helped only **marginally**. The grid *could* have picked bigrams or kept
stopwords — it didn't; the simple setup stayed best. Honest conclusion: on 149 rows,
**data — not hyperparameters — is the bottleneck.** The tuned pipeline was stored as
`best_model`, refit on all data.

---

## Step 11 — Save & predict

**Goal:** persist the model and use it on new feedback — the payoff. [Pickel/joblib]

**What we did:**
- Saved the tuned pipeline **+ label encoder** to `models/sentiment_model.joblib` (one file; the
  pipeline already contains TF-IDF + classifier).
- **Reloaded from disk** (proving the artifact works) and predicted on new sentences, cleaning
  them with the **same `clean_text()`** used in training (no train/serve skew).

**Outcome — predictions:**

| Prediction | Confidence | Feedback |
|------------|-----------:|----------|
| **positive** | 97% | "Absolutely love this, it works perfectly and support was great!" |
| **negative** | 79% | "The item arrived broken and no one will respond to my emails." |
| **neutral**  | 91% | "The package was delivered on Tuesday as scheduled." |
| **neutral**  | 82% | "It is fine, does the job but nothing special." |

Artifact written: `models/sentiment_model.joblib` (~32 KB).

**Analysis:** all four predictions are sensible — including the factual "delivered on Tuesday"
correctly read as **neutral**, the exact case that fooled models before Step 9. Caveats: the
mixed-tone "it is fine… nothing special" (neutral, 82%) is genuinely borderline, and Naive Bayes
probabilities tend to be **over-confident** — treat them as a ranking, not calibrated certainty.
The honest performance number remains the **CV macro-F1 ≈ 0.74**, not these hand-picked confidences.

---

## Overall outcome & analysis

**Phase 1 "done" criteria — all met:**
- ✅ End-to-end pipeline runs on the sample CSV.
- ✅ 4 models trained + compared in one table, plus honest cross-validation.
- ✅ We can explain why the leading model wins and predict on new sentences.

**Model scoreboard (5-fold CV macro-F1):** tuned Naive Bayes ~**0.74**; Logistic Regression and
Linear SVC ~0.72; Random Forest ~0.59 (weakest here).

**The three biggest lessons:**
1. **Explore & clean first** — Step 2 caught real data problems before modelling.
2. **Trust the right ruler** — a single tiny test split is noisy; **cross-validation** turned an
   apparent ~0.50 into a real ~0.72 (Step 9). This was the pivotal insight.
3. **Data > tuning at this scale** — grid search added only ~+0.03 (Step 10); the clear next
   lever is **more/better data**, especially neutral examples.

**Honest headline:** ~0.74 CV macro-F1 on **149 rows** is a *learning* result, not production
quality.

**Repo notes:**
- `models/` is **gitignored** — the `.joblib` is a regenerable artifact; re-run the notebook to
  recreate it.
- Full decision history: `PROJECT_SETUP.md` §6.

**Next (not started without an explicit "go"):** refactor the notebook into `src/*.py`, gather
more data, or begin **Phase 2 — churn prediction**.
