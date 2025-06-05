import streamlit as st
import json
from datetime import datetime
from supabase_client import supabase
from auth_helpers import require_auth, get_current_user

require_auth()
user = get_current_user()
user_id = user["id"]

st.title("💰 Income & Budget")

def get_current_month():
    return datetime.now().strftime("%Y-%m")

def fetch_income():
    resp = supabase.table("user_incomes").select("*").eq("user_id", user_id).limit(1).execute()
    return resp.data[0] if resp.data else None

def fetch_budget_record():
    # Get latest budget for user, ordered by month descending (latest first)
    resp = supabase.table("user_budgets") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("month", desc=True) \
        .limit(1) \
        .execute()
    return resp

def upsert_income(amount):
    supabase.table("user_incomes") \
        .upsert({"user_id": user_id, "amount": amount}, on_conflict="user_id") \
        .execute()

def upsert_budget(budget):
    supabase.table("user_budgets").upsert(
    {
        "user_id": user_id,
        "budget_json": json.dumps(budget),
        "month": get_current_month()
    },
    on_conflict="user_id,month"  # ✅ correct format
).execute()




def insert_savings_full_income(income):
    month = get_current_month()
    existing = supabase.table("monthly_savings") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("month", month) \
        .execute()

    if not existing.data:
        supabase.table("monthly_savings").insert({
            "user_id": user_id,
            "month": month,
            "amount": income,
            "recorded_on": datetime.now().date().isoformat()
        }).execute()

# -------- Income Section --------
income_data = fetch_income()
income = income_data["amount"] if income_data else 0.0

income = st.number_input("Monthly Income", value=income, min_value=0.0, step=0.01)

if st.button("Save Income"):
    upsert_income(income)
    st.success("Income saved")

if income <= 0:
    st.info("Please enter income first.")
    st.stop()

# -------- Budget Section --------
categories = ["Housing", "Food", "Transport", "Entertainment", "Health", "Others"]
budget_resp = fetch_budget_record()

reuse_old = False
existing_budget = {}

if budget_resp.data:
    latest_record = budget_resp.data[0]
    existing_budget = json.loads(latest_record["budget_json"])
    saved_month = latest_record.get("month")

    if saved_month != get_current_month():
        reuse_old = st.radio("It's a new month. Reuse last month's budget?", ["Yes", "No"]) == "Yes"
    else:
        reuse_old = True

new_budget = {}
total = 0

st.subheader("🧮 Budget Allocation (%)")
for cat in categories:
    default = existing_budget.get(cat, 0.0) if reuse_old else 0.0
    percent = st.number_input(cat, min_value=0.0, max_value=100.0, step=0.1, value=default)
    new_budget[cat] = percent
    total += percent

if total > 100:
    st.error("Total budget exceeds 100%. Please adjust the values.")
else:
    new_budget["Savings"] = round(100 - total, 2)
    st.write(f"**Savings will be set to:** {new_budget['Savings']}%")

    if st.button("Save Budget"):
        upsert_budget(new_budget)
        insert_savings_full_income(income)
        st.success("Budget and initial savings recorded for the month.")
