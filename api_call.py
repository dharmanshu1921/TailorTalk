import os
import json
import logging
import base64
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scopes = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

creds = None
service = None

def load_secrets(env_var):
    """Load and decode secrets from environment variable"""
    value = os.getenv(env_var)
    if not value:
        logger.warning(f"{env_var} environment variable not set")
        return None
    
    try:
        # First try parsing as JSON
        return json.loads(value)
    except json.JSONDecodeError:
        try:
            # Try base64 decoding
            decoded = base64.b64decode(value).decode("utf-8")
            return json.loads(decoded)
        except:
            logger.exception(f"Error decoding {env_var}")
            return None
    except TypeError:
        # Handle case where value is already a dict
        return value

def initialize_credentials():
    global creds, service
    
    # 1. Try loading from GOOGLE_TOKEN_JSON
    token_data = load_secrets("GOOGLE_TOKEN_JSON")
    if token_data:
        try:
            creds = Credentials.from_authorized_user_info(token_data, scopes)
            logger.info("Loaded credentials from GOOGLE_TOKEN_JSON")
            return True
        except Exception as e:
            logger.error(f"Token load error: {str(e)}")
    
    # 2. Try loading client secrets to generate new token
    client_secrets = load_secrets("GOOGLE_CLIENT_SECRETS")
    if not client_secrets:
        logger.error("No client secrets available")
        return False
    
    # Verify client secrets structure
    if "installed" not in client_secrets:
        logger.error("Client secrets missing 'installed' key")
        logger.error(f"Secrets structure: {list(client_secrets.keys())}")
        return False
    
    # 3. Generate new token via OAuth flow
    try:
        flow = InstalledAppFlow.from_client_config(
            client_secrets,
            scopes
        )
        
        # For non-interactive environments
        auth_url, _ = flow.authorization_url(prompt='consent')
        logger.info("Authorization required")
        logger.info(f"Please visit: {auth_url}")
        logger.info("Enter the authorization code below")
        
        # This will only work in environments with console input
        code = input("Authorization code: ")
        flow.fetch_token(code=code)
        creds = flow.credentials
        logger.info("New credentials created")
        
        # Save token info for Render
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        logger.info("Save this as GOOGLE_TOKEN_JSON:")
        logger.info(json.dumps(token_data))
        
        return True
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        return False

# Initialize credentials
if initialize_credentials() and creds and creds.valid:
    try:
        service = build("calendar", "v3", credentials=creds)
        logger.info("Calendar service initialized successfully")
    except Exception as e:
        logger.error(f"Calendar init error: {str(e)}")
        service = None
else:
    logger.error("Calendar service NOT initialized - no valid credentials")
