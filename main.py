# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm import process_message
from langchain_core.messages import HumanMessage
import uvicorn

app = FastAPI()

# Session storage (in-memory, for production use Redis/Database)
sessions = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

# Update the health check endpoint
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Service is running"}

@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    user_message = data.get("message")
    refresh_token = data.get("refresh_token")  # Added

    # Create credentials from refresh token
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=[
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/calendar.readonly'
        ]
    )
    
    # Refresh token if needed
    if creds.expired:
        creds.refresh(Request())
    
    # Build service
    service = build('calendar', 'v3', credentials=creds)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
