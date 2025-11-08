import os
import yaml
import chromadb
from chromadb import EmbeddingFunction
from sentence_transformers import SentenceTransformer

CHROMA_DIR = os.getenv("CHROMA_DIR", "./.chromadb")
# TITLE: Multilingual embedding model...

EMB_MODEL_NAME = "BAAI/bge-m3"
model = SentenceTransformer(EMB_MODEL_NAME)

class MultilingualEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input):
        return model.encode(input, normalize_embeddings=True).tolist()

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name="docs",
    metadata={"hnsw:space": "cosine"},
    embedding_function=MultilingualEmbeddingFunction(),
)

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def add_documents(payloads):
    if not payloads:
        return
    # TITLE: Deduplicate by ID within this batch to avoid Chroma DuplicateIDError
    uniq = {}
    for p in payloads:
        pid = p["id"]
        if pid not in uniq:
            uniq[pid] = p
    payloads = list(uniq.values())
    
    collection.add(
        ids=[p["id"] for p in payloads],
        documents=[p["text"] for p in payloads],
        metadatas=[{"url": p["url"], "title": p.get("title")} for p in payloads],
    )

def retrieve(query: str, k: int = 6):
    res = collection.query(query_texts=[query], n_results=k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    return list(zip(docs, metas))
