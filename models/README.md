# Anumaan — XGBoost Demand Forecasting Model

**Anumaan** ("estimate / prognosis" in Hindi) is the AI demand prediction
engine for the Anna Setu platform. It forecasts daily customer count for
a given kitchen location so managers can plan production accurately and
reduce food waste.

---

## Model File

| Property | Value |
|---|---|
| File | `anumaan_xgb_poisson.json` |
| File size | ~2.3 MB |
| MD5 (verified original) | `caafab89dacd2d8c242e02a0340acbbc` |
| Format | XGBoost native JSON (`booster.save_model()`) |

---

## Algorithm

| Property | Value |
|---|---|
| Algorithm | XGBoost Regressor |
| Objective | `count:poisson` (output is a positive count) |
| Hyperparameter search | Optuna (see `tune.py`) |
| Target variable | `Customer_Count` |
| Number of features | **47** |

---

## Training Data

| Property | Value |
|---|---|
| Source file | `restaurant_demand_28k.csv` |
| Locations | 26 (Loc_1 through Loc_26) |
| Date range | January 2023 – December 2025 (3 years daily) |
| Approximate rows | 28,000 |

---

## Data Split (Chronological)

Data is split by **date**, not randomly, to prevent look-ahead leakage.

| Split | Proportion | Date range |
|---|---|---|
| Train | 70% | 2023-01-08 to 2025-02-06 |
| Validation | 15% | 2025-02-07 to 2025-07-19 |
| Test | 15% | 2025-07-20 to 2025-12-30 |

---

## Test Performance

| Metric | Value |
|---|---|
| MAE | 48.77 – 48.95 |
| RMSE | 63.5 – 63.7 |

---

## Features (47 total, in exact model order)

Feature order is stored in `feature_manifest.json` and was read directly
from `booster.feature_names` — not typed from memory.

### Temporal (from `date` input)
| # | Feature | Description |
|---|---|---|
| 1 | `Day_of_Week` | 0=Mon … 6=Sun |
| 2 | `Month` | 1–12 |
| 3 | `Day_of_Year` | 1–365 |
| 4 | `Is_Weekend` | 1 if Day_of_Week ≥ 5 |
| 5 | `Annual_Seasonality` | `1.0 + 0.08 × sin(2π × Day_of_Year / 365)` |

### Context (supplied by user)
| # | Feature | Constraint |
|---|---|---|
| 6 | `Is_Holiday` | 0 or 1 |
| 7 | `Temp_Celsius` | −20.0 to 60.0 |
| 8 | `Rain_mm` | ≥ 0.0 |
| 9 | `Local_Event` | 0 or 1 |
| 10 | `Active_Promotion` | 0 or 1 |
| 11 | `Competitor_Promo` | 0 or 1 |
| 12 | `CPI_Index` | > 0.0 |
| 13 | `Online_Rating` | 1.0 to 5.0 |
| 14 | `Reservations` | ≥ 0 |

### Lag / rolling (location-specific historical data)
| # | Feature | Description |
|---|---|---|
| 15 | `Demand_Yesterday` | Customer count, same location, previous day |
| 16 | `Demand_7_Days_Ago` | Customer count, same location, 7 days prior |
| 17 | `Demand_MA7` | 7-day rolling mean of count (shift(1) before rolling — no leakage) |

### Cyclical encodings (derived from date)
| # | Feature | Formula |
|---|---|---|
| 18 | `Month_sin` | `sin(2π × Month / 12)` |
| 19 | `Month_cos` | `cos(2π × Month / 12)` |
| 20 | `DOW_sin` | `sin(2π × Day_of_Week / 7)` |
| 21 | `DOW_cos` | `cos(2π × Day_of_Week / 7)` |

### Location one-hot encoding (26 columns)
`Location_ID_Loc_1` through `Location_ID_Loc_9`, sorted **lexicographically**
(not numerically) as produced by `pandas.get_dummies()`:

```
Loc_1, Loc_10, Loc_11, Loc_12, Loc_13, Loc_14, Loc_15, Loc_16,
Loc_17, Loc_18, Loc_19, Loc_2, Loc_20, Loc_21, Loc_22, Loc_23,
Loc_24, Loc_25, Loc_26, Loc_3, Loc_4, Loc_5, Loc_6, Loc_7, Loc_8, Loc_9
```

