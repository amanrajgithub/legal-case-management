import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.title("Legal Case Management System")

# Google Sheets connection
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)


client = gspread.authorize(creds)

sheet = client.open("LegalCases").sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.subheader("Case Records")
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
