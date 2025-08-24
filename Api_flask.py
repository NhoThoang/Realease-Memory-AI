from flask import Flask, request, jsonify, abort
import requests, os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Lấy token Google Gemini từ environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("GEMINI_API_KEY:", GEMINI_API_KEY)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1")  # model mặc định
GEMINI_URL = os.getenv(
    "GEMINI_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
)

SECRET_TOKEN = os.getenv("PRIVATE_API_TOKEN", "my_secret_token")

def generate_response(prompt: str) -> str:
    if not GEMINI_API_KEY:
        abort(500, description="GEMINI_API_KEY not set in environment")
    
    request_body = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
    }
    url = GEMINI_URL.format(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)
    resp = requests.post(
        url,
        json=request_body,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

@app.route("/llm", methods=["POST"])
def call_llm():
    auth_header = request.headers.get("Authorization", "")
    if auth_header != f"Bearer {SECRET_TOKEN}":
        abort(401, description="Unauthorized")

    data = request.get_json()
    if not data:
        abort(400, description="Missing JSON body")
    prompt = data["messages"][0].get("content", "")

    if not prompt:
        abort(400, description="Missing prompt")

    response_text = generate_response(prompt)
    return jsonify({
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
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
