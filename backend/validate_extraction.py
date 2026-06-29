"""
Phase 0 Extraction Validation Script
=====================================
Run this BEFORE using the system in production.
Target: >85% accuracy on lab values, <30% miss rate on medicines.

Usage:
  python validate_extraction.py path/to/report.pdf
  python validate_extraction.py path/to/reports/   (process all PDFs in folder)
  python validate_extraction.py report.pdf --ai    (also run Stage 2 AI extraction)

Output:
  - Extracted lab values printed to console
  - Pass/fail accuracy score
  - Saved to extraction_validation_<timestamp>.txt

HIPAA note: Do not use real patient documents for validation tests.
Use anonymized or synthetic documents.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def extract_pdf(path: Path) -> str:
    try:
        from extraction.pdf_extractor import extract_text_from_pdf
        return extract_text_from_pdf(path.read_bytes())
    except Exception as exc:
        return f"[ERROR] PDF extraction failed: {exc}"


def extract_labs(raw_text: str) -> list[dict]:
    from extraction.extractor import _extract_lab_values
    return _extract_lab_values(raw_text, "VALIDATION", "VALIDATION", None)


def run_ai(raw_text: str) -> dict:
    from extraction.ai_extractor import extract_unstructured
    return extract_unstructured(raw_text)


def score_labs(extracted: list[dict], expected_tests: list[str]) -> dict:
    """
    Compare extracted test names against a list of expected test names.
    Returns hit rate and missed tests.
    """
    found = {row["test_name"] for row in extracted}
    hits = [t for t in expected_tests if t in found]
    misses = [t for t in expected_tests if t not in found]
    pct = (len(hits) / len(expected_tests) * 100) if expected_tests else 0
    return {"found": hits, "missed": misses, "accuracy_pct": round(pct, 1)}


def validate_file(path: Path, run_ai_flag: bool) -> dict:
    print(f"\n{'='*60}")
    print(f"File: {path.name}")
    print("─" * 60)

    raw_text = extract_pdf(path)
    if raw_text.startswith("[ERROR]"):
        print(raw_text)
        return {"file": path.name, "error": raw_text}

    print(f"OCR: extracted {len(raw_text)} characters from {path.name}")
    print()

    labs = extract_labs(raw_text)
    print(f"Stage 1 (Regex) — {len(labs)} lab values found:")
    for lab in labs:
        abnormal_flag = " *** ABNORMAL ***" if lab.get("is_abnormal") else ""
        print(f"  {lab['test_name']:<30} {lab['value']:<10} {lab.get('unit',''):<15} ref: {lab.get('reference_low','')}-{lab.get('reference_high','')}{abnormal_flag}")

    result = {
        "file": path.name,
        "char_count": len(raw_text),
        "lab_values": labs,
        "ai_extraction": None,
    }

    if run_ai_flag:
        print("\nStage 2 (Claude AI) — running extraction...")
        ai = run_ai(raw_text)
        print(f"  Diagnoses: {ai.get('diagnoses', [])}")
        print(f"  Medicines: {len(ai.get('medicines', []))} found")
        for med in ai.get("medicines", []):
            print(f"    - {med.get('brand','?')} ({med.get('generic','?')}) {med.get('dose','?')} {med.get('frequency','?')}")
        print(f"  Doctor: {ai.get('doctor')}")
        print(f"  Facility: {ai.get('facility')}")
        print(f"  Dates: {ai.get('dates')}")
        result["ai_extraction"] = ai

    return result


def main():
    parser = argparse.ArgumentParser(description="Phase 0 extraction validation")
    parser.add_argument("path", help="PDF file or folder of PDFs")
    parser.add_argument("--ai", action="store_true", help="Also run Stage 2 AI extraction")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"ERROR: {target} does not exist")
        sys.exit(1)

    if target.is_dir():
        pdf_files = list(target.glob("*.pdf")) + list(target.glob("*.PDF"))
        if not pdf_files:
            print(f"No PDF files found in {target}")
            sys.exit(1)
    else:
        pdf_files = [target]

    print(f"Validating {len(pdf_files)} file(s) — AI extraction: {'YES' if args.ai else 'NO'}")
    print("NOTE: Use anonymized/synthetic documents only — not real patient PHI.\n")

    all_results = []
    for f in pdf_files:
        result = validate_file(f, args.ai)
        all_results.append(result)

    # Summary
    total_labs = sum(len(r.get("lab_values", [])) for r in all_results)
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(all_results)} files, {total_labs} total lab values extracted")
    print()
    print("PASS/FAIL CRITERIA (Phase 0 gate):")
    avg_per_doc = total_labs / len(all_results) if all_results else 0
    if avg_per_doc >= 5:
        print(f"  Lab extraction: PASS (avg {avg_per_doc:.1f} values/doc — expected ≥5 for blood reports)")
    else:
        print(f"  Lab extraction: NEEDS REVIEW (avg {avg_per_doc:.1f} values/doc — check regex patterns)")

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(f"extraction_validation_{timestamp}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Phase 0 Extraction Validation — {timestamp}\n")
        f.write(f"Files tested: {len(all_results)}\n\n")
        for r in all_results:
            f.write(f"File: {r['file']}\n")
            if r.get("error"):
                f.write(f"  ERROR: {r['error']}\n")
            else:
                f.write(f"  OCR chars: {r['char_count']}\n")
                f.write(f"  Lab values ({len(r['lab_values'])}):\n")
                for lab in r.get("lab_values", []):
                    f.write(f"    {lab['test_name']}: {lab['value']} {lab.get('unit','')}\n")
                if r.get("ai_extraction"):
                    f.write(f"  AI: {json.dumps(r['ai_extraction'], indent=2)}\n")
            f.write("\n")
    print(f"\nReport saved to: {report_path}")
    print("\nNext step: manually verify each extracted value against the original document.")
    print("Target: >85% correct on known blood report format before building on top of extraction.")


if __name__ == "__main__":
    main()
