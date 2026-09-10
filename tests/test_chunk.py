def test_chunk_overlap():
    from src.chunk import chunk
    text = " ".join([f"w{i}" for i in range(2000)])
    chunks = chunk(text, size=600, overlap=100)
    assert len(chunks) >= 3
    assert chunks[1][:50] in chunks[0]  # overlap preserved
