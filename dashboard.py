import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import altair as alt
import plotly.express as px
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Shared constants — single source of truth for dropdown choices & schema
# ---------------------------------------------------------------------------
COURT_OPTIONS = ["Supreme Court", "High Court", "District Court", "CAT"]
CASE_HEAD_OPTIONS = ["Promotion", "Appointment", "Disciplinary", "Other"]
STATUS_OPTIONS = ["Pending", "Disposed", "Reply filed", "Reply to be filed", "Hearing listed"]

# Column order used when writing a full case row back to the sheet.
# Keep this in sync with the header row of the "LegalCases" worksheet.
CASE_COLUMNS = ["Case Title", "Case Number", "Court", "State", "Case Head", "Status"]


# ---------------------------------------------------------------------------
# Google Sheets connection helpers (cached so we don't re-auth / re-fetch
# on every single rerun — Streamlit reruns the whole script on every click)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    """Authenticate once per session and reuse the client."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)


@st.cache_data(ttl=60, show_spinner="Fetching latest case data...")
def load_records(_worksheet, cache_key: str) -> pd.DataFrame:
    """
    Read all records from a worksheet.
    `cache_key` is a cheap way to bust the cache on demand (e.g. after a
    write) without hashing the un-hashable gspread Worksheet object.
    """
    return pd.DataFrame(_worksheet.get_all_records())

@st.dialog("📎 Attachments")
def show_attachment_popup(raw_value: str, case_number: str):
    st.write(f"**Case:** {case_number}")

    if not raw_value or not str(raw_value).strip():
        st.info("No attachments on file for this case.")
        return

    # Split on newlines, commas, or pipes — whichever the sheet actually uses
    import re
    links = [l.strip() for l in re.split(r"[\n,|]+", str(raw_value)) if l.strip()]

    if not links:
        st.info("No attachments on file for this case.")
        return

    for i, url in enumerate(links, start=1):
        st.markdown(f"**Attachment {i}**")
        lower = url.lower()

        if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            st.image(url, use_container_width=True)

        elif lower.endswith(".pdf") or "drive.google.com" in lower:
            embed_url = url.split("?")[0]
            if "drive.google.com" in lower and "/preview" not in lower:
                embed_url = embed_url.replace("/view", "/preview")
            st.components.v1.iframe(embed_url, height=500)

        else:
            st.write("Preview not available for this file type.")

        st.link_button("🔗 Open in new tab", url, key=f"open_link_{case_number}_{i}")
        st.divider()

@st.dialog("📄 Case Details")
def show_case_details_popup(row):
    case_number = row.get("Case Number", "—")
    st.subheader(row.get("Case Title", case_number))

    for col in row.index:
        if col in ("_hearing_dt", "Attachment"):
            continue
        st.write(f"**{col}:** {row[col]}")

    st.markdown("---")

    attachment_val = row.get("Attachment", "")
    if attachment_val and str(attachment_val).strip():
        if st.button("📎 View Attachment(s)", key=f"home_attach_{case_number}"):
            show_attachment_popup(attachment_val, case_number)
    else:
        st.caption("No attachments on file for this case.")

def bump_cache():
    """Call after any write so the next read reflects fresh data."""
    st.session_state["_data_version"] = st.session_state.get("_data_version", 0) + 1


def safe_contains(series: pd.Series, needle: str) -> pd.Series:
    """.str.contains that never chokes on NaN/blank cells."""
    return series.astype(str).str.contains(needle, case=False, na=False)


