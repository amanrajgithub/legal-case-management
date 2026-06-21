import streamlit as st
from auth import google_login
from access_control import check_access
from dashboard import show_dashboard

st.set_page_config(page_title="Legal Case Management", layout="wide")
st.title("Legal Case Management - Secure Login")

def logout():
    if "token" in st.session_state:
        del st.session_state["token"]
    st.success("You have been logged out.")
    st.experimental_rerun()

auth_url, userinfo = google_login()

if auth_url:
    st.write("Redirecting to Google login…")
elif userinfo:
    user_email = userinfo["email"]
    if check_access(user_email):
        show_dashboard(user_email)
    else:
        st.error("Access denied. Please contact admin to be added to the AuthorizedUsers sheet.")

    # Always show logout option
    if st.button("🚪 Logout"):
        logout()
