"""
Shared contraindication datasets used by ContraindicationChecker.

Separating the data structures keeps the checker module within the
constitutional 500-line limit while centralizing reference data for reuse.
"""

from typing import Dict, Any

CONTRAINDICATIONS: Dict[str, Dict[str, Any]] = {
    # Cardiovascular contraindications
    "metoprolol+asthma": {
        "severity": "absolute",
        "reason": "Beta-blockers can cause severe bronchospasm in asthma",
        "alternatives": ["Calcium channel blockers", "ACE inhibitors"],
        "monitoring": ["Respiratory function"],
        "evidence_level": "high",
    },
    "propranolol+asthma": {
        "severity": "absolute",
        "reason": "Non-selective beta-blocker contraindicated in asthma",
        "alternatives": [
            "Cardioselective beta-blockers if essential",
            "Alternative antihypertensives",
        ],
        "monitoring": ["Respiratory function"],
        "evidence_level": "high",
    },
    "diltiazem+heart failure": {
        "severity": "relative",
        "reason": "Negative inotropic effect may worsen heart failure",
        "alternatives": ["ACE inhibitors", "ARBs", "Beta-blockers"],
        "monitoring": ["Left ventricular function", "Symptoms"],
        "evidence_level": "high",
    },
    # Kidney disease contraindications
    "metformin+kidney disease": {
        "severity": "absolute",
        "reason": "Risk of lactic acidosis with reduced kidney function",
        "alternatives": ["Insulin", "Sulfonylureas", "DPP-4 inhibitors"],
        "monitoring": ["Kidney function"],
        "evidence_level": "high",
    },
    "nsaid+kidney disease": {
        "severity": "relative",
        "reason": "Further reduction in kidney function",
        "alternatives": ["Acetaminophen", "Topical analgesics"],
        "monitoring": ["Serum creatinine", "BUN"],
        "evidence_level": "high",
    },
    # Liver disease contraindications
    "acetaminophen+liver disease": {
        "severity": "relative",
        "reason": "Hepatotoxicity risk with compromised liver function",
        "alternatives": ["Low-dose options", "Alternative analgesics"],
        "monitoring": ["Liver function tests"],
        "evidence_level": "high",
    },
    "simvastatin+liver disease": {
        "severity": "absolute",
        "reason": "Risk of hepatotoxicity",
        "alternatives": ["Lifestyle modifications", "Alternative lipid management"],
        "monitoring": ["Liver function tests"],
        "evidence_level": "high",
    },
    # GI contraindications
    "nsaid+peptic ulcer": {
        "severity": "relative",
        "reason": "Risk of GI bleeding and ulcer perforation",
        "alternatives": ["Acetaminophen", "COX-2 selective NSAIDs with PPI"],
        "monitoring": ["GI symptoms", "Hemoglobin"],
        "evidence_level": "high",
    },
    "aspirin+peptic ulcer": {
        "severity": "relative",
        "reason": "Increased bleeding risk",
        "alternatives": ["Clopidogrel", "Aspirin with PPI"],
        "monitoring": ["GI symptoms", "Complete blood count"],
        "evidence_level": "high",
    },
    # Psychiatric contraindications
    "fluoxetine+bipolar disorder": {
        "severity": "caution",
        "reason": "Risk of triggering manic episodes",
        "alternatives": ["Mood stabilizers first", "Atypical antipsychotics"],
        "monitoring": ["Mood symptoms", "Manic episodes"],
        "evidence_level": "moderate",
    },
}

AGE_CONTRAINDICATIONS: Dict[str, Dict[str, Any]] = {
    # Pediatric contraindications
    "aspirin+pediatric": {
        "severity": "absolute",
        "reason": "Risk of Reye's syndrome in children",
        "alternatives": ["Acetaminophen", "Ibuprofen (>6 months)"],
        "monitoring": ["Fever", "Neurological symptoms"],
        "evidence_level": "high",
    },
    "tetracycline+pediatric": {
        "severity": "absolute",
        "reason": "Tooth discoloration and growth inhibition",
        "alternatives": ["Penicillins", "Macrolides", "Cephalosporins"],
        "monitoring": ["Dental development"],
        "evidence_level": "high",
    },
    "fluoroquinolone+pediatric": {
        "severity": "relative",
        "reason": "Cartilage damage risk",
        "alternatives": ["Beta-lactam antibiotics", "Macrolides"],
        "monitoring": ["Joint symptoms"],
        "evidence_level": "high",
    },
    # Geriatric considerations
    "diphenhydramine+geriatric": {
        "severity": "caution",
        "reason": "Anticholinergic effects, falls risk",
        "alternatives": ["Loratadine", "Cetirizine"],
        "monitoring": ["Cognitive function", "Falls assessment"],
        "evidence_level": "high",
    },
    "benzodiazepine+geriatric": {
        "severity": "caution",
        "reason": "Increased sedation, falls, cognitive impairment",
        "alternatives": ["Non-benzodiazepine sleep aids", "CBT"],
        "monitoring": ["Cognitive function", "Falls risk"],
        "evidence_level": "high",
    },
    "nsaid+geriatric": {
        "severity": "caution",
        "reason": "Increased GI bleeding and cardiovascular risk",
        "alternatives": ["Acetaminophen", "Topical preparations"],
        "monitoring": ["GI symptoms", "Kidney function", "Blood pressure"],
        "evidence_level": "high",
    },
}

PREGNANCY_CONTRAINDICATIONS: Dict[str, Dict[str, Any]] = {
    "warfarin": {
        "category": "X",
        "reason": "Teratogenic effects, fetal bleeding",
        "alternatives": ["Heparin", "Low molecular weight heparin"],
        "monitoring": ["Coagulation studies"],
    },
    "isotretinoin": {
        "category": "X",
        "reason": "Severe birth defects",
        "alternatives": ["Topical retinoids", "Alternative acne treatments"],
        "monitoring": ["Pregnancy testing"],
    },
    "lisinopril": {
        "category": "D",
        "reason": "Fetal kidney damage, oligohydramnios",
        "alternatives": ["Methyldopa", "Labetalol", "Nifedipine"],
        "monitoring": ["Fetal growth", "Amniotic fluid"],
    },
    "atenolol": {
        "category": "D",
        "reason": "Fetal growth restriction",
        "alternatives": ["Methyldopa", "Labetalol"],
        "monitoring": ["Fetal growth", "Heart rate"],
    },
    "phenytoin": {
        "category": "D",
        "reason": "Fetal hydantoin syndrome",
        "alternatives": ["Lamotrigine", "Levetiracetam"],
        "monitoring": ["Fetal development", "Drug levels"],
    },
}

ALLERGY_CROSS_REACTIONS: Dict[str, Any] = {
    "penicillin": ["amoxicillin", "ampicillin", "cephalexin", "cefazolin"],
    "sulfa": ["sulfamethoxazole", "furosemide", "hydrochlorothiazide"],
    "aspirin": ["ibuprofen", "naproxen", "diclofenac", "celecoxib"],
    "codeine": ["morphine", "oxycodone", "hydrocodone"],
    "latex": ["avocado", "banana", "kiwi", "chestnut"],
}