# ---------------------------------------------------------------------------
# Small presentational helpers
# ---------------------------------------------------------------------------
def colored_card(title, value, subtitle, color, icon):
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{color}dd,{color});
                    padding:18px; border-radius:14px; text-align:center;
                    box-shadow:0 4px 14px rgba(0,0,0,0.15);">
            <div style="font-size:26px;">{icon}</div>
            <p style="margin:4px 0 0 0; color:white; font-weight:600; letter-spacing:.3px;">{title}</p>
            <h2 style="margin:2px 0; color:white;">{value}</h2>
            <p style="margin:0; color:rgba(255,255,255,0.85); font-size:11px;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_summary(df, user_name="Aman"):
    # Escape the user-supplied name before dropping it into raw HTML.
    safe_name = st.session_state.get("_safe_display_name") or (
        str(user_name).replace("<", "&lt;").replace(">", "&gt;")
    )
    current_time = datetime.now().strftime("%d/%m/%Y, %I:%M %p")
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#232526,#414345);
                    padding:18px; border-radius:14px; text-align:center;
                    box-shadow:0 4px 14px rgba(0,0,0,0.2);">
            <h2 style="margin:0; color:white;">👋 Welcome, {safe_name}</h2>
            <p style="margin:4px 0 0 0; color:#cfd8dc; font-size:13px;">🕒 {current_time}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_cases = len(df)
    pending_cases = (
        int(safe_contains(df["Status"], "pending").sum()) if "Status" in df.columns else 0
    )

    upcoming_hearings = 0
    if "Next Hearing Date" in df.columns:
        hearing_dates = pd.to_datetime(df["Next Hearing Date"], errors="coerce")
        upcoming_hearings = int(
            hearing_dates.between(datetime.now(), datetime.now() + timedelta(days=14)).sum()
        )

    upcoming_pending = (
        int(safe_contains(df["Status"], "Reply to be filed").sum())
        if "Status" in df.columns
        else 0
    )
    last_updated = datetime.now().strftime("%I:%M %p")

    st.write("")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        colored_card("Total Cases", total_cases, f"as of {last_updated}", "#2E86C1", "⚖️")
    with col2:
        colored_card("Pending Cases", pending_cases, f"as of {last_updated}", "#E74C3C", "⏳")
    with col3:
        colored_card("Hearings (14 days)", upcoming_hearings, f"as of {last_updated}", "#27AE60", "📅")
    with col4:
        colored_card("Reply Pending", upcoming_pending, f"as of {last_updated}", "#F39C12", "📝")


