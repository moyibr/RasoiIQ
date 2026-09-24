import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

# Load dataset
df = pd.read_csv("restaurant_demand_28k.csv")

# Convert Date column
df["Date"] = pd.to_datetime(df["Date"])

# Sort data
df = df.sort_values(["Location_ID", "Date"])

print("Dataset shape:", df.shape)

# Choose one location
location = "Loc_1"

sample = df[df["Location_ID"] == location].copy()

# 30-day moving average
sample["MA30"] = sample["Customer_Count"].rolling(30).mean()

plt.figure(figsize=(15,5))

# Daily demand
plt.plot(
    sample["Date"],
    sample["Customer_Count"],
    color="lightgray",
    linewidth=0.8,
    alpha=0.5,
    label="Daily Demand"
)

# Smooth trend
plt.plot(
    sample["Date"],
    sample["MA30"],
    color="crimson",
    linewidth=2.5,
    label="30-Day Moving Average"
)

plt.title(f"3-Year Customer Demand Trend ({location})")
plt.xlabel("Date")
plt.ylabel("Customer Count")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ---------------------------------------
# STEP 4: SPEARMAN CORRELATION HEATMAP
# ---------------------------------------

import numpy as np

# Select only numerical columns
numeric_df = df.select_dtypes(include=np.number)

print("\nNumerical columns:")
print(numeric_df.columns.tolist())

# Calculate Spearman correlation
corr = numeric_df.corr(method="spearman")

# Plot heatmap
plt.figure(figsize=(12, 9))

sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=0.5
)

plt.title("Spearman Correlation Heatmap")
plt.tight_layout()
plt.show()
# ==========================================
# STEP 5: DEMAND BY DAY OF WEEK
# ==========================================

day_names = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

# Create a readable day-name column
df["Day_Name"] = df["Day_of_Week"].map(day_names)

plt.figure(figsize=(10, 6))

sns.boxplot(
    data=df,
    x="Day_Name",
    y="Customer_Count",
    order=[
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]
)

plt.title("Customer Demand by Day of Week")
plt.xlabel("Day of Week")
plt.ylabel("Customer Count")

plt.tight_layout()
plt.show()
# ==========================================
# STEP 6: REMOVE TARGET LEAKAGE
# ==========================================

df = df.drop(columns=["Capacity_Utilization"])

print("\nCapacity_Utilization removed.")
print("Current dataset shape:", df.shape)

# ==========================================
# STEP 7: CREATE DEMAND_YESTERDAY
# ==========================================

df["Demand_Yesterday"] = (
    df.groupby("Location_ID")["Customer_Count"]
      .shift(1)
)

print("\nDemand_Yesterday created.")

print(
    df[
        [
            "Location_ID",
            "Date",
            "Customer_Count",
            "Demand_Yesterday"
        ]
    ].head(15)
)

# ==========================================
# STEP 8: CREATE DEMAND_7_DAYS_AGO
# ==========================================

df["Demand_7_Days_Ago"] = (
    df.groupby("Location_ID")["Customer_Count"]
      .shift(7)
)

print("\nDemand_7_Days_Ago created.")

print(
    df[
        [
            "Location_ID",
            "Date",
            "Customer_Count",
            "Demand_Yesterday",
            "Demand_7_Days_Ago"
        ]
    ].head(15)
)

# ==========================================
# STEP 9: CREATE 7-DAY MOVING AVERAGE
# ==========================================

df["Demand_MA7"] = (
    df.groupby("Location_ID")["Customer_Count"]
      .transform(
          lambda x: x.shift(1).rolling(7).mean()
      )
)

print("\nDemand_MA7 created.")

print(
    df[
        [
            "Location_ID",
            "Date",
            "Customer_Count",
            "Demand_Yesterday",
            "Demand_7_Days_Ago",
            "Demand_MA7"
        ]
    ].head(15)
)

# ==========================================
# STEP 10: CYCLICAL TIME FEATURES
# ==========================================

# Month
df["Month_sin"] = np.sin(
    2 * np.pi * df["Month"] / 12
)

df["Month_cos"] = np.cos(
    2 * np.pi * df["Month"] / 12
)

# Day of Week
df["DOW_sin"] = np.sin(
    2 * np.pi * df["Day_of_Week"] / 7
)

df["DOW_cos"] = np.cos(
    2 * np.pi * df["Day_of_Week"] / 7
)

print("\nCyclical features created.")

print(
    df[
        [
            "Date",
            "Month",
            "Day_of_Week",
            "Month_sin",
            "Month_cos",
            "DOW_sin",
            "DOW_cos"
        ]
    ].head(10)
)

