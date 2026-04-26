from app.rag.chunking.text_chunker import chunk_text


def test_chunk_text_returns_chunks() -> None:
    text = (
        "Análisis financiero Q2 2026. "
        "El margen operativo presentó presión por costos logísticos. "
        "Recomendaciones: revisar descuentos y renegociar proveedores."
    )

    chunks = chunk_text(
        text=text,
        chunk_size=80,
        chunk_overlap=20,
        min_chunk_size=20,
    )

    assert len(chunks) >= 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text
    assert chunks[0].char_count == len(chunks[0].text)


def test_chunk_text_does_not_return_empty_chunks() -> None:
    chunks = chunk_text(
        text="     ",
        chunk_size=100,
        chunk_overlap=20,
    )

    assert chunks == []


def test_chunk_overlap_must_be_smaller_than_chunk_size() -> None:
    try:
        chunk_text(
            text="Texto de prueba",
            chunk_size=100,
            chunk_overlap=100,
        )
    except ValueError as exc:
        assert str(exc) == "chunk_overlap must be smaller than chunk_size"
    else:
        raise AssertionError("Expected ValueError")