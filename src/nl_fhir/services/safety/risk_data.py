"""
Shared reference data for safety risk scoring.
"""

from typing import Dict

RISK_WEIGHTS: Dict[str, float] = {
    "drug_interactions": 0.25,
    "contraindications": 0.22,
    "dosage_concerns": 0.20,
    "patient_complexity": 0.15,
    "monitoring_requirements": 0.10,
    "medication_burden": 0.08,
}

HIGH_MONITORING_MEDICATIONS: Dict[str, str] = {
    "warfarin": "INR monitoring every 1-2 weeks",
    "digoxin": "Digoxin levels and electrolyte monitoring",
    "lithium": "Lithium levels every 3-6 months",
    "metformin": "Kidney function monitoring every 3-6 months",
}
