import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import root_mean_squared_error, r2_score
import numpy as np
import pickle
import os

# Load data
data_path = os.path.join("finpilot", "data", "external", "customer_data.csv")
df = pd.read_csv(data_path)

# Separate features and target
X = df.drop(columns=["name", "spending"])
y = df["spending"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Separate categorical and numerical columns
cat_cols = ["gender", "education", "country"]
num_cols = ["age", "income", "purchase_frequency"]

# One-hot encode categorical features
encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
X_train_cat = encoder.fit_transform(X_train[cat_cols])
X_test_cat = encoder.transform(X_test[cat_cols])

# Combine with numerical features
X_train_full = np.hstack([X_train_cat, X_train[num_cols].values])
X_test_full = np.hstack([X_test_cat, X_test[num_cols].values])

# Train model
model = RandomForestRegressor(random_state=42)
model.fit(X_train_full, y_train)

# Predict
y_pred = model.predict(X_test_full)
rmse = root_mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("Model trained")
print(f" RMSE: {rmse:.2f}")
print(f" R2 Score: {r2:.2f}")

# Save both model and encoder
with open(os.path.join("finpilot", "ml", "spending_model.pkl"), "wb") as f:
    pickle.dump((model, encoder, num_cols), f)

print("Model and encoder saved to spending_model.pkl")
