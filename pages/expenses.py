import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from supabase_client import supabase
from auth_helpers import require_auth, get_current_user
import json

require_auth()
user = get_current_user()
user_id = user["id"]

st.title("🧾 Expense Tracker & Monthly Savings")

# ---------- Helpers (existing ones here) ----------

def get_current_month():
    return datetime.now().strftime("%Y-%m")

def get_month_range():
    now = datetime.now()
    start = now.replace(day=1)
    end = (start + relativedelta(months=1)) - relativedelta(days=1)
    return start.isoformat(), end.isoformat()

# ... (other existing helpers like fetch_income(), fetch_budget(), fetch_expenses(), insert_expense(), update_monthly_savings(), calculate_remaining())

# ---------- Main Logic (existing code) ----------
def fetch_income():
    resp = supabase.table("user_incomes").select("amount").eq("user_id", user_id).limit(1).execute()
    return float(resp.data[0]["amount"]) if resp.data else 0.0

def fetch_budget():
    resp = supabase.table("user_budgets").select("budget_json").eq("user_id", user_id).limit(1).execute()
    if not resp.data:
        return {}
    try:
        return json.loads(resp.data[0]["budget_json"])
    except:
        return {}

def fetch_expenses(month_only=True):
    query = supabase.table("expenses").select("*").eq("user_id", user_id)
    if month_only:
        start, end = get_month_range()
        query = query.gte("created_at", start).lte("created_at", end)
    resp = query.order("created_at", desc=True).execute()
    return resp.data if resp.data else []

def insert_expense(category, amount, note):
    supabase.table("expenses").insert({
        "user_id": user_id,
        "category": category,
        "amount": amount,
        "note": note,
    }).execute()

def update_monthly_savings():
    expenses = fetch_expenses()
    total_spent = sum(e["amount"] for e in expenses)
    income = fetch_income()
    savings = income - total_spent
    if income == 0:
        return

    current_month = get_current_month()
    entry = {
        "user_id": user_id,
        "month": current_month,
        "amount": round(savings, 2),
        "recorded_on": datetime.now().date().isoformat()
    }

    existing = supabase.table("monthly_savings") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("month", current_month) \
        .limit(1) \
        .execute()

    if existing.data:
        supabase.table("monthly_savings").update(entry).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("monthly_savings").insert(entry).execute()

def calculate_remaining(budget, income, expenses_df, category):
    if category not in budget or income <= 0:
        return 0.0, 0.0
    allocated = (budget[category] / 100.0) * income
    used = expenses_df[expenses_df["category"] == category]["amount"].sum() if not expenses_df.empty else 0.0
    remaining = allocated - used
    return allocated, remaining



income = fetch_income()
budget = fetch_budget()


if not budget or income <= 0:
    st.warning("⚠️ You need to set your income and budget before adding expenses.")
    if st.button("Go to Budget Setup"):
        st.switch_page("pages/income_budget.py")
    st.stop()

expenses = fetch_expenses()

df = pd.DataFrame(expenses) if expenses else pd.DataFrame(columns=["category", "amount", "note", "created_at"])

# Update monthly savings based on current expenses and income
update_monthly_savings()

# ---------- Add New Expense ----------

with st.expander("➕ Add New Expense"):
    category = st.selectbox("Category", list(budget.keys()))
    amount = st.number_input("Amount", min_value=0.01, step=0.01)
    note = st.text_area("Note (optional)")

    allocated, remaining = calculate_remaining(budget, income, df, category)
    st.info(f"💡 Remaining budget for '{category}': ₹{remaining:.2f} out of ₹{allocated:.2f} ({budget[category]}%)")

    if st.button("Add Expense"):
        if amount > remaining:
            st.error("🚫 This expense exceeds your budget allocation for this category!")
        else:
            insert_expense(category, amount, note)
            st.success(f"✅ Added ₹{amount:.2f} to {category}.")
            st.rerun()

# ---------- Display Expenses ----------

st.subheader(f"📜 Expenses for {get_current_month()}")

if not df.empty:
    df["created_at"] = pd.to_datetime(df["created_at"], infer_datetime_format=True, errors='coerce')
    df.rename(columns={"created_at": "date"}, inplace=True)
    st.dataframe(df[["category", "amount", "note", "date"]].sort_values("date", ascending=False))
else:
    st.info("No expenses found for this month.")


