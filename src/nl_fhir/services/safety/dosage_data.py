"""
Shared dosage reference data for DosageValidator.

Extracting the static datasets keeps the validator implementation
within the 500-line constitutional ceiling and makes it easier to
maintain dosage ranges and adjustment factors independently.
"""

from typing import Dict, List, Any, Tuple

DOSAGE_DATABASE: Dict[str, List[Dict[str, Any]]] = {
    "acetaminophen": [
        {
            "min_dose": 325,
            "max_dose": 4000,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "adult",
        },
        {
            "min_dose": 10,
            "max_dose": 15,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "child",
            "weight_based": True,
        },
        {
            "min_dose": 160,
            "max_dose": 3200,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "geriatric",
        },
    ],
    "ibuprofen": [
        {
            "min_dose": 400,
            "max_dose": 2400,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "adult",
        },
        {
            "min_dose": 5,
            "max_dose": 10,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "child",
            "weight_based": True,
        },
        {
            "min_dose": 400,
            "max_dose": 1600,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "geriatric",
        },
    ],
    "simvastatin": [
        {
            "min_dose": 10,
            "max_dose": 80,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "adult",
        },
        {
            "min_dose": 10,
            "max_dose": 40,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "geriatric",
        },
    ],
    "lisinopril": [
        {
            "min_dose": 2.5,
            "max_dose": 40,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "adult",
        },
        {
            "min_dose": 2.5,
            "max_dose": 20,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "geriatric",
        },
    ],
    "metformin": [
        {
            "min_dose": 500,
            "max_dose": 2550,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "adult",
        },
        {
            "min_dose": 500,
            "max_dose": 2000,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "geriatric",
        },
    ],
    "warfarin": [
        {
            "min_dose": 1,
            "max_dose": 15,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "adult",
        },
        {
            "min_dose": 1,
            "max_dose": 10,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "geriatric",
        },
    ],
    "digoxin": [
        {
            "min_dose": 0.125,
            "max_dose": 0.5,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "adult",
        },
        {
            "min_dose": 0.0625,
            "max_dose": 0.25,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "geriatric",
        },
    ],
    "amlodipine": [
        {
            "min_dose": 2.5,
            "max_dose": 10,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "adult",
        },
        {
            "min_dose": 2.5,
            "max_dose": 5,
            "unit": "mg",
            "frequency": "daily",
            "route": "oral",
            "age_group": "geriatric",
        },
    ],
}

AGE_WEIGHT_FACTORS: Dict[str, Dict[str, float]] = {
    "infant": {"dose_factor": 0.1, "weight_factor": 1.0},
    "child": {"dose_factor": 0.5, "weight_factor": 1.0},
    "adolescent": {"dose_factor": 0.8, "weight_factor": 1.0},
    "adult": {"dose_factor": 1.0, "weight_factor": 1.0},
    "geriatric": {"dose_factor": 0.75, "weight_factor": 1.0},
}

ROUTE_CONVERSIONS: Dict[Tuple[str, str], float] = {
    ("oral", "iv"): 0.5,   # IV typically 50% of oral dose
    ("iv", "oral"): 2.0,   # Oral typically 200% of IV dose
    ("im", "oral"): 1.5,   # IM typically 150% of oral dose
    ("oral", "im"): 0.67,  # Oral to IM conversion
}

UNIT_CONVERSIONS: Dict[Tuple[str, str], float] = {
    ("mg", "g"): 0.001,
    ("g", "mg"): 1000,
    ("mcg", "mg"): 0.001,
    ("mg", "mcg"): 1000,
    ("mcg", "g"): 0.000001,
    ("g", "mcg"): 1_000_000,
}

MONITORING_REQUIREMENTS: Dict[str, List[str]] = {
    "acetaminophen": ["Liver function tests", "Daily maximum dose tracking"],
    "ibuprofen": ["Kidney function", "GI symptoms"],
    "simvastatin": ["Liver function tests", "Muscle symptoms"],
    "lisinopril": ["Blood pressure", "Kidney function", "Potassium levels"],
    "metformin": ["Kidney function", "Blood glucose"],
    "warfarin": ["INR", "Bleeding signs"],
    "digoxin": ["Heart rate", "Digoxin levels", "Electrolytes"],
}

DEFAULT_MONITORING: List[str] = ["Vital signs", "Symptom monitoring"]
