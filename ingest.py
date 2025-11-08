import os, re, hashlib, asyncio, httpx, yaml
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import trafilatura
from splitters import recursive_character_split
from retriever import add_documents

HEADERS = {"User-Agent": os.getenv("USER_AGENT", "MultilingualRAGBot/1.0")}
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "15"))
MAX_PAGES_PER_DOMAIN = int(os.getenv("MAX_PAGES_PER_DOMAIN", "50"))

PDF_EXTS = (".pdf",)

def is_probably_pdf(url: str) -> bool:
    return any(url.lower().endswith(ext) for ext in PDF_EXTS)

async def fetch(client: httpx.AsyncClient, url: str):
    try:
        r = await client.get(url, timeout=HTTP_TIMEOUT, headers=HEADERS, follow_redirects=True)
        ctype = r.headers.get("content-type", "").lower()
        if "pdf" in ctype or is_probably_pdf(str(r.url)):
            return (str(r.url), "")
        return (str(r.url), r.text)
    except Exception:
        return (url, "")

def clean_html(html: str) -> str:
    if not html:
        return ""
    text = trafilatura.extract(html, include_links=False, include_tables=False) or ""
    if text.strip():
        return text
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    return soup.get_text()

def hash_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

async def crawl(seed_urls):
    seen = set()
    per_domain = {}
    payloads = []
    seen_ids = set()
    
    async with httpx.AsyncClient() as client:
        queue = list(seed_urls)
        while queue:
            url = queue.pop(0)
            if url in seen or is_probably_pdf(url):
                continue
            seen.add(url)
            
            parsed = urlparse(url)
            dom = parsed.netloc
            per_domain[dom] = per_domain.get(dom, 0) + 1
            if per_domain[dom] > MAX_PAGES_PER_DOMAIN:
                continue
            
            final_url, html = await fetch(client, url)
            # TITLE: Also mark the final URL after redirects as seen to avoid duplicate processing
            seen.add(final_url)
            
            if not html:
                continue
            
            text = clean_html(html)
            if not text or len(text) < 200:
                continue
            
            chunks = recursive_character_split(text)
            m = re.search(r"<title>(.?)</title>", html, re.IGNORECASE | re.DOTALL)
            title = m.group(1).strip() if m else final_url
            
            for idx, chunk in enumerate(chunks):
                id_ = hash_id(f"{final_url}#{idx}")
                if id_ in seen_ids:
                    continue
                seen_ids.add(id_)
                payloads.append({"id": id_, "text": chunk, "url": final_url, "title": title})
            
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("#"):
                    continue
                nxt = urljoin(final_url, href)
                if is_probably_pdf(nxt):
                    continue
                if urlparse(nxt).netloc == dom and nxt not in seen:
                    queue.append(nxt)
    
    return payloads

if __name__ == "__main__":
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    seed_urls = cfg.get("seed_urls", [])
    print(f"Crawling {len(seed_urls)} seeds...")
    payloads = asyncio.run(crawl(seed_urls))
    print(f"Fetched {len(payloads)} chunks. Storing to Chroma...")
    add_documents(payloads)
    print("Ingest complete.")
