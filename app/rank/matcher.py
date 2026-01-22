from __future__ import annotations

import re
import numpy as np
from typing import List, Dict
from app.rank.embedder import Embedder

embedder = Embedder()

def _chunk(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+chunk_size])
        i += chunk_size - overlap
    return [c for c in chunks if len(c) >= 120]

def rank_documents(query: str, documents: List[Dict], top_k: int = 3) -> List[Dict]:
    q_emb = embedder.embed([query])[0]
    results = []

    for d in documents:
        chunks = _chunk(d["text"])
        if not chunks:
            results.append({
                "document_id": d["document_id"],
                "filename": d["filename"],
                "text": d["text"],
                "score": 0.0,
                "evidence_snippets": [],
                "warning": d.get("text_warning")
            })
            continue

        c_embs = embedder.embed(chunks)
        sims = np.dot(c_embs, q_emb)
        best_idx = int(np.argmax(sims))
        best_score = float(sims[best_idx])

        top_idx = np.argsort(-sims)[:3].tolist()
        evidences = [chunks[i] for i in top_idx]

        results.append({
            "document_id": d["document_id"],
            "filename": d["filename"],
            "text": d["text"],
            "score": best_score,
            "evidence_snippets": evidences,
            "warning": d.get("text_warning")
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max(1, top_k)]
