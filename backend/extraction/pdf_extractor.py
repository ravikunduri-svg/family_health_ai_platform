"""Stage 1 OCR for PDF files — pdfplumber → raw text."""
import io
import logging

log = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF byte stream.
    Returns concatenated page text separated by newlines.
    Raises ValueError if the file cannot be read as PDF.
    """
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber is not installed. Add it to requirements.txt.")

    pages_text: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
    except Exception as exc:
        log.error("PDF extraction failed: %s", type(exc).__name__)
        raise ValueError(f"Could not extract text from PDF: {exc}") from exc

    if not pages_text:
        return ""

    return "\n".join(pages_text)
