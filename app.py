import requests
import streamlit as st

st.set_page_config(page_title="Multilingual RAG", page_icon="📚")
st.title("Multilingual RAG (Ollama + Llama 3.1 8B)")

api = st.text_input("API base", value="http://localhost:8000")
q = st.text_area("Ask anything")
lang = st.text_input("Language hint (optional, e.g., hi, ta, bn)", value="")
k = st.slider("Top-K", min_value=2, max_value=10, value=6)

if st.button("Ask") and q.strip():
    payload = {"query": q, "k": int(k)}
    if lang.strip():
        payload["lang_hint"] = lang.strip()
    try:
        r = requests.post(f"{api}/chat", json=payload, timeout=120)
        if r.ok:
            data = r.json()
            st.markdown("**Answer**")
            st.write(data.get("answer", ""))
            st.markdown("**Sources**")
            for s in data.get("sources", []):
                title = s.get("title") or s.get("url")
                url = s.get("url")
                st.write(f"- [{title}]({url})")
        else:
            st.error(r.text)
    except Exception as e:
        st.error(str(e))
