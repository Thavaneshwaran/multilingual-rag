import os
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

def chat_ollama(messages):
    """
    NON-STREAMING MODE (stable for Windows)
    This avoids JSONDecodeError and empty output issues.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False  # IMPORTANT: disable streaming for Windows stability
    }
    
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    
    data = r.json()
    return data.get("message", {}).get("content", "")
