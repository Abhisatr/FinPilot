import streamlit as st
import requests
import json
import os
import re
from dotenv import load_dotenv
import plotly.graph_objs as go
from auth_helpers import require_auth, get_current_user
from pages.expenses import fetch_income, fetch_budget, fetch_expenses
from supabase_client import supabase


    
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_user_profile(user_id):
    try:
        res = supabase.table("user_profile").select("*").eq("user_id", user_id).execute()
        data = res.data
        if data and len(data) > 0:
            return data[0]
        else:
            return None
    except Exception:
        st.write("excetion no profile data")
        return None

def format_user_data_for_prompt(income, budget, expenses, profile):
    from collections import defaultdict
    import datetime

    formatted = f"📊 User Monthly Income: ₹{income:.2f}\n\n"
    formatted += "📁 Planned Budget Allocation (in %):\n"
    for category, percent in budget.items():
        formatted += f"- {category}: {percent}%\n"
    formatted += "\n"

    category_totals = defaultdict(float)
    for expense in expenses:
        category_totals[expense["category"]] += expense["amount"]

    formatted += "💸 Expenses This Month:\n"
    for cat, amt in category_totals.items():
        formatted += f"- {cat}: ₹{amt:.2f}\n"

    formatted += "\n🧾 Recent Expense Entries (up to 5 shown):\n"
    for exp in expenses[:5]:
        date = datetime.datetime.fromisoformat(exp["created_at"]).strftime("%Y-%m-%d")
        formatted += f"- {exp['category']}: ₹{exp['amount']} on {date} | Note: {exp['note'] or 'N/A'}\n"

    # Add profile info
    formatted += "\n👤 User Profile Info:\n"
    formatted += f"- Current Age: {profile.get('age', 'N/A')}\n"
    formatted += f"- Planned Retirement Age: {profile.get('retirement_age', 'N/A')}\n"
    formatted += f"- Total Savings So Far: ₹{profile.get('total_savings', 0):.2f}\n"
    formatted += f"- Annual Savings Goal: ₹{profile.get('savings_goal_per_year', 0):.2f}\n"

    return formatted

def get_budget_suggestions(user_data):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-site.streamlit.app",
        "X-Title": "FinPilot Suggestions Page"
    }

    prompt = f"""
You are a financial AI. Based on the user's income, budget, expenses, and profile, return a JSON object with the following keys:

1. "suggested_budget" (dictionary with category: percent allocation)
2. "retirement_forecast" (list of [age, amount] points representing savings forecast until retirement)
3. "retirement_threat_level" (a string describing the risk/threat to the user's retirement, e.g., 'Low', 'Moderate', 'High')
4. "five_year_goal_plan" (list of objects with "year" and "target_savings" indicating annual savings goals for the next five years to reduce retirement threat)

User Data:
{user_data}

Respond ONLY with valid JSON inside triple backticks like ```json ... ```
"""

    payload = {
        "model": "meta-llama/llama-4-maverick:free",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        json_text = response.json()["choices"][0]["message"]["content"]

        cleaned = re.sub(r"```json|```", "", json_text).strip()
        return json.loads(cleaned)

    except Exception as e:
        return {"error": str(e)}
def main():
    require_auth()
    user = get_current_user()
    user_id = user["id"]
    
    # Try to fetch user profile (may return None)
    profile = get_user_profile(user_id)

    st.title("🧠 AI-Powered Financial Suggestions")

    with st.spinner("Loading financial data..."):
        income = fetch_income()
        budget = fetch_budget()
        expenses = fetch_expenses()

    if not profile:
        st.warning("⚠️ No profile found. Please complete your profile first in the 'Profile' page.")
        st.stop()

    user_data = format_user_data_for_prompt(income, budget, expenses, profile)
    st.subheader("📄 Your Financial Summary")
    st.code(user_data, language="markdown")

    if st.button("💡 Generate Smart Suggestions"):
        with st.spinner("Thinking..."):
            result = get_budget_suggestions(user_data)

        if "error" in result:
            st.error(f"❌ Error fetching suggestions: {result['error']}")
            return

        st.subheader("📊 Suggested Budget Allocation")
        budget_labels = list(result["suggested_budget"].keys())
        budget_values = list(result["suggested_budget"].values())
        pie = go.Figure(data=[go.Pie(labels=budget_labels, values=budget_values, hole=0.3)])
        st.plotly_chart(pie, use_container_width=True)

        st.subheader("📈 Retirement Savings Forecast")
        forecast = result["retirement_forecast"]
        ages = [pt[0] for pt in forecast]
        amounts = [pt[1] for pt in forecast]
        line = go.Figure()
        line.add_trace(go.Scatter(x=ages, y=amounts, mode="lines+markers", name="Savings"))
        line.update_layout(xaxis_title="Age", yaxis_title="₹ Savings", template="plotly_white")
        st.plotly_chart(line, use_container_width=True)

        st.subheader("⚠️ Retirement Threat Level")
        st.info(result.get("retirement_threat_level", "No data available"))

        st.subheader("🎯 Five Year Savings Goal Plan")
        goal_plan = result.get("five_year_goal_plan", [])
        for year_goal in goal_plan:
            st.write(f"- Year {year_goal['year']}: Target Savings ₹{year_goal['target_savings']:.2f}")

if __name__ == "__main__":
    main()
