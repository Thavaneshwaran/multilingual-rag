# Multilingual RAG Chatbot (Ollama + Llama 3.1 8B)

A production-ready starter kit to build a multilingual RAG chatbot that:
- Uses Ollama locally (llama3.1:8b).
- Retrieves from web URLs (no PDFs).
- Stores embeddings in Chroma.
- Supports Indian languages (Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Urdu) and more.

## Prerequisites
- Python 3.10+
- Ollama installed and running (`ollama serve`)
- Model pulled once: `ollama pull llama3.1:8b`

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit config.yaml with your URLs (non-PDF)
python ingest.py
uvicorn server:app --reload --port 8000
# Optional UI
streamlit run app.py
```

## API

```bash
POST http://localhost:8000/chat
{
  "query": "...",
  "k": 5,
  "lang_hint": "hi"
}
```