# ==========================================
# STEP 11: CHECK MISSING VALUES
# ==========================================

print("\nMissing values in each column:")
print(df.isna().sum())

# ==========================================
# STEP 12: REMOVE ROWS WITH MISSING LAG VALUES
# ==========================================

df = df.dropna().reset_index(drop=True)

print("\nMissing values after cleanup:")
print(df.isna().sum())

print("\nNew dataset shape:", df.shape)

# ==========================================
# STEP 13: PREPARE MODEL FEATURES
# ==========================================

# Target variable
TARGET = "Customer_Count"

# Remove columns that should not directly enter the model
model_df = df.drop(
    columns=["Date", "Day_Name"]
).copy()

# Convert Location_ID into numerical one-hot features
model_df = pd.get_dummies(
    model_df,
    columns=["Location_ID"],
    dtype=int
)

# Separate features (X) and target (y)
X = model_df.drop(columns=[TARGET])
y = model_df[TARGET]

print("\nFeature columns:")
print(X.columns.tolist())

print("\nNumber of features:", X.shape[1])

print("\nTarget shape:", y.shape)

print("\nFirst 5 rows of X:")
print(X.head())

# ==========================================
# STEP 14: CHRONOLOGICAL TRAIN/VAL/TEST SPLIT
# ==========================================

# Get all unique dates in chronological order
dates = np.sort(df["Date"].unique())

# Calculate split points
n_dates = len(dates)

train_end = int(n_dates * 0.70)
val_end = int(n_dates * 0.85)

# Select dates for each section
train_dates = dates[:train_end]
val_dates = dates[train_end:val_end]
test_dates = dates[val_end:]

# Create masks using the original dataframe
train_mask = df["Date"].isin(train_dates)
val_mask = df["Date"].isin(val_dates)
test_mask = df["Date"].isin(test_dates)

# Split features
X_train = X.loc[train_mask]
X_val = X.loc[val_mask]
X_test = X.loc[test_mask]

# Split target
y_train = y.loc[train_mask]
y_val = y.loc[val_mask]
y_test = y.loc[test_mask]

# Print information
print("\n==========================================")
print("CHRONOLOGICAL DATA SPLIT")
print("==========================================")

print("\nTraining:")
print("Rows:", len(X_train))
print("Dates:", train_dates[0], "to", train_dates[-1])

print("\nValidation:")
print("Rows:", len(X_val))
print("Dates:", val_dates[0], "to", val_dates[-1])

print("\nTest:")
print("Rows:", len(X_test))
print("Dates:", test_dates[0], "to", test_dates[-1])

# ==========================================
# STEP 16: TRAIN BASELINE XGBOOST MODEL
# ==========================================

print("\n==========================================")
print("TRAINING BASELINE XGBOOST MODEL")
print("==========================================")

model = xgb.XGBRegressor(
    objective="count:poisson",
    eval_metric="mae",

    n_estimators=5000,

    learning_rate=0.03,
    max_depth=6,

    subsample=0.8,
    colsample_bytree=0.8,

    min_child_weight=5,

    tree_method="hist",

    early_stopping_rounds=50,

    random_state=42
)

print("\nStarting training...")

model.fit(
    X_train,
    y_train,

    eval_set=[
        (X_train, y_train),
        (X_val, y_val)
    ],

    verbose=100
)

print("\nTraining finished.")

print("Best iteration:", model.best_iteration)

# ==========================================
# STEP 17: EVALUATE BASELINE MODEL
# ==========================================

print("\n==========================================")
print("MODEL EVALUATION")
print("==========================================")

# Predictions
val_pred = model.predict(X_val)
test_pred = model.predict(X_test)

# Validation metrics
val_mae = mean_absolute_error(y_val, val_pred)
val_rmse = root_mean_squared_error(y_val, val_pred)

# Test metrics
test_mae = mean_absolute_error(y_test, test_pred)
test_rmse = root_mean_squared_error(y_test, test_pred)

print("\nValidation Performance:")
print(f"MAE  : {val_mae:.2f}")
print(f"RMSE : {val_rmse:.2f}")

print("\nTest Performance:")
print(f"MAE  : {test_mae:.2f}")
print(f"RMSE : {test_rmse:.2f}")

# ==========================================
# STEP 18: ACTUAL VS PREDICTED DEMAND
# ==========================================

plt.figure(figsize=(15, 6))

# Show first 200 test observations
plt.plot(
    y_test.values[:200],
    label="Actual Demand"
)

plt.plot(
    test_pred[:200],
    label="Predicted Demand"
)

plt.title("Actual vs Predicted Customer Demand")
plt.xlabel("Test Observation")
plt.ylabel("Customer Count")

plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()
plt.show()