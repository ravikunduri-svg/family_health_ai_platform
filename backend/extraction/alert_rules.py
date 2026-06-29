"""
Rule-based alert generation — no AI inference.
All rules are explicit thresholds or trend conditions.
Every alert generated here is auditable and reproducible.
"""
import logging
from datetime import date
from typing import Any

log = logging.getLogger(__name__)

# ── Single-value threshold rules ──────────────────────────────────────────────
# (test_name, threshold_type: "above"/"below", threshold, alert_title, description)
THRESHOLD_RULES: list[tuple] = [
    ("HbA1c",              "above", 6.5,   "HbA1c in Diabetic Range",
     "HbA1c ≥6.5% — meets diagnostic threshold for diabetes. Consult endocrinologist."),
    ("HbA1c",              "above", 5.7,   "HbA1c Pre-Diabetic",
     "HbA1c 5.7–6.4% — pre-diabetes range. Diet review recommended."),
    ("Fasting Blood Glucose", "above", 126.0, "Fasting Glucose Elevated",
     "Fasting glucose ≥126 mg/dL. Repeat test and consult physician."),
    ("Total Cholesterol",  "above", 240.0, "High Total Cholesterol",
     "Total cholesterol >240 mg/dL — high risk. Lipid-lowering review needed."),
    ("LDL Cholesterol",    "above", 160.0, "High LDL Cholesterol",
     "LDL >160 mg/dL. Discuss statin therapy with physician."),
    ("Triglycerides",      "above", 200.0, "High Triglycerides",
     "Triglycerides >200 mg/dL. Diet and lifestyle review recommended."),
    ("TSH",                "above", 5.0,   "TSH Elevated — Possible Hypothyroidism",
     "TSH >5.0 µIU/mL. Thyroid function review needed."),
    ("TSH",                "below", 0.35,  "TSH Low — Possible Hyperthyroidism",
     "TSH <0.35 µIU/mL. Thyroid function review needed."),
    ("Creatinine",         "above", 1.5,   "Creatinine Elevated",
     "Serum creatinine >1.5 mg/dL — possible kidney stress. Nephrology referral advised."),
    ("Hemoglobin",         "below", 10.0,  "Low Hemoglobin — Possible Anaemia",
     "Haemoglobin <10 g/dL — significant anaemia. Physician review needed."),
    ("Vitamin D",          "below", 20.0,  "Vitamin D Deficiency",
     "Vitamin D <20 ng/mL — deficient. Supplementation and sun exposure recommended."),
    ("Vitamin B12",        "below", 200.0, "Vitamin B12 Deficient",
     "Vitamin B12 <200 pg/mL. Supplementation and dietary review advised."),
    ("ALT",                "above", 56.0,  "ALT Elevated — Liver Stress",
     "ALT >56 U/L — possible liver inflammation. Alcohol, medication review needed."),
    ("AST",                "above", 56.0,  "AST Elevated — Liver Stress",
     "AST >56 U/L — possible liver stress. Review with physician."),
    ("Uric Acid",          "above", 7.5,   "High Uric Acid — Gout Risk",
     "Uric acid >7.5 mg/dL — hyperuricaemia. Dietary changes and hydration advised."),
    ("Potassium",          "above", 5.5,   "High Potassium — Hyperkalaemia",
     "Potassium >5.5 mEq/L — urgent. Physician review required."),
    ("Potassium",          "below", 3.0,   "Low Potassium — Hypokalaemia",
     "Potassium <3.0 mEq/L — urgent. Physician review required."),
    ("Sodium",             "above", 148.0, "High Sodium — Hypernatraemia",
     "Sodium >148 mEq/L. Hydration and physician review required."),
    ("Sodium",             "below", 132.0, "Low Sodium — Hyponatraemia",
     "Sodium <132 mEq/L — urgent. Physician review required."),
    ("PSA",                "above", 4.0,   "PSA Elevated",
     "PSA >4 ng/mL — urologist review recommended."),
    ("CRP",                "above", 10.0,  "High CRP — Inflammation Marker",
     "CRP >10 mg/L — significant inflammation. Physician review needed."),
]


def generate_alerts_from_lab_values(
    lab_rows: list[dict[str, Any]],
    member_id: str,
) -> list[dict[str, Any]]:
    """
    Given a list of newly extracted lab value rows, return alert dicts to insert.
    Uses threshold rules only — no AI inference.
    """
    alerts: list[dict[str, Any]] = []

    for row in lab_rows:
        test = row.get("test_name", "")
        value = row.get("value")
        doc_id = row.get("document_id")
        report_date = row.get("report_date")

        if value is None:
            continue

        for rule_test, rule_type, threshold, title, description in THRESHOLD_RULES:
            if test != rule_test:
                continue
            triggered = (
                (rule_type == "above" and float(value) >= threshold) or
                (rule_type == "below" and float(value) <= threshold)
            )
            if triggered:
                alerts.append({
                    "member_id": member_id,
                    "alert_type": "abnormal_value",
                    "title": title,
                    "description": description,
                    "due_date": str(report_date) if report_date else None,
                    "source_doc_id": doc_id,
                    "is_dismissed": False,
                })

    return alerts


def generate_alerts_from_medicines(
    medicine_rows: list[dict[str, Any]],
    member_id: str,
) -> list[dict[str, Any]]:
    """
    Check for medicines with duration_days set and flag renewal if near expiry.
    Prescription renewal alert: when duration_days is set and we're past the end date.
    """
    alerts: list[dict[str, Any]] = []
    today = date.today()

    for med in medicine_rows:
        duration_days = med.get("duration_days")
        prescribed_date = med.get("prescribed_date")
        brand = med.get("brand_name") or med.get("generic_name") or "Medicine"

        if not duration_days or not prescribed_date:
            continue

        try:
            if isinstance(prescribed_date, str):
                from datetime import datetime
                start = datetime.strptime(prescribed_date, "%Y-%m-%d").date()
            else:
                start = prescribed_date
            from datetime import timedelta
            end_date = start + timedelta(days=duration_days)
            if today >= end_date:
                alerts.append({
                    "member_id": member_id,
                    "alert_type": "medicine_renewal",
                    "title": f"Prescription Renewal Due: {brand}",
                    "description": (
                        f"{brand} prescription (started {start}) ended {end_date}. "
                        "Check if renewal is needed."
                    ),
                    "due_date": str(end_date),
                    "source_doc_id": med.get("document_id"),
                    "is_dismissed": False,
                })
        except Exception:
            log.debug("Could not compute renewal date for medicine %s", med.get("id"))

    return alerts
