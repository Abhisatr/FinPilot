import streamlit as st

def get_current_user():
    return st.session_state.get("user")

def require_auth():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.switch_page("pages/auth.py")
