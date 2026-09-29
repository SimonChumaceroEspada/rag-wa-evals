import re

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _sentences(text: str) -> list[str]:
    parts = _SENT_SPLIT.split((text or "").strip())
    return [re.sub(r"\s+", " ", p).strip() for p in parts if p.strip()]


def _word_chunks(words: list[str], size: int, overlap: int) -> list[str]:
    """Último recurso para 'oraciones' gigantes sin puntuación (p. ej. tablas)."""
    step = max(1, size - overlap)
    out = []
    for i in range(0, len(words), step):
        part = words[i : i + size]
        if not part:
            break
        out.append(" ".join(part))
        if i + size >= len(words):
            break
    return out


def chunk(text: str, size: int = 600, overlap: int = 100) -> list[str]:
    """Chunks que respetan frases: cada uno empieza y termina en una oración completa.

    Así el contexto que ve el LLM (y el fallback extractivo) nunca arranca a mitad
    de frase, que era lo que producía respuestas como "hour). Daily - async standup…".
    """
    sents = _sentences(text)
    if not sents:
        return []

    chunks: list[str] = []
    cur: list[str] = []
    cur_w = 0

    def flush(carry_overlap: bool) -> None:
        nonlocal cur, cur_w
        if not cur:
            return
        body = " ".join(cur)
        if not chunks or body != chunks[-1]:
            chunks.append(body)
        if not carry_overlap:
            cur, cur_w = [], 0
            return
        keep: list[str] = []
        kw = 0
        for s in reversed(cur):
            keep.insert(0, s)
            kw += len(s.split())
            if kw >= overlap:
                break
        cur, cur_w = keep, kw

    for s in sents:
        sw = len(s.split())
        if sw > size:
            flush(True)
            for oc in _word_chunks(s.split(), size, overlap):
                if oc and (not chunks or oc != chunks[-1]):
                    chunks.append(oc)
            cur, cur_w = [], 0
            continue
        if cur and cur_w + sw > size:
            flush(True)
        cur.append(s)
        cur_w += sw

    flush(False)
    return chunks