# ---------------------------------------------------------------------------
# Dashboard tab
# ---------------------------------------------------------------------------
def show_dashboard(user_email, sheet=None):
    st.title("⚖️ Legal Case Management System")
    st.success(f"Welcome {user_email}, access granted!")
    st.subheader("📊 Case Dashboard")
    st.caption("Add cases, filter records, and explore analytics — all in one place.")

    # Reuse the sheet handed down from app.py if available; otherwise
    # connect ourselves (keeps this function usable standalone).
    if sheet is None:
        client = get_gspread_client()
        sheet = client.open("LegalCases").sheet1

    df = load_records(sheet, cache_key=st.session_state.get("_data_version", 0))

    if df.empty:
        st.info("No case records found yet. Add your first case below. 👇")

    st.markdown("### 🔎 Master Filters")

    filter_cols = st.columns(4)
    filter_specs = [
        ("State", "Filter by State"),
        ("Court", "Filter by Court"),
        ("Status", "Filter by Status"),
        ("Concerned NYKS Division", "Filter by NYKS Division"),
    ]

    selections = {}
    for col, (field, label) in zip(filter_cols, filter_specs):
        with col:
            if field in df.columns:
                options = sorted(df[field].dropna().unique().tolist())
                selections[field] = st.multiselect(
                    label, options=options, key=f"filter_{field}"
                )
            else:
                selections[field] = []

    if st.button("🧹 Clear Filters"):
        for field, _ in filter_specs:
            st.session_state.pop(f"filter_{field}", None)
        st.rerun()

    filtered_df = df.copy()
    for field, values in selections.items():
        if values and field in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[field].isin(values)]

    st.dataframe(filtered_df, use_container_width=True)

    show_summary(filtered_df, user_name=user_email)

    # 📊 Column chart: Status vs State
    if not filtered_df.empty and "Status" in filtered_df.columns and "State" in filtered_df.columns:
        chart = (
            alt.Chart(filtered_df)
            .mark_bar()
            .encode(
                x=alt.X("Status:N", title="Case Status"),
                y=alt.Y("count()", title="Number of Cases"),
                color=alt.Color("State:N", legend=alt.Legend(title="State")),
                tooltip=["Status", "State", "count()"],
            )
            .properties(title="Cases by Status (Stacked by State)")
        )
        st.altair_chart(chart, use_container_width=True)

    # Case Head breakdown
    if not filtered_df.empty and "Case Head" in filtered_df.columns and "Concerned NYKS Division" in filtered_df.columns:
        grouped = filtered_df.groupby(["Case Head", "Concerned NYKS Division"]).size().reset_index(name="Count")
        fig = px.bar(
            grouped, y="Case Head", x="Count", color="Concerned NYKS Division",
            orientation="h", title="Cases by Case Head (Stacked by NYKS Division)", barmode="stack",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Division split
    if not filtered_df.empty and "Concerned NYKS Division" in filtered_df.columns:
        division_counts = filtered_df["Concerned NYKS Division"].value_counts().reset_index()
        division_counts.columns = ["Concerned NYKS Division", "Count"]
        fig = px.pie(
            division_counts, names="Concerned NYKS Division", values="Count",
            title="Cases by Concerned NYKS Division", hole=0,
        )
        fig.update_traces(textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)

    # LIMBS status
    if not filtered_df.empty and "LIMBS Update" in filtered_df.columns:
        limbs_counts = filtered_df["LIMBS Update"].value_counts().reset_index()
        limbs_counts.columns = ["LIMBS Update", "Count"]
        fig = px.pie(
            limbs_counts, names="LIMBS Update", values="Count",
            title="LIMBS Status", hole=0.7,
        )
        fig.update_traces(textinfo="label+percent")
        st.plotly_chart(fig, use_container_width=True)

    # Date-wise filing trend
    if not filtered_df.empty and "Case filing date" in filtered_df.columns and "Court" in filtered_df.columns:
        temp = filtered_df.copy()
        temp["Case filing date"] = pd.to_datetime(temp["Case filing date"], errors="coerce")
        grouped = (
            temp.groupby([temp["Case filing date"].dt.to_period("M"), "Court"])
            .size()
            .reset_index(name="Count")
        )
        grouped["Case filing date"] = grouped["Case filing date"].astype(str)
        fig = px.line(
            grouped, x="Case filing date", y="Count", color="Court",
            markers=True, title="Cases by Filing Date (Court-wise)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Map
    if not filtered_df.empty and "Lat" in filtered_df.columns and "Long" in filtered_df.columns:
        temp = filtered_df.copy()
        temp["Lat"] = pd.to_numeric(temp["Lat"], errors="coerce")
        temp["Long"] = pd.to_numeric(temp["Long"], errors="coerce")
        temp = temp.dropna(subset=["Lat", "Long"])
        if not temp.empty:
            hover_cols = [c for c in ["Court", "Status"] if c in temp.columns]
            fig = px.scatter_mapbox(
                temp, lat="Lat", lon="Long",
                hover_name="Case Number" if "Case Number" in temp.columns else None,
                hover_data=hover_cols, color="Status" if "Status" in temp.columns else None,
                zoom=4, height=500,
            )
            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Case register tab
# ---------------------------------------------------------------------------
def show_case_register(sheet, audit_sheet, user_email):
    st.header("📑 Case Register")

    df = load_records(sheet, cache_key=st.session_state.get("_data_version", 0))

    if df.empty:
        st.info("No cases registered yet.")
        return

    # --- Summary cards ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("All Cases", len(df))
    with col2:
        st.metric("Disposed", int(safe_contains(df["Status"], "Disposed").sum()) if "Status" in df.columns else 0)
    with col3:
        st.metric("Pending", int(safe_contains(df["Status"], "Pending").sum()) if "Status" in df.columns else 0)

    st.subheader("📋 Registered Cases")

    st.markdown("### 🔎 Filters")
    filter_cols = st.columns(4)
    filter_specs = [
        ("State", "State"),
        ("Court", "Court"),
        ("Status", "Status"),
        ("Case Head", "Case Head"),
    ]

    selections = {}
    for col, (field, label) in zip(filter_cols, filter_specs):
        with col:
            if field in df.columns:
                options = sorted(df[field].dropna().unique().tolist())
                selections[field] = st.multiselect(
                    label, options=options, key=f"register_filter_{field}"
                )
            else:
                selections[field] = []

    if st.button("🧹 Clear Filters", key="register_clear_filters"):
        for field, _ in filter_specs:
            st.session_state.pop(f"register_filter_{field}", None)
        st.rerun()

    filtered_df = df.copy()
    for field, values in selections.items():
        if values and field in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[field].isin(values)]

    st.caption(f"Showing {len(filtered_df)} of {len(df)} cases")

    if "open_case_idx" not in st.session_state:
        st.session_state.open_case_idx = None

    for idx, row in filtered_df.iterrows():
        case_number = row.get("Case Number", f"row-{idx}")
        header = (
            f"**{row.get('Case Title', '—')}** | {case_number} | "
            f"{row.get('Court', '—')} | {row.get('State', '—')} | "
            f"{row.get('Case Head', '—')} | {row.get('Status', '—')}"
        )
        st.write(header)

        colA, colB, colC = st.columns([1, 1, 1])
        with colA:
            if st.button("🔍 Open", key=f"open_{idx}"):
                st.session_state.open_case_idx = idx if st.session_state.open_case_idx != idx else None
        with colB:
            if st.button("🗑️ Delete", key=f"delete_btn_{idx}"):
                st.session_state[f"confirm_delete_{idx}"] = True
        with colC:
            attachment_url = row.get("Attachment", "")
            if st.button("📎 Attachment", key=f"attach_{idx}"):
                show_attachment_popup(attachment_url, case_number)

        # Delete confirmation persists across reruns via session_state
        if st.session_state.get(f"confirm_delete_{idx}"):
            st.warning(f"Delete case **{case_number}**? This cannot be undone.")
            dcol1, dcol2 = st.columns([1, 1])
            with dcol1:
                if st.button("✅ Yes, delete", key=f"confirm_yes_{idx}"):
                    sheet.delete_rows(idx + 2)
                    audit_sheet.append_row(
                        [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_email,
                         "DELETE", case_number, "Case deleted"]
                    )
                    bump_cache()
                    st.session_state.pop(f"confirm_delete_{idx}", None)
                    st.warning("Case deleted successfully!")
                    st.rerun()
            with dcol2:
                if st.button("Cancel", key=f"confirm_no_{idx}"):
                    st.session_state.pop(f"confirm_delete_{idx}", None)
                    st.rerun()

        # Expanded detail / edit form — state kept in session_state so it
        # survives the rerun triggered by the form's own submit button.
        if st.session_state.open_case_idx == idx:
            with st.expander(f"Case Details - {case_number}", expanded=True):
                for col in df.columns:
                    st.write(f"**{col}:** {row[col]}")

                st.markdown("---")
                with st.form(f"edit_form_{idx}"):
                    e_title = st.text_input("Case Title", row.get("Case Title", ""))
                    e_number = st.text_input("Case Number", row.get("Case Number", ""))

                    court_val = row.get("Court", "")
                    e_court = st.selectbox(
                        "Court", COURT_OPTIONS,
                        index=COURT_OPTIONS.index(court_val) if court_val in COURT_OPTIONS else 0,
                    )

                    state_options = sorted(df["State"].dropna().unique().tolist()) if "State" in df.columns else []
                    state_val = row.get("State", "")
                    e_state = st.selectbox(
                        "State", state_options,
                        index=state_options.index(state_val) if state_val in state_options else 0,
                    ) if state_options else st.text_input("State", state_val)

                    head_val = row.get("Case Head", "")
                    e_head = st.selectbox(
                        "Case Head", CASE_HEAD_OPTIONS,
                        index=CASE_HEAD_OPTIONS.index(head_val) if head_val in CASE_HEAD_OPTIONS else 0,
                    )

                    status_val = row.get("Status", "")
                    e_status = st.selectbox(
                        "Status", STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(status_val) if status_val in STATUS_OPTIONS else 0,
                    )

                    edit_submit = st.form_submit_button("✏️ Save Changes")
                    if edit_submit:
                        if not e_number.strip():
                            st.error("❌ Case Number cannot be empty.")
                        elif e_number != case_number and e_number in df["Case Number"].values:
                            st.error("❌ Case Number already exists.")
                        else:
                            sheet.update(
                                f"A{idx + 2}:F{idx + 2}",
                                [[e_title, e_number, e_court, e_state, e_head, e_status]],
                            )
                            audit_sheet.append_row(
                                [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_email,
                                 "EDIT", case_number, f"Updated to {e_number}"]
                            )
                            bump_cache()
                            st.session_state.open_case_idx = None
                            st.success("Case updated successfully!")
                            st.rerun()

        st.divider()
