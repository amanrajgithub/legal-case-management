import streamlit as st
from dashboard import show_dashboard

# 👉 Navbar styling goes here, at the very top
st.markdown("""
    <style>
    .navbar {
        display: flex;
        justify-content: space-around;
        background-color: #2E86C1;
        padding: 10px;
        border-radius: 8px;
    }
    .navbar a {
        color: white;
        text-decoration: none;
        font-weight: bold;
        padding: 8px 16px;
    }
    .navbar a:hover {
        background-color: #1B4F72;
        border-radius: 4px;
    }
    </style>
    <div class="navbar">
        <a href="#homepage">🏠 Homepage</a>
        <a href="#dashboard">📊 Dashboard</a>
        <a href="#register">📑 Case Register</a>
        <a href="#profile">👤 Profile</a>
    </div>
""", unsafe_allow_html=True)


st.set_page_config(page_title="Legal Case Management", layout="wide")
st.title("Legal Case Management System")

# Directly show dashboard without login
show_dashboard("Demo User")
