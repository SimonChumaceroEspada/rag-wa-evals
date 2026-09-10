def chunk(text: str, size: int = 600, overlap: int = 100) -> list[str]:
    """Split text into word-based chunks with overlap."""
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    chunks = []
    for i in range(0, len(words), step):
        part = words[i : i + size]
        if not part:
            break
        chunks.append(" ".join(part))
        if i + size >= len(words):
            break
    return chunks