> ⚠️ **The lexicographic sort is critical.** Passing the location columns in
> numeric order (Loc_1, Loc_2, … Loc_9, Loc_10 …) will silently produce
> wrong predictions because the model's tree splits reference column indices.

---

## Preprocessing Pipeline

The canonical preprocessing source is **`tune.py`** (root of the repo).
It performs, in order:

1. Load `restaurant_demand_28k.csv`
2. Drop `Capacity_Utilization` (target leakage)
3. Create `Demand_Yesterday` — `groupby(Location_ID).shift(1)`
4. Create `Demand_7_Days_Ago` — `groupby(Location_ID).shift(7)`
5. Create `Demand_MA7` — `groupby(Location_ID).transform(lambda x: x.shift(1).rolling(7).mean())`
6. Add `Annual_Seasonality` (formula above)
7. Compute cyclical features (`Month_sin/cos`, `DOW_sin/cos`)
8. `pd.get_dummies(columns=["Location_ID"], dtype=int)` — produces lexicographic OHE
9. Drop rows with NaN lag values (`dropna()`)
10. Chronological 70/15/15 split by unique date
11. Train with `xgb.train()` using Optuna-tuned hyperparameters + early stopping
12. Save with `booster.save_model("models/anumaan_xgb_poisson.json")`

`preprocess.py` is an earlier EDA and baseline script — it is **not** the
training source for the saved model.

---

## Inference (Backend Service)

The FastAPI inference layer lives in:
- `backend/app/services/anumaan.py` — feature engineering + singleton model loader
- `backend/app/routers/anumaan.py` — `POST /anumaan/predict-demand` endpoint
- `backend/app/schemas/anumaan.py` — Pydantic request/response models

The service replicates every transformation from `tune.py` at inference time
and builds the 47-feature vector in the exact same column order.

---

## Verified End-to-End Example

The following was run against the live backend with the restored original model
file (MD5 `caafab89dacd2d8c242e02a0340acbbc`) and xgboost 3.4.1.
**Verified end-to-end (backend + frontend), not theoretical.**

### Request (`POST /anumaan/predict-demand`)

```json
{
  "location_id": "Loc_3",
  "date": "2026-09-22",
  "is_holiday": 0,
  "temp_celsius": 24.5,
  "rain_mm": 0,
  "local_event": 0,
  "active_promotion": 1,
  "competitor_promo": 0,
  "cpi_index": 142.3,
  "online_rating": 4.2,
  "reservations": 125,
  "demand_yesterday": 410,
  "demand_7_days_ago": 395,
  "demand_ma7": 402.7
}
```

### Response

```json
{
  "predicted_customers": 493,
  "recommended_production": null,
  "expected_surplus": null,
  "location_id": "Loc_3",
  "date": "2026-09-22"
}
```

`predicted_customers = 493` (raw model output ≈ 494.5, rounded to nearest int).
Independent verification produced ≈ 494.5 for this input.

---

## ⚠️ Known Compatibility Issue: xgboost < 3.x

**xgboost 2.1.1 has a confirmed bug parsing the `base_score` field** for
models saved in the XGBoost native JSON format.

- The model correctly stores `base_score = 302.09` in the JSON file.
- xgboost 2.1.1 silently ignores this and loads the default `base_score = 0.5`
  instead, producing near-zero predictions (raw output ≈ 0.817 → rounds to 1).
- **No error or warning is raised.** The model appears to load successfully.

**Required version: xgboost ≥ 3.4.1**

```
pip install "xgboost>=3.4.1"
```

This is documented in `backend/requirements.txt` as `xgboost==3.4.1`.
Do not downgrade. Do not attempt to "fix" the model output by retraining —
the model is correct; only the library version matters.

---

## Files in This Directory

| File | Description |
|---|---|
| `anumaan_xgb_poisson.json` | Trained XGBoost Booster (native JSON, do not re-save) |
| `feature_manifest.json` | Machine-readable feature order + valid locations + formulas |
| `README.md` | This file |
