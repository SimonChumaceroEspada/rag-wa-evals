def test_chunk_overlap():
    from src.chunk import chunk
    text = " ".join([f"w{i}" for i in range(2000)])
    chunks = chunk(text, size=600, overlap=100)
    assert len(chunks) >= 3
    assert chunks[1][:50] in chunks[0]  # overlap preserved


def test_chunks_never_cut_sentences():
    from src.chunk import chunk
    sents = [f"Oración {i} de la prueba con palabras de relleno suficientes aquí." for i in range(1, 41)]
    chunks = chunk(" ".join(sents), size=20, overlap=5)
    assert len(chunks) >= 2
    for c in chunks:
        assert c[0].isupper(), f"empieza a mitad de frase: {c[:60]}"
        assert c[-1] in ".!?", f"no cierra la frase: {c[-60:]}"
