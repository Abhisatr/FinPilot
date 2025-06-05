import streamlit as st
from supabase_client import supabase

def login():
    st.subheader("🔐 Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    
    if st.button("Login"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.user:
                st.session_state["user"] = {
                    "id": res.user.id,
                    "email": res.user.email
                }
                st.success("✅ Login successful")
                st.switch_page("main.py")
            else:
                st.error("Invalid credentials")
        except Exception as e:
            st.error(f"❌ Login failed: {e}")

def signup():
    st.subheader("📝 Sign Up")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_pass")
    
    if st.button("Sign Up"):
        try:
            res = supabase.auth.sign_up({"email": email, "password": password})
            if res.user:
                st.success("✅ Signup successful. Check your email.")
                st.switch_page("pages/auth.py")
                st.rerun()

        except Exception as e:
            st.error(f"❌ Signup failed: {e}")

auth_mode = st.radio("Choose an option", ["Login", "Sign Up"])
login() if auth_mode == "Login" else signup()
