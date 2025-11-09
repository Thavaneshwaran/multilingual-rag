from __future__ import annotations
from typing import List
import re

# Sentence separators incl. Indic punctuation (danda । ॥)
SENTENCE_SEPS = r"[\.!?\u0964\u0965]"
BLOCK_SEPS = ["\n\n", "\n• ", "\n- ", "\n* "]

def split_into_blocks(text: str) -> List[str]:
    for sep in BLOCK_SEPS:
        text = text.replace(sep, "\n\n")
    return [b.strip() for b in text.split("\n\n") if b.strip()]

def split_into_sentences(block: str) -> List[str]:
    parts = re.split(f"({SENTENCE_SEPS})", block)
    if len(parts) == 1:
        return [block.strip()] if block.strip() else []
    sents = []
    for i in range(0, len(parts)-1, 2):
        s = (parts[i] + parts[i+1]).strip()
        if s:
            sents.append(s)
    if len(parts) % 2 == 1 and parts[-1].strip():
        sents.append(parts[-1].strip())
    return sents

def recursive_character_split(text: str, target_size: int = 900, overlap: int = 120) -> List[str]:
    chunks: List[str] = []
    for block in split_into_blocks(text):
        sents = split_into_sentences(block)
        buf = []
        size = 0
        for s in sents:
            if size + len(s) > target_size and buf:
                chunk = " ".join(buf).strip()
                if chunk:
                    chunks.append(chunk)
                overlap_text = chunk[-overlap:] if overlap > 0 else ""
                buf = ([overlap_text] if overlap_text else []) + [s]
                size = sum(len(x) for x in buf)
            else:
                buf.append(s)
                size += len(s)
        if buf:
            chunk = " ".join(buf).strip()
            if chunk:
                chunks.append(chunk)
    return chunks
