import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

scaler = StandardScaler()

print(os.getcwd()) 

# Load and preprocess data
df = pd.read_csv(r'data\external\data.csv')

# One-Hot encode 'Occupation' and 'City_Tier'
df = pd.get_dummies(df, columns=['Occupation', 'City_Tier'], drop_first=True)
print(df.head())

# Split features and target
X = df.drop('Desired_Savings', axis=1)
y = df['Desired_Savings']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training samples: {X_train.shape[0]}")
print(f"Test samples: {X_test.shape[0]}")

# Scale all features initially
X_train_scaled_all = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
X_test_scaled_all = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

# Initial model training for feature importance
model_initial = RandomForestRegressor(random_state=42)
model_initial.fit(X_train_scaled_all, y_train)

# Extract feature importances
importances = model_initial.feature_importances_
feat_names = X_train.columns

# Filter features above importance threshold
threshold = 0.01
filtered_indices = np.where(importances >= threshold)[0]
sorted_filtered_indices = filtered_indices[np.argsort(importances[filtered_indices])[::-1]]
selected_features = feat_names[sorted_filtered_indices]

# Display selected features
print("\nSelected important features:")
for feat in selected_features:
    print(f"{feat}: {importances[feat_names.get_loc(feat)]:.4f}")

# Scale only selected features
X_train_filtered = X_train[selected_features]
X_test_filtered = X_test[selected_features]

X_train_filtered_scaled = pd.DataFrame(scaler.fit_transform(X_train_filtered), columns=selected_features)
X_test_filtered_scaled = pd.DataFrame(scaler.transform(X_test_filtered), columns=selected_features)

# Retrain model on important features
model_final = RandomForestRegressor(random_state=42)
model_final.fit(X_train_filtered_scaled, y_train)

# Evaluate model
y_pred = model_final.predict(X_test_filtered_scaled)

mse = root_mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\nFinal Model Metrics (Important Features Only):")
print(f"Mean Squared Error: {mse:.2f}")
print(f"R2 Score: {r2:.2f}")

# Plot feature importances (filtered only)
sorted_importances = importances[sorted_filtered_indices]
plt.figure(figsize=(10, 6))
plt.title(f"Feature Importances (>{threshold})")
plt.bar(range(len(selected_features)), sorted_importances, align='center')
plt.xticks(range(len(selected_features)), selected_features, rotation=45, ha='right')
plt.tight_layout()
plt.show()

import joblib

joblib.dump(model_final, r"ml\model_rf_savings.pkl")
joblib.dump(scaler, r"ml\scaler.pkl")

# Optionally save test data for later use in visualization
X_test["Desired_Savings"] = y_test
X_test.to_csv(r"data\external\processed\test_data.csv", index=False)
