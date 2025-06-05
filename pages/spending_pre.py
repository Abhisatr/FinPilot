import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt

st.set_page_config(page_title="Spending Predictor", layout="centered")

st.title("🧠 Spending Prediction")
st.write("Enter your details to get a personalized spending estimate and compare it to the average.")

# 📥 User Input Form
with st.form("user_input"):
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    education = st.selectbox("Education", ["High School", "Graduate", "Post-Graduate"])
    country = st.selectbox("Country", ["India", "USA", "UK", "Other"])
    age = st.number_input("Age", min_value=18, max_value=100)
    income = st.number_input("Monthly Income (₹)", min_value=0.0)
    purchase_frequency = st.number_input("Average Purchases per Month", min_value=0)

    submit = st.form_submit_button("Predict Spending")

# 🧠 Load Model and Predict
if submit:
    try:
        with open("ml/spending_model.pkl", "rb") as f:
                model, encoder, num_cols = pickle.load(f)
                cat_cols = ["gender", "education", "country"]
                
        user_df = pd.DataFrame([{
            "gender": gender,
            "education": education,
            "country": country,
            "age": age,
            "income": income,
            "purchase_frequency": purchase_frequency
        }])

        # Encode + Combine
        X_cat = encoder.transform(user_df[cat_cols])
        X_num = user_df[num_cols].values
        X_final = np.hstack([X_cat, X_num])

        # Predict
        predicted_spending = model.predict(X_final)[0]
        st.success(f"🎯 Predicted Monthly Spending: ₹{predicted_spending:.2f}")

        # 🎯 Goal-based recommendation
        suggested_goal = 0.5 * income  # Example rule: save 50%
        if predicted_spending > suggested_goal:
            st.warning("⚠️ Your spending exceeds the suggested limit (50% of income).")
        else:
            st.info("✅ Your spending is within a healthy range.")

        # 📊 Compare with average (mock values for demo)
        avg_data = {
            "You": predicted_spending,
            "Avg Public": income * 0.6  # Mock comparison (60% of income)
        }

        fig, ax = plt.subplots()
        ax.bar(avg_data.keys(), avg_data.values(), color=["blue", "gray"])
        ax.set_ylabel("Monthly Spending (₹)")
        ax.set_title("Your Spending vs Average")
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Error: {e}")
