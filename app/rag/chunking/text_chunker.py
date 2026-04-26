import re
from dataclasses import dataclass


@dataclass
class ChunkResult:
    chunk_index: int
    text: str
    char_count: int


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _split_into_sentences(text: str) -> list[str]:
    """
    Divide el texto en oraciones simples.
    Mantiene signos como punto, signo de interrogación y exclamación.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _build_overlap_text(previous_chunk: str, chunk_overlap: int) -> str:
    if chunk_overlap <= 0 or not previous_chunk:
        return ""

    overlap_text = previous_chunk[-chunk_overlap:].strip()

    # Evitar empezar en media palabra
    first_space = overlap_text.find(" ")
    if first_space != -1:
        overlap_text = overlap_text[first_space + 1 :].strip()

    return overlap_text


def chunk_text(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 100,
    min_chunk_size: int = 120,
) -> list[ChunkResult]:
    cleaned = _normalize_text(text)
    if not cleaned:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    sentences = _split_into_sentences(cleaned)

    # Fallback por si el texto no tiene puntuación
    if len(sentences) <= 1:
        return _chunk_by_characters(
            text=cleaned,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
        )

    raw_chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            raw_chunks.append(current)

        # Si una oración sola es demasiado grande, usar fallback por caracteres para esa oración
        if len(sentence) > chunk_size:
            overflow_chunks = _chunk_by_characters(
                text=sentence,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                min_chunk_size=min_chunk_size,
            )
            raw_chunks.extend([chunk.text for chunk in overflow_chunks])
            current = ""
        else:
            current = sentence

    if current:
        raw_chunks.append(current)

    # Unir último chunk si queda demasiado pequeño
    if len(raw_chunks) >= 2 and len(raw_chunks[-1]) < min_chunk_size:
        raw_chunks[-2] = f"{raw_chunks[-2]} {raw_chunks[-1]}".strip()
        raw_chunks.pop()

    chunks: list[ChunkResult] = []

    for index, raw_chunk in enumerate(raw_chunks):
        if index == 0 or chunk_overlap <= 0:
            final_text = raw_chunk
        else:
            overlap_text = _build_overlap_text(raw_chunks[index - 1], chunk_overlap)
            final_text = f"{overlap_text} {raw_chunk}".strip()

            if len(final_text) > chunk_size:
                final_text = final_text[-chunk_size:].strip()
                first_space = final_text.find(" ")
                if first_space != -1:
                    final_text = final_text[first_space + 1 :].strip()

        chunks.append(
            ChunkResult(
                chunk_index=index,
                text=final_text,
                char_count=len(final_text),
            )
        )

    return chunks


def _chunk_by_characters(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int,
) -> list[ChunkResult]:
    chunks: list[ChunkResult] = []
    start = 0
    index = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        if end < text_length:
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space

        chunk = text[start:end].strip()

        remaining = text_length - end
        if remaining < min_chunk_size and end < text_length:
            chunk = text[start:text_length].strip()
            end = text_length

        if chunk:
            chunks.append(
                ChunkResult(
                    chunk_index=index,
                    text=chunk,
                    char_count=len(chunk),
                )
            )
            index += 1

        if end >= text_length:
            break

        start = max(end - chunk_overlap, 0)

        # Evitar empezar en media palabra
        while start < text_length and start > 0 and text[start - 1] != " ":
            start += 1

    return chunks