"""Híbrido denso (Qdrant) + BM25 (palabras exactas) con fusión RRF.

Los ids de chunk son md5-hex en UUID (idénticos a ingest) para fusionar.
"""

import hashlib
import re
import unicodedata
import uuid

from rank_bm25 import BM25Okapi

RRF_K = 60
_INDEX_CACHE: dict = {}


def tokenize(text: str) -> list[str]:
    s = unicodedata.normalize("NFD", text.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.findall(r"\w+", s)


def chunk_id(text: str) -> str:
    return str(uuid.UUID(hex=hashlib.md5(text.encode()).hexdigest()))


def build_fixture_index(docs: list[str]) -> dict:
    return {
        "bm25": BM25Okapi([tokenize(d) for d in docs]),
        "ids": list(range(len(docs))),
        "texts": docs,
    }


def build_index(lang: str) -> dict:
    from src.chunk import chunk
    from src.ingest import collect_lang_files, read_doc_text

    ids, texts, sources = [], [], []
    for f in collect_lang_files(lang):
        t = read_doc_text(f)
        if not t.strip():
            continue
        for c in chunk(t, size=600, overlap=100):
            ids.append(chunk_id(c))
            texts.append(c)
            sources.append(f.name)
    # dedup por id (mismo chunk en .md+PDF espejo): conserva primero
    seen, uids, utexts, usrc = set(), [], [], []
    for i, t, s in zip(ids, texts, sources):
        if i not in seen:
            seen.add(i)
            uids.append(i)
            utexts.append(t)
            usrc.append(s)
    return {
        "bm25": BM25Okapi([tokenize(t) for t in utexts]),
        "ids": uids,
        "texts": utexts,
        "sources": usrc,
    }


def get_index(lang: str) -> dict:
    if lang not in _INDEX_CACHE:
        _INDEX_CACHE[lang] = build_index(lang)
    return _INDEX_CACHE[lang]


def search_bm25(idx: dict, query: str, k: int = 10) -> list[tuple]:
    scores = idx["bm25"].get_scores(tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    return [(idx["ids"][i], float(scores[i])) for i in ranked[:k] if scores[i] > 0]


def rrf_fuse(dense: list[tuple], bm25: list[tuple], k: int = RRF_K) -> list[tuple]:
    """Reciprocal Rank Fusion: 1/(k+rank). Desempata: rank denso, luego BM25."""
    acc: dict = {}
    for rank, (i, _) in enumerate(dense, 1):
        d = acc.setdefault(i, {"s": 0.0, "dr": rank, "br": 10**9})
        d["s"] += 1.0 / (k + rank)
    for rank, (i, _) in enumerate(bm25, 1):
        d = acc.setdefault(i, {"s": 0.0, "dr": 10**9, "br": rank})
        d["s"] += 1.0 / (k + rank)
        d["br"] = min(d["br"], rank)
    return sorted(acc.items(), key=lambda kv: (-kv[1]["s"], kv[1]["dr"], kv[1]["br"], str(kv[0])))


def hybrid_search(client, lang: str, qvec: list[float], qtext: str,
                  k_dense: int = 10, k_bm25: int = 10, k_final: int = 5) -> list[dict]:
    col = f"docs_{lang}"
    dhits = client.query_points(collection_name=col, query=qvec, limit=k_dense).points
    dense = [(str(h.id), float(h.score)) for h in dhits]
    idx = get_index(lang)
    bm25 = search_bm25(idx, qtext, k=k_bm25)
    fused = rrf_fuse(dense, bm25)[:k_final]
    ids = [i for i, _ in fused]
    found = {str(p.id): p for p in client.retrieve(collection_name=col, ids=ids)} if ids else {}
    out = []
    for i, meta in fused:
        p = found.get(i)
        if p is None:
            continue
        out.append({
            "text": p.payload.get("text", ""),
            "source": p.payload.get("source", ""),
            "score": meta["s"],
        })
    return out
