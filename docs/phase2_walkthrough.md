# Phase 2 — Churn Prediction: Full Walkthrough

> Companion to `notebooks/02_churn_prototype.ipynb`, in the same style as the Phase 1
> walkthrough. The deliverable is the **chance** a customer churns — a probability — so
> probability quality (ROC-AUC, calibration) is the first-class concern throughout.

_Last updated: 2026-07-12_

**Problem type:** supervised, binary classification with probability output —
map a customer profile → P(churn).

**Pipeline shape:** Acquire → Load & explore → Clean → Encode → Split → Train models →
Evaluate → Compare → Diagnose (calibrate + threshold + drivers) → Tune → Save & predict.

---

## Step 1 — Acquire the dataset

**IBM Telco Customer Churn** — the standard public churn benchmark: **7,043 real telecom
customers, 21 columns**, target `Churn` (Yes/No). Committed as `data/telco_churn.csv`
(~1 MB). Real data, consistent with the Phase 1 decision to avoid synthetic "toy" datasets.

## Step 2 — Load & explore

- Churn rate **26.5%** — imbalanced, so plain accuracy would mislead (a "nobody churns"
  model scores 73.5%).
- Month-to-month contracts churn ~43%; two-year contracts ~3%. Churners cluster at low
  tenure.
- **Real data bug found:** `TotalCharges` is typed as text because **11 customers have a
  blank** — all with `tenure=0` (brand-new customers). Exploring first caught it, exactly
  like Phase 1's missing label.

## Step 3 — Clean

Coerce `TotalCharges` to numeric with blanks → 0 (justified: those customers have paid
nothing yet), drop `customerID`, map `Churn` Yes/No → 1/0. Nothing speculative.

## Step 4 — Encode features

Tabular data this time: `ColumnTransformer` with `StandardScaler` on the 3 numeric
columns and `OneHotEncoder(handle_unknown="ignore")` on the 16 categoricals (19 raw
columns → ~45 model features). Everything lives inside the model `Pipeline`, so encoders
fit on the **training split only** — the same no-leakage principle as Phase 1's TF-IDF.
`handle_unknown="ignore"` also means serving never crashes on an unseen category value.

## Step 5 — Split

Stratified 80/20 (`random_state=42`) → 5,634 train / 1,409 test. A 1,409-customer test
set is a trustworthy ruler on its own — the contrast with Phase 1's noisy 38-row split.

## Step 6 — Train several models

Same swappable-pipeline discipline as Phase 1. XGBoost is optional (needs the `libomp`
system library on macOS; the notebook degrades gracefully without it).

## Steps 7–8 — Evaluate & compare (held-out 1,409 customers)

| Model | ROC-AUC | PR-AUC | Brier ↓ | Recall@0.5 |
|-------|--------:|-------:|--------:|-----------:|
| **Logistic Regression (balanced)** | **0.842** | 0.633 | 0.169 | 0.783 |
| HistGradientBoosting | 0.833 | **0.638** | **0.142** | 0.529 |
| Random Forest | 0.822 | 0.602 | 0.156 | 0.644 |

**The interesting tension:** Logistic Regression ranks customers best (highest ROC-AUC)
but has the *worst* Brier score — `class_weight="balanced"` deliberately inflates churn
probabilities. Great ranking, dishonest percentages. That's what Step 9 fixes.

## Step 9 — Diagnose: calibrate, choose the threshold, explain the drivers

1. **Calibration.** Wrapped the leader in `CalibratedClassifierCV(method="sigmoid", cv=5)`:
   Brier **0.169 → 0.138** while ROC-AUC stayed **0.842** (sigmoid calibration is
   monotone, so the ranking survives). A stated "70% churn risk" now means ~70% of such
   customers actually churn.
2. **Threshold as a business decision.** With a retention offer at ~$50 and a lost
   customer at ~$500, sweeping thresholds on the calibrated probabilities puts the
   cost minimum at **0.10** — which is no accident: the theoretical optimum for a
   10:1 cost asymmetry is exactly the cost ratio (50/500 = 0.10). The API ships this
   threshold *inside the model bundle*, not as a hidden 0.5.
3. **Drivers.** Coefficients match business intuition: **fiber-optic internet** (+0.72)
   and **month-to-month contracts** (+0.66) push churn; **tenure** (−1.14) and
   **two-year contracts** (−0.77) protect. This answers the stakeholder question
   "why is this customer flagged?" for free.

## Step 10 — Tune

`GridSearchCV` over `C`, 5-fold ROC-AUC: best `C=10`, CV 0.846 vs 0.842 test after
calibration — **marginal**, repeating Phase 1's lesson that at this scale data beats
hyperparameters.

## Step 11 — Save & predict

Final model (tuned + calibrated, refit on all 7,043 rows) saved to
`models/churn_model.joblib` **together with the decision threshold** — in production the
model and its decision policy version together. Reloaded from disk and probed:

| Customer profile | Churn probability | Decision (th=0.10) |
|------------------|------------------:|--------------------|
| tenure 2, fiber optic, month-to-month, e-check | **74.3%** | flag for retention |
| tenure 68, DSL, two-year, auto bank transfer | **0.6%** | leave alone |

---

## Serving (mirrors Phase 1)

- `src/churn.py` — `build_churn_pipeline()`, `train_churn()`, bundle save/load; the app
  trains on startup if the artifact is missing (seconds), so nothing binary ships in git.
- `POST /predict-churn` — fully typed request (invalid category values → 422), returns
  `{churn_probability, will_churn, risk_band}`; each prediction is logged as one
  structured JSON line (the seed of a monitoring story).
- Frontend gains a "Will this customer churn?" form pre-filled with a high-risk profile —
  switch Contract to "Two year" and raise tenure to watch the risk drop live.

## The three production lessons this phase adds

1. **`class_weight="balanced"` breaks probability honesty** even while helping ranking —
   calibrate before showing a percentage to a human.
2. **0.5 is a convention, not a decision** — derive the threshold from costs, document
   it, and version it with the model.
3. **A 1,409-row test set didn't need cross-validation** — knowing *when* a single split
   is sufficient is as important as knowing when it isn't (Phase 1, Step 9).

**Honest headline:** ROC-AUC ≈ **0.84**, competitive with published Telco baselines;
calibrated probabilities; documented cost-based threshold. Neutral-tension caveat: with
threshold 0.10 the model flags ~half of all customers (precision 0.40 / recall 0.95) —
correct under the stated cost model, and the first thing to revisit if real retention
costs differ.
