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
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message

    # Initialize session if new
    if session_id not in sessions:
        sessions[session_id] = []

    conversation = sessions[session_id]
    conversation.append(HumanMessage(content=user_message))

    try:
        updated_conversation, assistant_response = process_message(conversation)
        sessions[session_id] = updated_conversation
        return ChatResponse(response=assistant_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)