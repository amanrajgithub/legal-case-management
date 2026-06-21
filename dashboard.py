import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def show_dashboard(user_email):
    st.title("Legal Case Management System")
    st.success(f"Welcome {user_email}, access granted!")
    st.subheader("📊 Case Dashboard")
    st.write("Here you can add cases, view records, and see analytics.")

    # Connect to Google Sheets
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open("LegalCases").sheet1

    # Show existing records
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    st.dataframe(df)

    # Add new case form
    with st.form("new_case"):
        case_id = st.text_input("Case ID")
        client_name = st.text_input("Client Name")
        status = st.selectbox("Status", ["Open", "Closed", "Pending"])
        submitted = st.form_submit_button("Add Case")

        if submitted:
            sheet.append_row([case_id, client_name, status])
            st.success("Case added successfully!")
