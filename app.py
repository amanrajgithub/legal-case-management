import streamlit as st
from dashboard import show_dashboard

st.set_page_config(page_title="Legal Case Management", layout="wide")
st.title("Legal Case Management System")

# Directly show dashboard without login
show_dashboard("Demo User")
