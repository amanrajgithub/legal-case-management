import streamlit as st
from auth import google_login
from access_control import check_access
from dashboard import show_dashboard

st.set_page_config(page_title="Legal Case Management", layout="wide")
st.title("Legal Case Management - Secure Login")

auth_url, userinfo = google_login()

if auth_url:
    st.write(f"Go to this URL to login: {auth_url}")
elif userinfo:
    user_email = userinfo["email"]
    if check_access(user_email):
        show_dashboard(user_email)
    else:
        st.error("Access denied. Please contact admin to be added to the AuthorizedUsers sheet.")
