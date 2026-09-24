import pandas as pd
import numpy as np

def generate_single_location_data(loc_id, start_date="2023-01-01", days=1095, base_demand=200, capacity=400, seed=42):
    """Generates a realistic, production-ready dataset for a SINGLE restaurant location."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start=start_date, periods=days, freq="D")
    df = pd.DataFrame({"Date": dates})
    
    # 1. TEMPORAL & HOLIDAY FEATURES
    df["Day_of_Week"] = df["Date"].dt.dayofweek
    df["Month"] = df["Date"].dt.month
    df["Day_of_Year"] = df["Date"].dt.dayofyear
    df["Is_Weekend"] = (df["Day_of_Week"] >= 5).astype(int)
    df["Annual_Seasonality"] = 1 + 0.08 * np.sin(2 * np.pi * df["Day_of_Year"] / 365.25)
    
    df["Is_Holiday"] = 0
    holiday_dates = []
    for year in df["Date"].dt.year.unique():
        holiday_dates.extend([
            pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-02-14"), 
            pd.Timestamp(f"{year}-07-04"), pd.Timestamp(f"{year}-10-31"), 
            pd.Timestamp(f"{year}-12-25")
        ])
    df.loc[df["Date"].isin(holiday_dates), "Is_Holiday"] = 1

    # 2. WEATHER (HURDLE MODEL)
    day_index = np.arange(days)
    seasonal_temp = 25 + 8 * np.sin(2 * np.pi * day_index / 365.25)
    df["Temp_Celsius"] = np.clip(seasonal_temp + rng.normal(0, 2.5, days), 10, 42)
    
    rain_prob = np.clip(0.15 + 0.20 * np.sin(2 * np.pi * (day_index - 150) / 365.25), 0.05, 0.60)
    is_raining = rng.random(days) < rain_prob
    df["Rain_mm"] = np.where(is_raining, rng.gamma(shape=2.0, scale=8.0, size=days), 0)
    df["Rain_mm"] = df["Rain_mm"].clip(0, 100)

    # 3. CONTEXTUAL & MACRO FEATURES
    df["Local_Event"] = (rng.random(days) < 0.05).astype(int)
    df["Active_Promotion"] = (rng.random(days) < 0.15).astype(int)
    df["Competitor_Promo"] = (rng.random(days) < 0.10).astype(int)
    df["CPI_Index"] = 100 + np.linspace(0, 10, days) + rng.normal(0, 0.3, days)
    
    # Ratings: Ornstein-Uhlenbeck Process
    mu, theta, sigma = 4.2, 0.05, 0.02
    ratings = [4.2]
    for _ in range(1, days):
        dr = theta * (mu - ratings[-1]) + rng.normal(0, sigma)
        ratings.append(np.clip(ratings[-1] + dr, 3.5, 4.9))
    df["Online_Rating"] = ratings

    # 4. LOG-LINEAR DEMAND CALCULATION
    log_demand = np.full(days, np.log(base_demand))
    log_weekly = np.log([0.90, 0.92, 0.96, 1.00, 1.12, 1.35, 1.25])
    log_demand += log_weekly[df["Day_of_Week"].values]
    
    log_demand += np.where(df["Is_Holiday"] == 1, np.log(1.35), 0)
    log_demand += np.where(df["Local_Event"] == 1, np.log(1.20), 0)
    log_demand += np.where(df["Active_Promotion"] == 1, np.log(1.15), 0)
    log_demand += np.where(df["Competitor_Promo"] == 1, np.log(0.92), 0)
    
    log_demand -= 0.002 * ((df["Temp_Celsius"] - 25) ** 2)
    log_demand -= 0.015 * df["Rain_mm"]
    
    expected_demand_linear = np.exp(log_demand) * df["Annual_Seasonality"]

    # 5. RESERVATIONS 
    reservation_rate = 0.18 + (0.08 * df["Is_Weekend"]) + (0.05 * df["Is_Holiday"])
    df["Reservations"] = rng.poisson(expected_demand_linear * reservation_rate)

    # 6. AUTOREGRESSIVE MOMENTUM
    final_expected = np.zeros(days)
    final_expected[0] = expected_demand_linear.iloc[0]
    for i in range(1, days):
        final_expected[i] = (0.75 * expected_demand_linear.iloc[i]) + (0.25 * final_expected[i - 1])

    # 7. NEGATIVE BINOMIAL NOISE & CAPACITY
    dispersion = 20
    p = dispersion / (dispersion + final_expected)
    customer_count = rng.negative_binomial(dispersion, p)
    
    customer_count = np.minimum(customer_count, capacity)
    customer_count = np.maximum(customer_count, df["Reservations"])
    
    df["Customer_Count"] = customer_count.astype(int)
    df["Capacity_Utilization"] = (df["Customer_Count"] / capacity).round(3)
    
    # Add Location ID to distinguish restaurants in the final big dataset
    df.insert(0, 'Location_ID', f"Loc_{loc_id}")

    return df

def generate_franchise_dataset(num_locations=26, days_per_location=1095):
    """Loops through and generates data for multiple restaurant locations."""
    print(f"Generating data for {num_locations} locations over {days_per_location} days...")
    all_locations_data = []
    
    master_rng = np.random.default_rng(99)
    
    for loc in range(1, num_locations + 1):
        unique_base_demand = master_rng.integers(100, 500) 
        unique_capacity = unique_base_demand + master_rng.integers(50, 200)
        unique_seed = master_rng.integers(1, 999999)
        
        loc_df = generate_single_location_data(
            loc_id=loc, 
            days=days_per_location, 
            base_demand=unique_base_demand, 
            capacity=unique_capacity,
            seed=unique_seed
        )
        all_locations_data.append(loc_df)
        
        if loc % 10 == 0 or loc == num_locations:
            print(f"  ... {loc} locations generated.")
            
    final_dataset = pd.concat(all_locations_data, ignore_index=True)
    return final_dataset

# =============================================================
# RUN THE SCRIPT
# =============================================================
if __name__ == "__main__":
    # Generates ~28k rows by simulating 26 locations over 3 years (1095 days)
    franchise_data = generate_franchise_dataset(num_locations=26, days_per_location=1095)
    
    print("\nDataset Generation Complete!")
    print(f"Total Rows: {len(franchise_data)}")
    print(f"Total Columns: {len(franchise_data.columns)}")
    
    file_name = "restaurant_demand_28k.csv"
    franchise_data.to_csv(file_name, index=False)
    print(f"\nSaved successfully to your current folder as: '{file_name}'")