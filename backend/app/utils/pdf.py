import fitz
from pathlib import Path


def extract_text(pdf_source: str | bytes) -> str:
    """
    Extract all text from a PDF file path or raw PDF bytes.
    """
    try:
        if isinstance(pdf_source, bytes):
            document = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            resolved_path = str(Path(pdf_source).resolve())
            document = fitz.open(resolved_path)

        pages = []
        for page in document:
            text = page.get_text()
            if text:
                pages.append(text)

        document.close()
        return "\n".join(pages)
    except Exception as e:
        raise ValueError(f"Could not read PDF file: {str(e)}")