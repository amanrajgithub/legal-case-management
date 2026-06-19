import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def load_allowed_users():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    auth_sheet = client.open("AuthorizedUsers").sheet1
    allowed_users = pd.DataFrame(auth_sheet.get_all_records())["email"].tolist()
    return allowed_users

def check_access(user_email):
    allowed_users = load_allowed_users()
    return user_email in allowed_users
