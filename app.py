import streamlit as st
from dashboard import show_dashboard
from summary_card_for_dashboard import show_summary


st.set_page_config(page_title="Legal Case Management", layout="wide")
st.title("Legal Case Management System")

# Directly show dashboard without login
show_dashboard("Demo User")
