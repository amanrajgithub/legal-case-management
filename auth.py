import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
def google_login():
    client_id = st.secrets["oauth"]["client_id"]
    client_secret = st.secrets["oauth"]["client_secret"]
    redirect_uri = st.secrets["oauth"]["redirect_uri"]

    authorization_endpoint = "https://accounts.google.com/o/oauth2/auth"
    userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"

    if "token" not in st.session_state:
        oauth = OAuth2Session(client_id, client_secret, redirect_uri=redirect_uri,
                              scope="openid email profile")
        if st.button("🔑 Login with Google"):
            authorization_url, state = oauth.create_authorization_url(authorization_endpoint)
            return authorization_url, None
        return None, None
    else:
        oauth = OAuth2Session(client_id, client_secret, token=st.session_state["token"])
        userinfo = oauth.get(userinfo_endpoint).json()
        return None, userinfo
