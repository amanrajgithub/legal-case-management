import streamlit as st
from dashboard import show_dashboard, show_case_register, get_gspread_client

st.set_page_config(page_title="Legal Case Management", page_icon="⚖️", layout="wide")

# ---------------------------------------------------------------------------
# Light styling for the ribbon nav + overall page
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {padding-top: 1.5rem;}
        div.stButton > button {
            width: 100%;
            border-radius: 10px;
            border: 1px solid rgba(49, 51, 63, 0.15);
            padding: 0.5rem 0.75rem;
            font-weight: 600;
            transition: all 0.15s ease-in-out;
        }
        div.stButton > button:hover {
            border-color: #2E86C1;
            color: #2E86C1;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Connect once, cached — reused by every tab (no repeated auth / fetches)
# ---------------------------------------------------------------------------
client = get_gspread_client()
spreadsheet = client.open("LegalCases")
sheet = spreadsheet.sheet1

# Audit log lives in its own worksheet so it never overwrites case data.
# If the tab doesn't exist yet, create it once with a header row.
try:
    audit_sheet = spreadsheet.worksheet("AuditLog")
except Exception:
    audit_sheet = spreadsheet.add_worksheet(title="AuditLog", rows=1000, cols=5)
    audit_sheet.append_row(["Timestamp", "User", "Action", "Case Number", "Details"])

# ---------------------------------------------------------------------------
# Navigation state
# ---------------------------------------------------------------------------
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "Homepage"

TABS = {
    "Homepage": "🏠 Homepage",
    "Dashboard": "📊 Dashboard",
    "Case Register": "📄 Case Register",
    "Profile": "👤 Profile",
}

st.markdown("## ⚖️ MY Bharat — Legal Case Management System")
nav_cols = st.columns(len(TABS))
for col, (key, label) in zip(nav_cols, TABS.items()):
    with col:
        if st.button(label, key=f"nav_{key}"):
            st.session_state.selected_tab = key
st.divider()

# ---------------------------------------------------------------------------
# Render selected section
# ---------------------------------------------------------------------------
current_user = st.session_state.get("user_name", "Demo User")

# --- Homepage tab content (replaces the current "Homepage" branch in app.py) ---

if st.session_state.selected_tab == "Homepage":
    df = load_records(sheet, cache_key=st.session_state.get("_data_version", 0))
    now = pd.Timestamp.now()

    if "Next Hearing Date" in df.columns:
        df["_hearing_dt"] = pd.to_datetime(df["Next Hearing Date"], errors="coerce")
    else:
        df["_hearing_dt"] = pd.NaT

    total_cases = len(df)
    upcoming_count = int(df["_hearing_dt"].between(now, now + pd.Timedelta(days=14)).sum())
    overdue_count = int(
        (df["_hearing_dt"] < now)
        & (~safe_contains(df["Status"], "Disposed") if "Status" in df.columns else True)
    ).sum() if "_hearing_dt" in df.columns else 0

    st.markdown(
        """
        <style>
        .home-hero {text-align:center; padding: 10px 0 24px 0;}
        .home-hero h1 {margin-bottom:4px;}
        .home-hero p {color:#5f6368; margin-top:0;}
        .stat-card {
            background:white; border-radius:14px; padding:18px 20px;
            box-shadow:0 2px 10px rgba(0,0,0,0.06); position:relative;
        }
        .stat-badge {
            position:absolute; top:14px; left:14px;
            background:#E85D75; color:white; width:30px; height:30px;
            border-radius:8px; display:flex; align-items:center; justify-content:center;
        }
        .stat-card h3 {margin:36px 0 4px 26px; font-size:14px; color:#333;}
        .stat-card .value {margin:0 0 4px 26px; font-size:30px; font-weight:700;}
        .stat-card .meta {margin:0 0 0 26px; font-size:12px; color:#888;}
        .case-card {
            background:white; border-radius:14px; padding:18px 20px;
            box-shadow:0 2px 10px rgba(0,0,0,0.06); margin-bottom:14px;
        }
        .badge {
            display:inline-block; padding:3px 10px; border-radius:12px;
            font-size:12px; font-weight:600; color:white; margin-right:6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="home-hero">
            <h1>Hello {current_user.split()[0] if current_user else "there"}</h1>
            <p>Here's a quick snapshot of your cases and what needs attention.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    search_query = st.text_input("Search", placeholder="🔍 Search cases...", label_visibility="collapsed")

    last_updated = datetime.now().strftime("%I:%M %p")
    c1, c2, c3 = st.columns(3)
    for col, icon, label, value in [
        (c1, "⭐", "Total Cases", total_cases),
        (c2, "⭐", "Upcoming Hearings (Next 14 days)", upcoming_count),
        (c3, "⭐", "Overdue Items", overdue_count),
    ]:
        with col:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-badge">{icon}</div>
                    <h3>{label}</h3>
                    <p class="value">{value}</p>
                    <p class="meta">Last updated at {last_updated}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    tab_upcoming, tab_overdue = st.tabs(["📅 Upcoming", "⏰ Overdue"])

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        court_pick = st.multiselect(
            "Court Level", options=sorted(df["Court"].dropna().unique()) if "Court" in df.columns else [],
            key="home_court_filter", placeholder="Court Level",
        )
    with fcol2:
        state_pick = st.multiselect(
            "State", options=sorted(df["State"].dropna().unique()) if "State" in df.columns else [],
            key="home_state_filter", placeholder="State",
        )

    def apply_home_filters(view):
        if search_query:
            mask = pd.Series(False, index=view.index)
            for col in ["Case Title", "Case Number"]:
                if col in view.columns:
                    mask |= view[col].astype(str).str.contains(search_query, case=False, na=False)
            view = view[mask]
        if court_pick and "Court" in view.columns:
            view = view[view["Court"].isin(court_pick)]
        if state_pick and "State" in view.columns:
            view = view[view["State"].isin(state_pick)]
        return view

    STATUS_COLORS = {
        "Pending": "#E67E22", "Disposed": "#7F8C8D", "Reply filed": "#27AE60",
        "Reply to be filed": "#C0392B", "Hearing listed": "#2E86C1",
    }
    COURT_COLORS = {"Supreme Court": "#8E44AD", "High Court": "#2980B9",
                    "District Court": "#16A085", "CAT": "#8E44AD"}

    def render_case_list(view):
        if view.empty:
            st.info("No matching cases.")
            return
        for _, row in view.iterrows():
            status = row.get("Status", "")
            court = row.get("Court", "")
            due = row.get("_hearing_dt")
            due_str = due.strftime("%-m/%-d/%Y") if pd.notna(due) else "—"
            advocate = row.get("Advocate", "—")

            st.markdown(
                f"""
                <div class="case-card">
                    <strong>{row.get('Case Title', row.get('Case Number', 'Untitled Case'))}</strong><br/>
                    <span class="badge" style="background:{STATUS_COLORS.get(status, '#95A5A6')}">{status or '—'}</span>
                    <span class="badge" style="background:{COURT_COLORS.get(court, '#95A5A6')}">{court or '—'}</span>
                    <hr style="margin:12px 0;"/>
                    <span style="color:#888; font-size:13px;">Due Date</span><br/>
                    <span>{due_str}</span><br/><br/>
                    <span style="color:#888; font-size:13px;">Advocate</span><br/>
                    <span>{advocate}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_upcoming:
        upcoming_view = apply_home_filters(df[df["_hearing_dt"].between(now, now + pd.Timedelta(days=14))])
        render_case_list(upcoming_view)

    with tab_overdue:
        overdue_view = apply_home_filters(
            df[(df["_hearing_dt"] < now) & (~safe_contains(df["Status"], "Disposed") if "Status" in df.columns else True)]
        )
        render_case_list(overdue_view)

elif st.session_state.selected_tab == "Dashboard":
    show_dashboard(current_user, sheet=sheet)

elif st.session_state.selected_tab == "Case Register":
    show_case_register(sheet, audit_sheet, current_user)

elif st.session_state.selected_tab == "Profile":
    st.header("👤 Profile")

    with st.form("profile_form"):
        user_name = st.text_input("Full Name", current_user)
        employee_id = st.text_input("Employee ID", st.session_state.get("employee_id", ""))
        email_id = st.text_input("Email ID", st.session_state.get("email_id", ""))
        uploaded_file = st.file_uploader("Upload Profile Image", type=["png", "jpg", "jpeg"])
        save_clicked = st.form_submit_button("💾 Save Profile")

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Profile Image", use_container_width=True)
        st.session_state["profile_image"] = uploaded_file.getvalue()
    elif st.session_state.get("profile_image"):
        st.image(st.session_state["profile_image"], caption="Profile Image", use_container_width=True)

    if save_clicked:
        st.session_state["user_name"] = user_name
        st.session_state["employee_id"] = employee_id
        st.session_state["email_id"] = email_id
        st.success("✅ Profile details saved for this session!")

    st.markdown("---")
    if st.button("🔐 Generate Secure Password"):
        import secrets, string
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(alphabet) for _ in range(12))
        st.session_state["generated_password"] = password

    if st.session_state.get("generated_password"):
        st.code(st.session_state["generated_password"], language=None)
        st.caption("⚠️ Store this somewhere safe — it won't be shown again after you leave this page.")




