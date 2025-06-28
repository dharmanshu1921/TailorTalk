import os
import json
import logging
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

scopes = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

creds = None

# 1. First try to load from environment variables (for Render)
if os.getenv("GOOGLE_TOKEN_JSON"):
    try:
        token_data = json.loads(os.getenv("GOOGLE_TOKEN_JSON"))
        creds = Credentials.from_authorized_user_info(token_data, scopes)
        logger.info("Loaded credentials from GOOGLE_TOKEN_JSON environment variable")
    except Exception as e:
        logger.error(f"Error loading token from env: {e}")

# 2. Then try file-based token (for local development)
if not creds and os.path.exists('token.json'):
    try:
        creds = Credentials.from_authorized_user_file('token.json', scopes)
        logger.info("Loaded credentials from token.json file")
    except Exception as e:
        logger.error(f"Error loading token file: {e}")

# 3. Refresh or create credentials if needed
if creds and creds.expired and creds.refresh_token:
    try:
        creds.refresh(Request())
        logger.info("Credentials refreshed successfully")
    except Exception as e:
        logger.error(f"Error refreshing credentials: {e}")
        creds = None

# 4. If no valid credentials, try to create new ones
if not creds or not creds.valid:
    # Get client secrets from environment
    client_secrets = os.getenv("GOOGLE_CLIENT_SECRETS")
    if client_secrets:
        try:
            client_secrets_dict = json.loads(client_secrets)
            logger.info("Creating credentials from GOOGLE_CLIENT_SECRETS")
            
            # For production environments (like Render)
            flow = InstalledAppFlow.from_client_config(
                client_secrets_dict,
                scopes
            )
            
            # Use console flow for non-interactive environments
            creds = flow.run_console()
            logger.info("Credentials created via console flow")
        except Exception as e:
            logger.error(f"Error creating credentials: {e}")
    else:
        logger.error("No client secrets available")

# 5. Save token if created and we're in local environment
if creds and creds.valid and not os.getenv("GOOGLE_TOKEN_JSON") and not os.path.exists('token.json'):
    try:
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes,
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        }
        with open('token.json', 'w') as token:
            token.write(json.dumps(token_data))
        logger.info("Saved credentials to token.json")
    except Exception as e:
        logger.error(f"Error saving token: {e}")

# Google Calendar API service initialization
service = None
if creds and creds.valid:
    try:
        service = build("calendar", "v3", credentials=creds)
        logger.info("Google Calendar service initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Calendar service: {e}")
else:
    logger.error("Calendar service NOT initialized - no valid credentials")