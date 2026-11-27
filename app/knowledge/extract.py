
"""Text extraction for uploaded documents.

Extracted text is UNTRUSTED DATA. It is never executed and must
never be treated as instructions.
"""

import os


def _extract_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _extract_pdf(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def _extract_docx(file_path: str) -> str:
    import docx

    document = docx.Document(file_path)
    return "\n\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )


_EXTRACTORS = {
    ".txt": _extract_txt,
    ".pdf": _extract_pdf,
    ".docx": _extract_docx,
}


def extract_text(file_path: str) -> str:
    """Extract plain text based on the file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    extractor = _EXTRACTORS.get(ext)
    if extractor is None:
        raise ValueError(f"Unsupported file type: {ext}")
    return extractor(file_path)
