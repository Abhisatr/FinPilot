import streamlit as st
import pandas as pd
import json
from datetime import datetime
from supabase_client import supabase
from auth_helpers import require_auth, get_current_user
import plotly.express as px

require_auth()
user = get_current_user()
user_id = user["id"]

st.title("📊 Monthly Analysis & Insights")

def get_current_month():
    return datetime.now().strftime("%Y-%m")

def fetch_income():
    resp = supabase.table("user_incomes").select("*").eq("user_id", user_id).limit(1).execute()
    return resp.data[0]["amount"] if resp.data else 0.0

def fetch_budget(month):
    resp = supabase.table("user_budgets").select("*").eq("user_id", user_id).eq("month", month).limit(1).execute()
    return json.loads(resp.data[0]["budget_json"]) if resp.data else {}

def fetch_expenses(month):
    # Prepare date range from month for filtering by created_at
    from datetime import datetime, timedelta
    year, month_num = map(int, month.split('-'))
    first_day = datetime(year, month_num, 1)
    # Calculate last day of month
    if month_num == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month_num + 1, 1) - timedelta(days=1)

    resp = supabase.table("expenses") \
        .select("*") \
        .eq("user_id", user_id) \
        .gte("created_at", first_day.isoformat()) \
        .lte("created_at", last_day.isoformat()) \
        .execute()

    error = getattr(resp, 'error', None)
    if error:
        print("Error fetching expenses:", error)
        return []

    data = getattr(resp, 'data', None)
    if data is None:
        print("No data found")
        return []

    return data


def fetch_savings(month):
    resp = supabase.table("monthly_savings").select("*").eq("user_id", user_id).eq("month", month).limit(1).execute()
    return resp.data[0]["amount"] if resp.data else 0.0

# ---- Data Fetch ----
month = get_current_month()
income = fetch_income()
budget = fetch_budget(month)
expenses = fetch_expenses(month)
savings = fetch_savings(month)

# ---- Processing ----
category_totals = {}
total_expense = 0

for entry in expenses:
    cat = entry["category"]
    amt = entry["amount"]
    category_totals[cat] = category_totals.get(cat, 0) + amt
    total_expense += amt

# ---- Section: Summary ----
st.subheader("💡 Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Income", f"₹{income:,.2f}")
col2.metric("Total Spent", f"₹{total_expense:,.2f}")
col3.metric("Savings", f"₹{savings:,.2f}")

# ---- Section: Budget vs Actual Bar Chart ----
if budget and category_totals:
    st.subheader("📌 Budget vs Actual Spending")

    comparison_data = []
    for cat in budget:
        if cat == "Savings":
            continue
        planned_pct = budget[cat]
        planned_amt = round(income * (planned_pct / 100), 2)
        actual_amt = category_totals.get(cat, 0.0)
        comparison_data.append({
            "Category": cat,
            "Budgeted": planned_amt,
            "Spent": actual_amt
        })

    df_compare = pd.DataFrame(comparison_data)

    fig = px.bar(df_compare, x="Category", y=["Budgeted", "Spent"], barmode="group", title="Budget vs Actual")
    st.plotly_chart(fig, use_container_width=True)

# ---- Section: Overspending Alerts ----
overspent = []
for cat in budget:
    if cat == "Savings":
        continue
    expected = income * (budget[cat] / 100)
    actual = category_totals.get(cat, 0)
    if actual > expected:
        overspent.append((cat, actual - expected))

if overspent:
    st.subheader("🚨 Overspending Detected")
    for cat, extra in overspent:
        st.error(f"⚠️ {cat}: Overspent by ₹{extra:.2f}")

# ---- Section: Expense Distribution Pie Chart ----
if category_totals:
    st.subheader("🍕 Expense Distribution by Category")
    pie_data = pd.DataFrame({
        "Category": list(category_totals.keys()),
        "Amount": list(category_totals.values())
    })
    pie = px.pie(pie_data, names="Category", values="Amount", title="Expenses by Category")
    st.plotly_chart(pie, use_container_width=True)

# ---- Section: Monthly Savings History ----
def fetch_savings_history():
    resp = supabase.table("monthly_savings").select("*").eq("user_id", user_id).order("month", desc=False).execute()
    return resp.data if resp.data else []

savings_data = fetch_savings_history()
if savings_data:
    st.subheader("📈 Monthly Savings Trend")
    df_savings = pd.DataFrame(savings_data)
    df_savings["month"] = pd.to_datetime(df_savings["month"])
    fig2 = px.line(df_savings, x="month", y="amount", markers=True, title="Savings Over Time")
    st.plotly_chart(fig2, use_container_width=True)
