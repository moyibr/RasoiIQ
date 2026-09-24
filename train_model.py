import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import xgboost as xgb

def preprocess_restaurant_data(file_path):
    # 1. Load the dataset
    print("Loading data...")
    df = pd.read_csv(file_path)
    
    # 2. Time-Based Sorting
    # Time-series data MUST be split chronologically. We sort by Date to ensure 
    # we train on the past to predict the future.
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by=['Location_ID', 'Date'])
    
    # 3. Categorical Encoding
    # XGBoost needs numbers. We strip "Loc_" from Location_ID and convert to integer.
    df['Location_ID'] = df['Location_ID'].str.replace('Loc_', '').astype(int)
    
    # 4. Target Definition & Data Leakage Removal
    # Capacity_Utilization is calculated using Customer_Count. Keeping it is data leakage.
    target_col = 'Customer_Count'
    leakage_col = 'Capacity_Utilization'
    
    # XGBoost cannot natively handle datetime objects, so we drop the Date column 
    # (we already have Day_of_Week, Month, etc. capturing the temporal patterns).
    cols_to_drop = ['Date', leakage_col]
    
    # Separate Features (X) and Target (y)
    y = df[target_col]
    X = df.drop(columns=[target_col] + cols_to_drop)
    
    # 5. Temporal Train-Test Split
    # We do NOT use random split (shuffle=True) because predicting yesterday 
    # using tomorrow's data is cheating. We take the first 80% of time as train.
    split_idx = int(len(df) * 0.8)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"Data ready. Training rows: {len(X_train)} | Testing rows: {len(X_test)}")
    return X_train, X_test, y_train, y_test

# =============================================================
# EXECUTION & XGBOOST SETUP
# =============================================================
if __name__ == "__main__":
    # Point this to your generated CSV file
    file_name = "restaurant_demand_28k.csv"
    
    # Run the preprocessing pipeline
    X_train, X_test, y_train, y_test = preprocess_restaurant_data(file_name)
    
    # Optional: Train a baseline XGBoost model immediately
    print("\nTraining baseline XGBoost Regressor...")
    model = xgb.XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective='count:poisson' # Highly effective for count data like foot traffic
    )
    
    # Fit the model and evaluate on the test set to prevent overfitting
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        early_stopping_rounds=20,
        verbose=50
    )
    
    # Check baseline performance
    from sklearn.metrics import mean_absolute_error
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    print(f"\nBaseline Mean Absolute Error (MAE): {mae:.2f} customers")