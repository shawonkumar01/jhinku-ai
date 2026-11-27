
"""Text cleaning and chunking.

Chunks are the unit that will later be embedded and stored in
pgvector for RAG retrieval.
"""

import re

DEFAULT_CHUNK_SIZE = 1000   # characters
DEFAULT_OVERLAP = 200       # characters of overlap between chunks


def clean_text(text: str) -> str:
    """Normalize whitespace and remove control characters."""
    # Remove control chars except newline/tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize whitespace on each line, collapse blank lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks of roughly chunk_size chars.

    Tries to break on paragraph/sentence boundaries where possible.
    """
    text = clean_text(text)
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Prefer breaking at a paragraph or sentence boundary
        # within the last 20% of the window.
        if end < len(text):
            window = text[start:end]
            boundary = max(
                window.rfind("\n\n"),
                window.rfind(". "),
                window.rfind("! "),
                window.rfind("? "),
            )
            if boundary > int(chunk_size * 0.8):
                end = start + boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # Next chunk starts `overlap` chars before this one ended,
        # snapped forward to a word boundary.
        next_start = max(end - overlap, start + 1)
        while next_start < len(text) and text[next_start] not in " \n":
            next_start += 1
        start = next_start

    return chunks
