import streamlit as st
from auth_helpers import require_auth, get_current_user
from pages.profile import get_user_profile
from supabase_client import supabase

require_auth()
user = get_current_user()
user_id = user["id"]


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

profile = get_user_profile(user_id)

# Sidebar logo
with st.sidebar:
    st.image("assets/FinPilot.png.jpeg", width=150)


st.title(f"👋 Welcome {user['email']}")

if profile==None:
    st.warning("USER PROFILE NOT SET")
    if st.button("Set Profile"):
        st.switch_page("pages/profile.py")

st.page_link("pages/income_budget.py", label="💰 Income & Budget Setup", icon="💵")
st.page_link("pages/expenses.py", label="🧾 Expense Tracker", icon="🧾")
st.page_link("pages/analysis.py", label="📊 Budget Analysis", icon="📈")

if st.button("Logout"):
    del st.session_state["user"]
    st.success("Logged out successfully")
    st.switch_page("pages/auth.py")
