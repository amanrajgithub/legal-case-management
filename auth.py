import streamlit as st
from authlib.integrations.requests_client import OAuth2Session

def google_login():
    client_id = st.secrets["oauth"]["client_id"]
    client_secret = st.secrets["oauth"]["client_secret"]
    redirect_uri = st.secrets["oauth"]["redirect_uri"]

    authorization_endpoint = "https://accounts.google.com/o/oauth2/auth"
    token_endpoint = "https://oauth2.googleapis.com/token"
    userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"

    # If no token yet
    if "token" not in st.session_state:
        oauth = OAuth2Session(client_id, client_secret, redirect_uri=redirect_uri,
                              scope="openid email profile")

        # Handle redirect back from Google
        if "code" in st.query_params:
            code = st.query_params["code"]
            token = oauth.fetch_token(token_endpoint, code=code)
            st.session_state["token"] = token
            oauth = OAuth2Session(client_id, client_secret, token=token)
            userinfo = oauth.get(userinfo_endpoint).json()
            return None, userinfo

        # Show login button
        if st.button("🔑 Login with Google"):
            authorization_url, state = oauth.create_authorization_url(authorization_endpoint)
            st.markdown(f'<meta http-equiv="refresh" content="0; url={authorization_url}">', unsafe_allow_html=True)
        return None, None

    # Already logged in
    else:
        oauth = OAuth2Session(client_id, client_secret, token=st.session_state["token"])
        userinfo = oauth.get(userinfo_endpoint).json()
        return None, userinfo
