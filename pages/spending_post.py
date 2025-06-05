import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import os
from sklearn.metrics import r2_score
st.set_page_config(page_title="Savings Predictor", layout="wide")
# --- Load model and scaler ---
@st.cache_resource
def load_model_scaler():
    model_path = r"ml\model_rf_savings.pkl"
    scaler_path = r"ml\scaler.pkl"
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        st.error("Model or Scaler file missing.")
        return None, None
    return joblib.load(model_path), joblib.load(scaler_path)

# --- Load test data ---
def load_test_data():
    try:
        df = pd.read_csv(r"data\external\processed\test_data.csv")
        required_cols = {"Income", "Desired_Savings_Percentage", "Disposable_Income", "Desired_Savings"}
        if required_cols.issubset(df.columns):
            return df
        else:
            st.warning("Test data missing required columns.")
            return None
    except FileNotFoundError:
        return None

# --- Classification of savings goal ---
def classify_savings(savings_pct):
    if savings_pct < 10:
        return "Low"
    elif savings_pct < 25:
        return "Moderate"
    else:
        return "High"

# --- Forecast next 6 months savings ---
def monthly_forecast(current_saving):
    # Simple linear growth assumption: 2% increase per month
    months = np.arange(1, 7)
    forecast = current_saving * (1 + 0.02 * months)
    return months, forecast

# --- Main App ---
model, scaler = load_model_scaler()
test_df = load_test_data()


st.title("💡 Personalized Savings Predictor")

# Tabs for better UI
tabs = st.tabs(["🔮 Predict", "📈 Forecast", "📊 Data & Export"])

with tabs[0]:  # Prediction tab
    st.subheader("Enter your financial details:")
    with st.form("predict_form"):
        income = st.number_input("Monthly Income (₹)", min_value=0.0, format="%.2f")
        savings_pct = st.slider("Desired Savings Percentage (%)", 0.0, 100.0, 10.0, step=0.1)
        disposable_income = st.number_input("Disposable Income (₹)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Predict Savings")

        if submitted and model and scaler:
            input_df = pd.DataFrame([{
                "Income": income,
                "Desired_Savings_Percentage": savings_pct,
                "Disposable_Income": disposable_income
            }])
            try:
                input_scaled = scaler.transform(input_df)
                prediction = model.predict(input_scaled)[0]
                st.success(f"💰 Recommended Monthly Savings: ₹{prediction:,.2f}")

                # Classification result
                goal_class = classify_savings((prediction / income) * 100 if income > 0 else 0)
                st.info(f"🏷️ Savings Goal Classification: **{goal_class}**")

                # Save prediction in session state for forecast tab
                st.session_state['latest_prediction'] = prediction

            except Exception as e:
                st.error(f"Prediction error: {e}")

with tabs[1]:  # Forecast tab
    st.subheader("Monthly Savings Forecast (Next 6 Months)")
    if 'latest_prediction' in st.session_state:
        pred = st.session_state['latest_prediction']
        months, forecast_vals = monthly_forecast(pred)

        fig, ax = plt.subplots()
        ax.plot(months, forecast_vals, marker='o', linestyle='-', color='green')
        ax.set_xlabel("Month")
        ax.set_ylabel("Predicted Savings (₹)")
        ax.set_title("6-Month Savings Forecast")
        ax.grid(True)
        ax.set_xticks(months)
        st.pyplot(fig)

        # Show forecast data as table
        forecast_df = pd.DataFrame({
            "Month": [f"Month {m}" for m in months],
            "Predicted Savings (₹)": forecast_vals.round(2)
        })
        st.dataframe(forecast_df)
    else:
        st.warning("Please make a prediction first in the 'Predict' tab.")

with tabs[2]:  # Data & Export tab
    if test_df is not None and model and scaler:
        st.subheader("Prediction vs Actual Savings")
        # Filters
        income_min, income_max = st.slider(
            "Filter by Income Range (₹)",
            float(test_df["Income"].min()),
            float(test_df["Income"].max()),
            (float(test_df["Income"].min()), float(test_df["Income"].max())),
            step=1000.0
        )
        filtered_df = test_df[(test_df["Income"] >= income_min) & (test_df["Income"] <= income_max)]

        X_test = filtered_df[["Income", "Desired_Savings_Percentage", "Disposable_Income"]]
        y_test = filtered_df["Desired_Savings"]

        try:
            X_scaled = scaler.transform(X_test)
            y_pred = model.predict(X_scaled)

            # Scatter plot
            fig, ax = plt.subplots()
            ax.scatter(y_test, y_pred, alpha=0.5, color='skyblue', edgecolors='k')
            ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
            ax.set_xlabel("Actual Savings")
            ax.set_ylabel("Predicted Savings")
            ax.set_title("Prediction vs Actual Savings")
            st.pyplot(fig)

            # R2 Score
            r2 = r2_score(y_test, y_pred)
            st.markdown(f"**R² Score:** {r2:.4f}")

            # Export button
            if st.button("Export Filtered Predictions to CSV"):
                export_df = X_test.copy()
                export_df["Actual_Savings"] = y_test
                export_df["Predicted_Savings"] = y_pred
                os.makedirs("exports", exist_ok=True)
                export_path = r"data\exports\predicted_savings_filtered.csv"
                export_df.to_csv(export_path, index=False)
                

            # Show filtered dataframe
            st.subheader("Filtered Test Data with Predictions")
            display_df = export_df.copy()
            display_df["Predicted_Savings"] = y_pred.round(2)
            st.dataframe(display_df.reset_index(drop=True), height=300)

        except Exception as e:
            pass

    else:
        st.warning("Test data not found or model/scaler not loaded.")

