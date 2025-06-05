import streamlit as st
from supabase_client import supabase
from auth_helpers import require_auth, get_current_user
from datetime import datetime

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

def update_total_savings(user_id):
    response = supabase.table("monthly_savings").select("amount").eq("user_id", user_id).execute()
    if not response.data:
        total = 0
    else:
        total = sum(item["amount"] for item in response.data)

    supabase.table("user_profile").update({"total_savings": total}).eq("user_id", user_id).execute()
    return total

def create_user_profile(user_id):
    default_profile = {
        "user_id": user_id,
        "name": "",
        "age": 20,
        "country": "India",
        "total_savings": update_total_savings(user_id),
        "savings_goal_per_year": 0
    }
    res = supabase.table("user_profile").insert(default_profile).execute()
    data = res.data
    if data and len(data) > 0:
        return data[0]
    else:
        return None

def update_user_profile(user_id, name, age, country, savings_goal_per_year):
    res = supabase.table("user_profile").update({
        "name": name,
        "age": age,
        "country": country,
        "savings_goal_per_year": savings_goal_per_year,
        "total_savings": update_total_savings(user_id)
    }).eq("user_id", user_id).execute()

    data = res.data
    if data and len(data) > 0:
        return True
    else:
        return False

def get_current_year_savings_progress(user_id):
    current_year = datetime.now().year
    response = supabase.table("monthly_savings").select("*").eq("user_id", user_id).execute()
    if not response.data:
        return 0, 0, 0

    year_savings = 0
    for entry in response.data:
        timestamp = entry.get("created_at") or entry.get("date")
        if timestamp:
            entry_year = datetime.fromisoformat(timestamp[:10]).year
            if entry_year == current_year:
                year_savings += entry.get("amount", 0)

    profile = get_user_profile(user_id)
    goal = profile.get("savings_goal_per_year", 0) if profile else 0
    completion_rate = (year_savings / goal) if goal else 0
    return year_savings, goal, completion_rate

def main():
    require_auth()
    user = get_current_user()
    user_id = user["id"]

    profile = get_user_profile(user_id)
    if not profile:
        profile = create_user_profile(user_id)
        if not profile:
            st.stop()

    st.title("Your Profile")

    st.write(f"**Total Savings (All Time):** ₹{profile.get('total_savings', 0):,.2f}")

    year_savings, goal, completion_rate = get_current_year_savings_progress(user_id)
    st.write(f"**Current Year Savings:** ₹{year_savings:,.2f} / ₹{goal:,.2f}")
    st.progress(min(completion_rate, 1.0))

    name = st.text_input("Name", value=profile.get("name", ""))
    age = st.number_input("Age", value=profile.get("age", 20), min_value=0, max_value=120, step=1)
    country = st.text_input("Country", value=profile.get("country", ""))
    savings_goal_per_year = st.number_input("Savings Goal (per year)", value=profile.get("savings_goal_per_year", 0), min_value=0)

    if st.button("Save Profile / Update"):
        if update_user_profile(user_id, name, age, country, savings_goal_per_year):
            st.success("Profile updated successfully!")
            st.rerun()
        else:
            st.error("Failed to update profile.")

if __name__ == "__main__":
    main()
