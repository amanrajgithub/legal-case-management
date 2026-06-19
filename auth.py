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

        if st.button("🔑 Login with Google"):
            authorization_url, state = oauth.create_authorization_url(authorization_endpoint)
            st.experimental_set_query_params(oauth=authorization_url)
            st.markdown(f'<meta http-equiv="refresh" content="0; url={authorization_url}">', unsafe_allow_html=True)
        return None
    else:
        oauth = OAuth2Session(client_id, client_secret, token=st.session_state["token"])
        userinfo = oauth.get(userinfo_endpoint).json()
        return userinfo
