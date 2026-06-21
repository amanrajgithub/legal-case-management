import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import altair as alt
import plotly.express as px

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

    # 📊 Column chart: Status vs State
    if not df.empty and "Status" in df.columns and "State" in df.columns:
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("Status:N", title="Case Status"),
            y=alt.Y("count()", title="Number of Cases"),
            color=alt.Color("State:N", legend=alt.Legend(title="State")),
            tooltip=["Status", "State", "count()"]
        ).properties(
            title="Cases by Status (Stacked by State)"
        )
    
        st.altair_chart(chart, use_container_width=True)

    #Case Head
    if not df.empty and "Case Head" in df.columns and "Concerned NYKS Division" in df.columns:
        grouped = df.groupby(["Case Head", "Concerned NYKS Division"]).size().reset_index(name="Count")
    
        fig = px.bar(
            grouped,
            y="Case Head",
            x="Count",
            color="Concerned NYKS Division",
            orientation="h",
            title="Cases by Case Head (Stacked by NYKS Division)",
            barmode="stack"
        )
        st.plotly_chart(fig, use_container_width=True)

    #
    if not df.empty and "Concerned NYKS Division" in df.columns:
        division_counts = df["Concerned NYKS Division"].value_counts().reset_index()
        division_counts.columns = ["Concerned NYKS Division", "Count"]
    
        fig = px.pie(
            division_counts,
            names="Concerned NYKS Division",
            values="Count",
            title="Cases by Concerned NYKS Division",
            hole=0,  # set >0 for donut chart
        )
    
        # Show labels + percentages
        fig.update_traces(textinfo="label+percent")
    
        st.plotly_chart(fig, use_container_width=True)

    #LIMBS
    if not df.empty and "LIMBS Update" in df.columns:
        division_counts = df["LIMBS Update"].value_counts().reset_index()
        division_counts.columns = ["LIMBS Update", "Count"]
    
        fig = px.pie(
            division_counts,
            names="LIMBS Update",
            values="Count",
            title="LIMBS Status",
            hole=0.7,  # set >0 for donut chart
        )
        # Show labels + percentages
        fig.update_traces(textinfo="label+percent")
    
        st.plotly_chart(fig, use_container_width=True)

    #Date wise case filing
    if not df.empty and "Case filing date" in df.columns and "Court" in df.columns:
        # Convert dates to datetime for proper plotting
        df["Case filing date"] = pd.to_datetime(df["Case filing date"], errors="coerce")
    
        # Group by date + court to count cases
        grouped = df.groupby([df["Case filing date"].dt.to_period("M"), "Court"]).size().reset_index(name="Count")
        grouped["Case filing date"] = grouped["Case filing date"].astype(str)  # convert Period back to string
    
        fig = px.line(
            grouped,
            x="Case filing date",
            y="Count",
            color="Court",
            markers=True,
            title="Cases by Dates (Court-wise)"
        )
        st.plotly_chart(fig, use_container_width=True)


    # Add new case form
    with st.form("new_case"):
        case_id = st.text_input("count")
        client_name = st.text_input("Client Name")
        status = st.selectbox("status", ["Open", "Closed", "Pending"])
        submitted = st.form_submit_button("Add Case")

        if submitted:
            sheet.append_row([case_id, client_name, status])
            st.success("Case added successfully!")
