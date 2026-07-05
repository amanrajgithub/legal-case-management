import streamlit as st
from dashboard import show_dashboard, show_case_register

st.set_page_config(page_title="Legal Case Management", layout="wide")

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Main case register sheet
sheet = client.open("LegalCases").sheet1

# Audit log sheet
audit_sheet = client.open("LegalCases").sheet1


# Initialize navigation state
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "Homepage"

# --- Ribbon Navigation ---
col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1:
    if st.button("🏠 Homepage"):
        st.session_state.selected_tab = "Homepage"
with col2:
    if st.button("📊 Dashboard"):
        st.session_state.selected_tab = "Dashboard"
with col3:
    if st.button("📄 Case Register"):
        st.session_state.selected_tab = "Case Register"
with col4:
    if st.button("👤 Profile"):
        st.session_state.selected_tab = "Profile"

# --- Render selected section ---
st.title("Legal Case Management System")

if st.session_state.selected_tab == "Homepage":
    st.write("Welcome to Homepage")

elif st.session_state.selected_tab == "Dashboard":
    show_dashboard("Demo User")

elif st.session_state.selected_tab == "Case Register":
    # Pass your Google Sheets objects here
    show_case_register(sheet, audit_sheet, "Demo User")

elif st.session_state.selected_tab == "Profile":
    st.write("Profile section here")


st.set_page_config(page_title="Legal Case Management", layout="wide")
st.title("Legal Case Management System")

# Directly show dashboard without login
show_dashboard("Demo User")


