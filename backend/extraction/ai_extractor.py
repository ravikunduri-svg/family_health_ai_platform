"""
Stage 2 AI extraction — sends raw OCR text to Groq and returns structured JSON.

IMPORTANT: Every output from this module is informational only.
Do NOT use extracted data for clinical decisions without physician review.
"""
import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

_MODEL = "llama-3.3-70b-versatile"  # Groq free tier; strong JSON instruction following
_MAX_INPUT_CHARS = 6000   # Truncate raw text before sending
_MAX_TOKENS = 1500

_EXTRACTION_PROMPT = """\
You are a medical document parser. Extract structured information from the following \
Indian medical document text.

Return ONLY a valid JSON object with exactly this structure — no markdown, no explanation:
{
  "diagnoses": ["list of diagnoses or conditions explicitly mentioned"],
  "medicines": [
    {
      "brand": "brand name as written",
      "generic": "generic/INN name if you can identify it, else null",
      "dose": "dosage e.g. 500mg, null if not found",
      "frequency": "e.g. twice daily, null if not found",
      "duration": "e.g. 7 days, null if not found"
    }
  ],
  "doctor": "doctor name if present, else null",
  "facility": "hospital or lab name if present, else null",
  "dates": {
    "report": "date of report in YYYY-MM-DD, null if not found",
    "followup": "followup date in YYYY-MM-DD, null if not found"
  },
  "procedures": ["list of procedures, tests ordered, or surgeries mentioned"],
  "symptoms": ["list of symptoms or complaints mentioned"]
}

Rules:
- Only include what is EXPLICITLY stated. Do not infer or guess.
- For medicine generic names: only fill if you are confident — use null otherwise.
- For dates: Indian format is often DD-MM-YYYY or DD/MM/YYYY — convert to YYYY-MM-DD.
- If nothing is found for a field, use null or empty array.

Document text:
{text}
"""


def extract_unstructured(raw_text: str) -> dict[str, Any]:
    """
    Send raw OCR text to Groq and return parsed extraction dict.
    Returns empty structure on failure rather than raising (allows pipeline to continue).
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        log.warning("GROQ_API_KEY not set — skipping AI extraction")
        return _empty_extraction()

    try:
        from groq import Groq
    except ImportError:
        log.error("groq package not installed")
        return _empty_extraction()

    truncated = raw_text[:_MAX_INPUT_CHARS]
    prompt = _EXTRACTION_PROMPT.replace("{text}", truncated)

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = completion.choices[0].message.content.strip()
        log.debug("AI extractor raw response (first 200 chars): %s", response_text[:200])

        # Extract JSON object from response — handles markdown fences and preamble text
        import re as _re
        json_match = _re.search(r"\{.*\}", response_text, _re.DOTALL)
        if not json_match:
            log.error("AI extractor: no JSON object found in Groq response")
            return _empty_extraction()
        json_text = json_match.group(0)

        result = json.loads(json_text)
        if not isinstance(result, dict):
            log.error("AI extractor: parsed JSON is not a dict (got %s)", type(result).__name__)
            return _empty_extraction()
        return _validate_structure(result)
    except json.JSONDecodeError as exc:
        log.error("AI extractor: Groq returned invalid JSON — %s", exc)
        return _empty_extraction()
    except Exception as exc:
        log.error("AI extractor failed: %s — %s", type(exc).__name__, exc)
        return _empty_extraction()


def _empty_extraction() -> dict[str, Any]:
    return {
        "diagnoses": [],
        "medicines": [],
        "doctor": None,
        "facility": None,
        "dates": {"report": None, "followup": None},
        "procedures": [],
        "symptoms": [],
    }


def _validate_structure(raw: dict) -> dict[str, Any]:
    """Ensure required keys exist; fill missing with defaults."""
    empty = _empty_extraction()
    return {
        "diagnoses": raw.get("diagnoses") or [],
        "medicines": raw.get("medicines") or [],
        "doctor": raw.get("doctor"),
        "facility": raw.get("facility"),
        "dates": raw.get("dates") or empty["dates"],
        "procedures": raw.get("procedures") or [],
        "symptoms": raw.get("symptoms") or [],
    }
