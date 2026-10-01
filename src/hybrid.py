"""Híbrido denso (Qdrant) + BM25 (palabras exactas) con fusión RRF.

Los ids de chunk son md5-hex en UUID (idénticos a ingest) para fusionar.
"""

import hashlib
import os
import pathlib
import pickle
import re
import unicodedata
import uuid

from rank_bm25 import BM25Okapi

RRF_K = 60
_INDEX_CACHE: dict = {}
_INDEX_DIR = os.environ.get("HYBRID_CACHE_DIR", "/tmp" if os.name != "nt" else os.getenv("TEMP", "/tmp"))


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


def _make_index(ids: list, texts: list[str], sources: list[str]) -> dict:
    """Dedup por id (mismo chunk en .md+PDF espejo): conserva el primero."""
    seen, uids, utexts, usrc = set(), [], [], []
    for i, t, s in zip(ids, texts, sources):
        if i in seen:
            continue
        seen.add(i)
        uids.append(i)
        utexts.append(t)
        usrc.append(s)
    return {
        # colección vacía: bm25 None en vez de BM25Okapi([]) que revienta
        "bm25": BM25Okapi([tokenize(t) for t in utexts]) if utexts else None,
        "ids": uids,
        "texts": utexts,
        "sources": usrc,
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
    return _make_index(ids, texts, sources)


def build_index_from_collection(client, lang: str) -> dict:
    """BM25 desde los payloads de Qdrant.

    El deploy (Render) no lleva los PDFs —están en .gitignore—, así que indexar
    el disco dejaba el corpus vacío, BM25Okapi([]) explotaba y la API caía al
    fallback denso sin rerank.
    """
    col = f"docs_{lang}"
    ids, texts, sources = [], [], []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=col,
            limit=256,
            offset=offset,
            with_payload=["text", "source"],
            with_vectors=False,
        )
        for p in points:
            payload = p.payload or {}
            t = payload.get("text", "")
            if not t:
                continue
            ids.append(str(p.id))
            texts.append(t)
            sources.append(payload.get("source", ""))
        if offset is None:
            break
    return _make_index(ids, texts, sources)


def _cache_paths(lang: str):
    import pathlib

    d = pathlib.Path(_INDEX_DIR) / "rag-wa-bm25"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{lang}.pkl", d / f"{lang}.meta.json"


def get_index(lang: str, client=None) -> dict:
    """Índice BM25.

    Con ``client`` sale de los payloads de Qdrant (fuente de verdad: es lo que
    realmente se puede recuperar). Sin él, de los archivos locales — sólo para
    uso offline / tests.
    """
    import json

    if lang in _INDEX_CACHE:
        return _INDEX_CACHE[lang]

    pkl, meta = _cache_paths(lang)
    if client is not None:
        n = int(getattr(client.get_collection(f"docs_{lang}"), "points_count", -1))
        sig = {"src": "qdrant", "n": n}
    else:
        from src.ingest import collect_lang_files

        files = sorted(str(f) for f in collect_lang_files(lang))
        sig = {
            "src": "files",
            "files": files,
            "mtimes": [pathlib.Path(f).stat().st_mtime for f in files],
        }
    try:
        if pkl.exists() and json.loads(meta.read_text()) == sig:
            with open(pkl, "rb") as fh:
                idx = pickle.load(fh)
            idx["bm25"] = BM25Okapi([tokenize(t) for t in idx["texts"]]) if idx["texts"] else None
            _INDEX_CACHE[lang] = idx
            print(f"bm25 {lang}: índice desde caché ({len(idx['texts'])} chunks)")
            return idx
    except Exception as e:
        print(f"bm25 caché inválida ({e.__class__.__name__}), reconstruyo")
    idx = build_index_from_collection(client, lang) if client is not None else build_index(lang)
    try:
        with open(pkl, "wb") as fh:
            pickle.dump({k: v for k, v in idx.items() if k != "bm25"}, fh)
        meta.write_text(json.dumps(sig))
    except Exception as e:
        print(f"bm25 no se pudo cachear ({e.__class__.__name__})")
    _INDEX_CACHE[lang] = idx
    return idx


def search_bm25(idx: dict, query: str, k: int = 10) -> list[tuple]:
    if idx.get("bm25") is None:
        return []
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
    idx = get_index(lang, client)
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
