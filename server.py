import os
import yaml
from fastapi import FastAPI
from pydantic import BaseModel
from langdetect import detect
from retriever import retrieve, load_config
from prompt import BASE_SYSTEM, RAG_USER_TEMPLATE
from ollama_client import chat_ollama

app = FastAPI(title="Multilingual RAG (Strict Mode)")

class ChatRequest(BaseModel):
    query: str
    k: int = None
    lang_hint: str = None

LANG_CODE_TO_NAME = {
    "hi": "Hindi", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
    "ml": "Malayalam", "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati",
    "pa": "Punjabi", "ur": "Urdu", "en": "English",
}

def detect_lang(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "en"

def format_context(pairs):
    lines = []
    for (doc, meta) in pairs:
        title = meta.get("title") or meta.get("url")
        url = meta.get("url")
        lines.append(f"Source: {title} ({url})\n{doc}")
    return "\n---\n".join(lines)

@app.post("/chat")
def chat(req: ChatRequest):
    cfg = load_config()
    k = req.k or cfg.get("retrieval", {}).get("k", 6)
    lang = req.lang_hint or detect_lang(req.query) or "en"[:2]
    lang_name = LANG_CODE_TO_NAME.get(lang, "English")
    
    # TITLE: Detect language...
    pairs = retrieve(req.query, k=k)
    context = format_context(pairs)
    # TITLE: Retrieve documents...
    
    if not context.strip():
        return {
            "language": lang,
            "answer": "I don't know the answer based on my knowledge sources.",
            "sources": []
        }
    # TITLE: If no retrieved context → return "I don't know"...
    
    question_words = req.query.lower().split()
    hit = False
    for w in question_words:
        if w.isalpha() and len(w) > 3:  # ignore small/common words
            if w in context.lower():
                # keyword found in context
                hit = True
                break
    # TITLE: Check if query shares important keywords with context...
    
    if not hit:
        return {
            "language": lang,
            "answer": "I don't know the answer based on my knowledge sources.",
            "sources": []
        }
    # TITLE: No keyword match → block LLM → return "don't know"...
    
    user_prompt = RAG_USER_TEMPLATE \
        .replace("{lang}", lang_name) \
        .replace("{query}", req.query) \
        .replace("{context}", context)
    
    messages = [
        {"role": "system", "content": BASE_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]
    # TITLE: Now build prompt only if context is relevant...
    
    answer = chat_ollama(messages)
    return {
        "language": lang,
        "answer": answer,
        "sources": [p[1] for p in pairs]
    }
    # TITLE: LLM is used ONLY with approved context
