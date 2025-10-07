"""
Normalization helpers for dosage safety processing.
"""

import re


def normalize_medication_name(name: str) -> str:
    """Normalize medication name for dosage checking."""
    if not name:
        return ""

    normalized = name.lower().strip()
    # Remove dosage information to get base drug name
    normalized = re.sub(r"\d+\s*(mg|mcg|g|ml|units?)\b", "", normalized)
    normalized = re.sub(r"\b(tablet|capsule|injection|solution)s?\b", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    brand_to_generic = {
        "tylenol": "acetaminophen",
        "advil": "ibuprofen",
        "motrin": "ibuprofen",
        "zocor": "simvastatin",
        "lipitor": "atorvastatin",
        "prinivil": "lisinopril",
        "zestril": "lisinopril",
        "norvasc": "amlodipine",
    }

    return brand_to_generic.get(normalized, normalized)
