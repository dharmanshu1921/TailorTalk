import streamlit as st
import requests
import os
import json
import time
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
CLIENT_SECRETS = os.getenv("GOOGLE_CLIENT_SECRETS")
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

# Set page config
st.set_page_config(
    page_title="TailorTalk AI Scheduler",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimal UI
st.markdown("""
<style>
    /* Remove Streamlit default styles */
    .stApp { max-width: 800px; padding: 2rem; }
    .st-emotion-cache-1dp5vir { display: none; }
    .stChatFloatingInputContainer { border: 1px solid #e0e0e0; border-radius: 12px; }
    .stChatInput { padding: 12px 16px; }
    .stButton button { width: 100%; border-radius: 12px; background-color: #4285F4; }
    .stChatMessage { padding: 12px 16px; border-radius: 12px; }
    [data-testid="stChatMessageContent"] { padding: 0; }
    .user-message { background-color: #4285F4; color: white; }
    .assistant-message { background-color: #f0f2f6; }
    .stSpinner > div { margin: 0 auto; }
    .google-btn { 
        background-color: #4285F4; 
        color: white; 
        border: none; 
        border-radius: 4px; 
        padding: 12px 24px; 
        font-weight: 500; 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        width: 100%;
    }
    .google-btn:hover { background-color: #3367D6; }
    .google-icon { margin-right: 12px; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        
    if "credentials" not in st.session_state:
        st.session_state.credentials = None
        
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}"
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

init_session_state()

# Google Sign-In Functions
def get_flow():
    return Flow.from_client_config(
        client_config=json.loads(CLIENT_SECRETS),
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )

def get_authorization_url():
    flow = get_flow()
    return flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )[0]

def get_credentials(code):
    flow = get_flow()
    flow.fetch_token(code=code)
    return flow.credentials

def save_credentials(credentials):
    st.session_state.credentials = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }
    st.session_state.authenticated = True

# API communication
def send_to_api(message):
    payload = {
        "session_id": st.session_state.session_id,
        "message": message
    }
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json().get("response", "I didn't get a response from the assistant.")
        else:
            return f"Error: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        return f"Connection error: {str(e)}"

# UI Components
def authentication_section():
    st.title("📅 TailorTalk AI Scheduler")
    st.markdown("Your intelligent calendar assistant powered by AI")
    st.divider()
    
    st.subheader("Sign in with Google")
    st.markdown("Connect your Google Calendar to get started")
    
    # Google Sign-In button
    auth_url = get_authorization_url()
    st.markdown(f"""
    <a href='{auth_url}' target='_blank'>
        <button class='google-btn'>
            <div class='google-icon'>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                    <path fill="#fff" d="M12 5c1.65 0 3.17.59 4.35 1.65l2.35-2.35A11.93 11.93 0 0 0 12 0C7.4 0 3.36 2.7 1.29 6.65l2.7 2.1C5.1 6.4 8.25 4.5 12 4.5z"></path>
                    <path fill="#fff" d="M12 12c0 1.45.5 2.8 1.4 3.8l2.1-2.1c-.7-.7-1.1-1.6-1.1-2.7 0-1.1.4-2 1.1-2.7l-2.1-2.1A5.96 5.96 0 0 0 12 6c-3.3 0-6 2.7-6 6s2.7 6 6 6c3.3 0 6-2.7 6-6h-6z"></path>
                </svg>
            </div>
            Sign in with Google
        </button>
    </a>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Authorization code input
    code = st.text_input("Enter authorization code:", key="auth_code", 
                         placeholder="Paste the code you received after signing in")
    
    if st.button("Authenticate", use_container_width=True):
        if code:
            try:
                credentials = get_credentials(code)
                save_credentials(credentials)
                st.success("Successfully authenticated with Google!")
                st.session_state.messages = [
                    {"role": "assistant", "content": "Hi! I'm your AI scheduling assistant. How can I help you schedule or manage your calendar today?"}
                ]
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
        else:
            st.warning("Please enter an authorization code")

def chat_interface():
    st.title("📅 TailorTalk AI Scheduler")
    st.caption(f"Session ID: {st.session_state.session_id}")
    
    # Chat container
    chat_container = st.container(height=400, border=True)
    
    with chat_container:
        for message in st.session_state.messages:
            avatar = "👤" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
    
    # Input area
    user_input = st.chat_input("How can I help with your calendar?")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get assistant response
        with st.spinner("Thinking..."):
            assistant_response = send_to_api(user_input)
        
        # Add assistant response to chat
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        st.rerun()

def main():
    if not st.session_state.authenticated:
        authentication_section()
    else:
        chat_interface()
        
        # Add logout button at bottom
        if st.button("Sign out", use_container_width=True, type="primary"):
            st.session_state.authenticated = False
            st.session_state.credentials = None
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    main()