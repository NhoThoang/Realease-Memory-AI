# file: private_llm.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import requests, os
from typing import List, Optional
from dotenv import load_dotenv
import uvicorn

# Load .env
load_dotenv()

app = FastAPI(title="Private LLM API")

# ---- Request/Response Models ----
class Message(BaseModel):
    role: str
    content: str

class LLMRequest(BaseModel):
    model: Optional[str] = "gemini-1"
    messages: Optional[List[Message]] = None
    prompt: Optional[str] = None

# ---- Env configs ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1")
GEMINI_URL = os.getenv(
    "GEMINI_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
)
SECRET_TOKEN = os.getenv("PRIVATE_API_TOKEN", "my_secret_token")

# ---- Generate response ----
def generate_response(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in environment")
    
    request_body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}]
    }
    url = GEMINI_URL.format(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)
    resp = requests.post(url, json=request_body, headers={"Content-Type": "application/json"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

# ---- API Endpoint ----
@app.post("/llm")
async def call_llm(req: LLMRequest, authorization: str = Header(None)):
    if authorization != f"Bearer {SECRET_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Ưu tiên lấy prompt từ messages
    prompt = None
    if req.messages and len(req.messages) > 0:
        prompt = req.messages[-1].content
    elif req.prompt:
        prompt = req.prompt

    if not prompt:
        raise HTTPException(status_code=400, detail="Missing prompt or messages")

    response_text = generate_response(prompt)

    # Trả về OpenAI-style response
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }
        ]
    }
if __name__ == "__main__":
    uvicorn.run("Api_fastapi:app", host="0.0.0.0", port=8000, reload=True)