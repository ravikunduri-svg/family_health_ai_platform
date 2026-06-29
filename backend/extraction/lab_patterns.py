"""
40+ regex patterns for Indian lab reports.
Covers CBC, Lipid, Thyroid, Liver, Kidney, Diabetes, Vitamins, Electrolytes, Urine.

Pattern structure:
  test_name   — normalized name stored in DB
  aliases     — list of strings/patterns to search for in report text (case-insensitive)
  unit        — expected/default unit
  ref_low     — typical lower reference bound (adult average; report range preferred)
  ref_high    — typical upper reference bound (adult average; report range preferred)

Extraction logic (in extractor.py):
  For each line in OCR text:
    For each pattern: if any alias matches → extract first float on the line as value
    Attempt to extract reference range from the same line (X.X - Y.Y or X.X–Y.Y)
"""

LAB_PATTERNS = [
    # ── Diabetes ────────────────────────────────────────────────────────────────
    {
        "test_name": "HbA1c",
        "aliases": ["hba1c", "hb a1c", "glycated haemoglobin", "glycated hemoglobin",
                    "glycosylated haemoglobin", "glycosylated hemoglobin", "a1c", "ghb"],
        "unit": "%",
        "ref_low": 4.0,
        "ref_high": 5.7,
    },
    {
        "test_name": "Fasting Blood Glucose",
        "aliases": ["fasting blood glucose", "fasting glucose", "fbg", "fasting blood sugar",
                    "fbs", "glucose fasting", "blood glucose fasting"],
        "unit": "mg/dL",
        "ref_low": 70.0,
        "ref_high": 99.0,
    },
    {
        "test_name": "Post-Prandial Blood Glucose",
        "aliases": ["post prandial", "postprandial", "pp blood glucose", "ppbs",
                    "2hr post glucose", "2 hour post glucose", "blood glucose pp"],
        "unit": "mg/dL",
        "ref_low": 70.0,
        "ref_high": 140.0,
    },
    {
        "test_name": "Random Blood Glucose",
        "aliases": ["random blood glucose", "random glucose", "rbs", "random blood sugar"],
        "unit": "mg/dL",
        "ref_low": 70.0,
        "ref_high": 140.0,
    },
    # ── Complete Blood Count (CBC) ───────────────────────────────────────────────
    {
        "test_name": "Hemoglobin",
        "aliases": ["haemoglobin", "hemoglobin", "hb", "hgb"],
        "unit": "g/dL",
        "ref_low": 11.5,
        "ref_high": 17.5,
    },
    {
        "test_name": "WBC",
        "aliases": ["wbc", "white blood cell", "white blood count", "total leucocyte",
                    "total leukocyte", "tlc", "total wbc"],
        "unit": "10^3/µL",
        "ref_low": 4.0,
        "ref_high": 11.0,
    },
    {
        "test_name": "RBC",
        "aliases": ["rbc", "red blood cell", "red blood count", "total rbc", "erythrocyte count"],
        "unit": "10^6/µL",
        "ref_low": 3.8,
        "ref_high": 5.8,
    },
    {
        "test_name": "Platelets",
        "aliases": ["platelet", "plt", "thrombocyte", "platelet count"],
        "unit": "10^3/µL",
        "ref_low": 150.0,
        "ref_high": 410.0,
    },
    {
        "test_name": "Hematocrit",
        "aliases": ["hematocrit", "haematocrit", "hct", "pcv", "packed cell volume"],
        "unit": "%",
        "ref_low": 36.0,
        "ref_high": 54.0,
    },
    {
        "test_name": "MCV",
        "aliases": ["mcv", "mean corpuscular volume", "mean cell volume"],
        "unit": "fL",
        "ref_low": 80.0,
        "ref_high": 100.0,
    },
    {
        "test_name": "MCH",
        "aliases": ["mch", "mean corpuscular haemoglobin", "mean corpuscular hemoglobin",
                    "mean cell haemoglobin"],
        "unit": "pg",
        "ref_low": 27.0,
        "ref_high": 32.0,
    },
    {
        "test_name": "MCHC",
        "aliases": ["mchc", "mean corpuscular haemoglobin concentration",
                    "mean cell haemoglobin concentration"],
        "unit": "g/dL",
        "ref_low": 32.0,
        "ref_high": 36.0,
    },
    {
        "test_name": "RDW",
        "aliases": ["rdw", "red cell distribution width", "rdw-cv", "rdw-sd"],
        "unit": "%",
        "ref_low": 11.5,
        "ref_high": 14.5,
    },
    {
        "test_name": "Neutrophils",
        "aliases": ["neutrophil", "neutrophils", "neutrophil %", "seg"],
        "unit": "%",
        "ref_low": 40.0,
        "ref_high": 75.0,
    },
    {
        "test_name": "Lymphocytes",
        "aliases": ["lymphocyte", "lymphocytes", "lymphocyte %"],
        "unit": "%",
        "ref_low": 20.0,
        "ref_high": 45.0,
    },
    {
        "test_name": "Eosinophils",
        "aliases": ["eosinophil", "eosinophils", "eosinophil %"],
        "unit": "%",
        "ref_low": 1.0,
        "ref_high": 6.0,
    },
    # ── Lipid Panel ─────────────────────────────────────────────────────────────
    {
        "test_name": "Total Cholesterol",
        "aliases": ["total cholesterol", "cholesterol total", "serum cholesterol",
                    "cholesterol"],
        "unit": "mg/dL",
        "ref_low": 0.0,
        "ref_high": 200.0,
    },
    {
        "test_name": "HDL Cholesterol",
        "aliases": ["hdl cholesterol", "hdl-c", "hdl", "high density lipoprotein",
                    "good cholesterol"],
        "unit": "mg/dL",
        "ref_low": 40.0,
        "ref_high": 999.0,
    },
    {
        "test_name": "LDL Cholesterol",
        "aliases": ["ldl cholesterol", "ldl-c", "ldl", "low density lipoprotein",
                    "bad cholesterol"],
        "unit": "mg/dL",
        "ref_low": 0.0,
        "ref_high": 100.0,
    },
    {
        "test_name": "VLDL Cholesterol",
        "aliases": ["vldl cholesterol", "vldl-c", "vldl", "very low density lipoprotein"],
        "unit": "mg/dL",
        "ref_low": 0.0,
        "ref_high": 30.0,
    },
    {
        "test_name": "Triglycerides",
        "aliases": ["triglyceride", "triglycerides", "tg", "serum triglycerides"],
        "unit": "mg/dL",
        "ref_low": 0.0,
        "ref_high": 150.0,
    },
    # ── Thyroid ─────────────────────────────────────────────────────────────────
    {
        "test_name": "TSH",
        "aliases": ["tsh", "thyroid stimulating hormone", "thyroid stimulatory hormone",
                    "thyrotropin"],
        "unit": "µIU/mL",
        "ref_low": 0.35,
        "ref_high": 4.94,
    },
    {
        "test_name": "T3 Total",
        "aliases": ["t3 total", "total t3", "triiodothyronine total", "t3"],
        "unit": "ng/dL",
        "ref_low": 60.0,
        "ref_high": 200.0,
    },
    {
        "test_name": "T4 Total",
        "aliases": ["t4 total", "total t4", "thyroxine total", "t4"],
        "unit": "µg/dL",
        "ref_low": 4.5,
        "ref_high": 12.5,
    },
    {
        "test_name": "Free T3",
        "aliases": ["free t3", "ft3", "free triiodothyronine"],
        "unit": "pg/mL",
        "ref_low": 2.3,
        "ref_high": 4.2,
    },
    {
        "test_name": "Free T4",
        "aliases": ["free t4", "ft4", "free thyroxine"],
        "unit": "ng/dL",
        "ref_low": 0.89,
        "ref_high": 1.76,
    },
    # ── Kidney Function ──────────────────────────────────────────────────────────
    {
        "test_name": "Creatinine",
        "aliases": ["creatinine", "serum creatinine", "creatinine serum"],
        "unit": "mg/dL",
        "ref_low": 0.6,
        "ref_high": 1.3,
    },
    {
        "test_name": "Urea",
        "aliases": ["urea", "blood urea", "bun", "blood urea nitrogen", "serum urea"],
        "unit": "mg/dL",
        "ref_low": 7.0,
        "ref_high": 45.0,
    },
    {
        "test_name": "Uric Acid",
        "aliases": ["uric acid", "serum uric acid", "ua"],
        "unit": "mg/dL",
        "ref_low": 3.5,
        "ref_high": 7.2,
    },
    {
        "test_name": "eGFR",
        "aliases": ["egfr", "estimated gfr", "glomerular filtration"],
        "unit": "mL/min/1.73m²",
        "ref_low": 60.0,
        "ref_high": 999.0,
    },
    # ── Liver Function ───────────────────────────────────────────────────────────
    {
        "test_name": "ALT",
        "aliases": ["alt", "sgpt", "alanine aminotransferase", "alanine transaminase"],
        "unit": "U/L",
        "ref_low": 0.0,
        "ref_high": 40.0,
    },
    {
        "test_name": "AST",
        "aliases": ["ast", "sgot", "aspartate aminotransferase", "aspartate transaminase"],
        "unit": "U/L",
        "ref_low": 0.0,
        "ref_high": 40.0,
    },
    {
        "test_name": "Alkaline Phosphatase",
        "aliases": ["alkaline phosphatase", "alp", "alk phos"],
        "unit": "U/L",
        "ref_low": 44.0,
        "ref_high": 147.0,
    },
    {
        "test_name": "Total Bilirubin",
        "aliases": ["total bilirubin", "bilirubin total", "serum bilirubin total"],
        "unit": "mg/dL",
        "ref_low": 0.0,
        "ref_high": 1.2,
    },
    {
        "test_name": "Direct Bilirubin",
        "aliases": ["direct bilirubin", "bilirubin direct", "conjugated bilirubin"],
        "unit": "mg/dL",
        "ref_low": 0.0,
        "ref_high": 0.3,
    },
    {
        "test_name": "Total Protein",
        "aliases": ["total protein", "serum total protein", "protein total"],
        "unit": "g/dL",
        "ref_low": 6.0,
        "ref_high": 8.3,
    },
    {
        "test_name": "Albumin",
        "aliases": ["albumin", "serum albumin"],
        "unit": "g/dL",
        "ref_low": 3.5,
        "ref_high": 5.0,
    },
    {
        "test_name": "GGT",
        "aliases": ["ggt", "gamma gt", "gamma glutamyl transferase", "ggtp"],
        "unit": "U/L",
        "ref_low": 0.0,
        "ref_high": 60.0,
    },
    # ── Electrolytes ─────────────────────────────────────────────────────────────
    {
        "test_name": "Sodium",
        "aliases": ["sodium", "serum sodium", "na+", "na"],
        "unit": "mEq/L",
        "ref_low": 136.0,
        "ref_high": 145.0,
    },
    {
        "test_name": "Potassium",
        "aliases": ["potassium", "serum potassium", "k+", " k "],
        "unit": "mEq/L",
        "ref_low": 3.5,
        "ref_high": 5.1,
    },
    {
        "test_name": "Chloride",
        "aliases": ["chloride", "serum chloride", "cl-"],
        "unit": "mEq/L",
        "ref_low": 98.0,
        "ref_high": 107.0,
    },
    {
        "test_name": "Calcium",
        "aliases": ["calcium", "serum calcium", "ca"],
        "unit": "mg/dL",
        "ref_low": 8.6,
        "ref_high": 10.3,
    },
    # ── Vitamins & Minerals ──────────────────────────────────────────────────────
    {
        "test_name": "Vitamin D",
        "aliases": ["vitamin d", "25-oh vitamin d", "25 oh vitamin d", "25-hydroxyvitamin",
                    "vit d", "vitamin d3"],
        "unit": "ng/mL",
        "ref_low": 30.0,
        "ref_high": 100.0,
    },
    {
        "test_name": "Vitamin B12",
        "aliases": ["vitamin b12", "vit b12", "cobalamin", "cyanocobalamin", "b12"],
        "unit": "pg/mL",
        "ref_low": 200.0,
        "ref_high": 900.0,
    },
    {
        "test_name": "Iron",
        "aliases": ["serum iron", "iron serum", " iron "],
        "unit": "µg/dL",
        "ref_low": 60.0,
        "ref_high": 170.0,
    },
    {
        "test_name": "Ferritin",
        "aliases": ["ferritin", "serum ferritin"],
        "unit": "ng/mL",
        "ref_low": 12.0,
        "ref_high": 300.0,
    },
    {
        "test_name": "TIBC",
        "aliases": ["tibc", "total iron binding capacity"],
        "unit": "µg/dL",
        "ref_low": 250.0,
        "ref_high": 370.0,
    },
    # ── Other ────────────────────────────────────────────────────────────────────
    {
        "test_name": "PSA",
        "aliases": ["psa", "prostate specific antigen", "total psa"],
        "unit": "ng/mL",
        "ref_low": 0.0,
        "ref_high": 4.0,
    },
    {
        "test_name": "CRP",
        "aliases": ["crp", "c reactive protein", "c-reactive protein", "hs-crp", "hscrp"],
        "unit": "mg/L",
        "ref_low": 0.0,
        "ref_high": 5.0,
    },
    {
        "test_name": "ESR",
        "aliases": ["esr", "erythrocyte sedimentation rate", "westergren"],
        "unit": "mm/hr",
        "ref_low": 0.0,
        "ref_high": 20.0,
    },
]
