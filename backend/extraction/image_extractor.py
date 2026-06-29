"""Stage 1 OCR for image files — pytesseract → raw text."""
import io
import logging

log = logging.getLogger(__name__)

# Tesseract config tuned for lab report layout (assume mostly text, column format)
_TESSERACT_CONFIG = "--oem 3 --psm 6"


def extract_text_from_image(file_bytes: bytes) -> str:
    """
    Extract text from an image byte stream using Tesseract OCR.
    Raises RuntimeError if Tesseract is not installed.
    Raises ValueError if the image cannot be processed.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise RuntimeError(
            "pytesseract or Pillow is not installed. Add them to requirements.txt."
        )

    try:
        image = Image.open(io.BytesIO(file_bytes))
        # Convert to RGB if needed (handles RGBA, palette mode, etc.)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        text = pytesseract.image_to_string(image, config=_TESSERACT_CONFIG)
        return text or ""
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract binary not found. Install with: apt-get install tesseract-ocr "
            "or on Windows: choco install tesseract"
        )
    except Exception as exc:
        log.error("Image OCR failed: %s", type(exc).__name__)
        raise ValueError(f"Could not extract text from image: {exc}") from exc
