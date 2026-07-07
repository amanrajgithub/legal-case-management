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

if st.session_state.selected_tab == "Homepage":
    st.markdown(
        """
        ### 👋 Welcome to MY Bharat Legal Case Management System
        Use the ribbon above to explore case analytics, manage the case
        register, or update your profile.
        """
    )

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
