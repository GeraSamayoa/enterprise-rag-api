from pathlib import Path

from pypdf import PdfReader


SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = SUPPORTED_TEXT_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS


def extract_text_from_file(file_path: str) -> tuple[str, dict]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in SUPPORTED_TEXT_EXTENSIONS:
        text = path.read_text(encoding="utf-8")
        return text, {
            "file_name": path.name,
            "extension": suffix,
        }

    if suffix in SUPPORTED_PDF_EXTENSIONS:
        reader = PdfReader(file_path)
        pages_text: list[str] = []

        for index, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages_text.append(f"[PAGE {index}]\n{page_text}")

        return "\n\n".join(pages_text), {
            "file_name": path.name,
            "extension": suffix,
            "page_count": len(reader.pages),
        }

    raise ValueError(f"Unsupported file extension: {suffix}")