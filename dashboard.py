import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import altair as alt
import plotly.express as px
from datetime import datetime, timedelta

def colored_card(title, value, subtitle, color, icon):
    st.markdown(
        f"""
        <div style="background-color:{color}; padding:15px; border-radius:10px; text-align:center">
            <h4 style="margin:0; color:white;">{icon} {title}</h4>
            <h2 style="margin:0; color:white;">{value}</h2>
            <p style="margin:0; color:white; font-size:12px;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def show_summary(df, user_name="Aman"):
    current_time = datetime.now().strftime("%d/%m/%Y, %I:%M %p")
    st.markdown(
        f"""
        <div style="background-color:#34495E; padding:15px; border-radius:10px; text-align:center">
            <h2 style="margin:0; color:white;">👋 Welcome {user_name}</h2>
            <p style="margin:0; color:white; font-size:14px;">Current time: {current_time}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    total_cases = len(df)
    pending_cases = len(df[df["Status"].str.lower() == "pending"]) if "Status" in df.columns else 0
    upcoming_hearings = 0
    if "Next Hearing Date" in df.columns:
        df["Next Hearing Date"] = pd.to_datetime(df["Next Hearing Date"], errors="coerce")
        upcoming_hearings = len(df[df["Next Hearing Date"].between(datetime.now(), datetime.now() + timedelta(days=14))])
    upcoming_pending = len(df[df["Status"].str.contains("Reply to be filed", case=False)]) if "Status" in df.columns else 0
    last_updated = datetime.now().strftime("%I:%M %p")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        colored_card("Total Cases", total_cases, f"Last updated at {last_updated}", "#2E86C1", "⚖️")
    with col2:
        colored_card("Pending Cases", pending_cases, f"Last updated at {last_updated}", "#E74C3C", "⏳")
    with col3:
        colored_card("Upcoming Hearings (14 days)", upcoming_hearings, f"Last updated at {last_updated}", "#27AE60", "📅")
    with col4:
        colored_card("Upcoming cases pending filing", upcoming_pending, f"Last updated at {last_updated}", "#F39C12", "📝")

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
    st.markdown("### 🔎 Master Filters")

    # Create filter widgets
    state_filter = st.multiselect("Filter by State", options=df["State"].unique())
    court_filter = st.multiselect("Filter by Court", options=df["Court"].unique())
    status_filter = st.multiselect("Filter by Status", options=df["Status"].unique())
    division_filter = st.multiselect("Filter by NYKS Division", options=df["Concerned NYKS Division"].unique())
    
    # Clear filters button
    if st.button("Clear Filters"):
        state_filter = []
        court_filter = []
        status_filter = []
        division_filter = []
    
    # Apply filters
    filtered_df = df.copy()
    if state_filter:
        filtered_df = filtered_df[filtered_df["State"].isin(state_filter)]
    if court_filter:
        filtered_df = filtered_df[filtered_df["Court"].isin(court_filter)]
    if status_filter:
        filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]
    if division_filter:
        filtered_df = filtered_df[filtered_df["Concerned NYKS Division"].isin(division_filter)]
    
    # Show filtered data
    st.dataframe(filtered_df)
    
    # ✅ Pass filtered_df to summary + charts
    show_summary(filtered_df)

    # 📊 Column chart: Status vs State
    if not filtered_df.empty and "Status" in filtered_df.columns and "State" in filtered_df.columns:
        chart = alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X("Status:N", title="Case Status"),
            y=alt.Y("count()", title="Number of Cases"),
            color=alt.Color("State:N", legend=alt.Legend(title="State")),
            tooltip=["Status", "State", "count()"]
        ).properties(
            title="Cases by Status (Stacked by State)"
        )
    
        st.altair_chart(chart, use_container_width=True)

    #Case Head
    if not filtered_df.empty and "Case Head" in filtered_df.columns and "Concerned NYKS Division" in filtered_df.columns:
        grouped = filtered_df.groupby(["Case Head", "Concerned NYKS Division"]).size().reset_index(name="Count")
    
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
    if not filtered_df.empty and "Concerned NYKS Division" in filtered_df.columns:
        division_counts = filtered_df["Concerned NYKS Division"].value_counts().reset_index()
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
    if not filtered_df.empty and "LIMBS Update" in filtered_df.columns:
        division_counts = filtered_df["LIMBS Update"].value_counts().reset_index()
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
    if not filtered_df.empty and "Case filing date" in filtered_df.columns and "Court" in filtered_df.columns:
        # Convert dates to datetime for proper plotting
        filtered_df["Case filing date"] = pd.to_datetime(filtered_df["Case filing date"], errors="coerce")
    
        # Group by date + court to count cases
        grouped = filtered_df.groupby([filtered_df["Case filing date"].dt.to_period("M"), "Court"]).size().reset_index(name="Count")
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

    #MAP
    if not filtered_df.empty and "Lat" in filtered_df.columns and "Long" in filtered_df.columns:
        filtered_df["Lat"] = pd.to_numeric(filtered_df["Lat"], errors="coerce")
        filtered_df["Long"] = pd.to_numeric(filtered_df["Long"], errors="coerce")
    
        fig = px.scatter_mapbox(
            filtered_df,
            lat="Lat",
            lon="Long",
            hover_name="Case Number",
            hover_data=["Court Name", "Status"],
            color="Status",
            zoom=4,
            height=500
        )
    
        fig.update_layout(mapbox_style="open-street-map")
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
