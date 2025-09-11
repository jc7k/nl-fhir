"""
Story 4.2: Drug Interaction Detection System
Comprehensive medication interaction checking with severity classification
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass
import re


class InteractionSeverity(Enum):
    """Drug interaction severity levels"""
    CONTRAINDICATED = "contraindicated"  # Avoid combination
    MAJOR = "major"                      # Monitor closely, consider alternatives
    MODERATE = "moderate"                # Monitor for effects
    MINOR = "minor"                      # Awareness sufficient


@dataclass
class DrugInteraction:
    """Drug interaction model"""
    drug_a: str
    drug_b: str
    severity: InteractionSeverity
    mechanism: str
    clinical_effect: str
    management_recommendation: str
    evidence_level: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "drug_a": self.drug_a,
            "drug_b": self.drug_b,
            "severity": self.severity.value,
            "mechanism": self.mechanism,
            "clinical_effect": self.clinical_effect,
            "management_recommendation": self.management_recommendation,
            "evidence_level": self.evidence_level
        }


class DrugInteractionChecker:
    """Comprehensive drug interaction detection and analysis"""
    
    def __init__(self):
        self.interaction_database = self._initialize_interaction_database()
        self.drug_name_normalizer = self._initialize_drug_normalizer()
    
    def check_bundle_interactions(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check all drug interactions in a FHIR bundle
        
        Returns comprehensive interaction analysis with severity classification
        """
        medications = self._extract_medications(bundle)
        if len(medications) < 2:
            return {
                "has_interactions": False,
                "interaction_count": 0,
                "interactions": [],
                "summary": "No drug interactions possible (less than 2 medications)"
            }
        
        interactions = []
        severity_counts = {severity.value: 0 for severity in InteractionSeverity}
        
        # Check all medication pairs for interactions
        for i, med_a in enumerate(medications):
            for med_b in medications[i+1:]:
                interaction = self._check_drug_pair(med_a, med_b)
                if interaction:
                    interactions.append(interaction.to_dict())
                    severity_counts[interaction.severity.value] += 1
        
        # Generate interaction summary
        summary = self._generate_interaction_summary(interactions, severity_counts)
        
        return {
            "has_interactions": len(interactions) > 0,
            "interaction_count": len(interactions),
            "interactions": interactions,
            "severity_breakdown": severity_counts,
            "summary": summary,
            "recommendations": self._generate_interaction_recommendations(interactions)
        }
    
    def _extract_medications(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all medications from FHIR bundle"""
        medications = []
        entries = bundle.get("entry", []) or []
        
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "MedicationRequest":
                med_name = self._get_medication_name(resource)
                if med_name:
                    medications.append({
                        "name": med_name,
                        "normalized_name": self._normalize_drug_name(med_name),
                        "resource": resource
                    })
        
        return medications
    
    def _get_medication_name(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract medication name from MedicationRequest resource"""
        # Try medicationCodeableConcept first
        med_concept = resource.get("medicationCodeableConcept", {})
        if med_concept.get("text"):
            return med_concept["text"]
        
        codings = med_concept.get("coding", [])
        if codings and isinstance(codings, list):
            return codings[0].get("display") or codings[0].get("code")
        
        # Try medicationReference if present
        med_ref = resource.get("medicationReference", {})
        if med_ref.get("display"):
            return med_ref["display"]
        
        return None
    
    def _normalize_drug_name(self, drug_name: str) -> str:
        """Normalize drug name for interaction checking"""
        if not drug_name:
            return ""
        
        # Convert to lowercase and remove common suffixes
        normalized = drug_name.lower().strip()
        
        # Remove dosage information
        normalized = re.sub(r'\d+\s*(mg|mcg|g|ml|units?)\b', '', normalized)
        normalized = re.sub(r'\d+/\d+\s*(mg|mcg|g|ml)\b', '', normalized)
        
        # Remove formulation information
        formulations = [
            'tablet', 'tablets', 'capsule', 'capsules', 'injection', 'injections',
            'solution', 'suspension', 'cream', 'ointment', 'gel', 'patch',
            'drops', 'spray', 'inhaler', 'syrup', 'liquid'
        ]
        for form in formulations:
            normalized = re.sub(rf'\b{form}s?\b', '', normalized)
        
        # Clean up whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Map to known drug names
        return self.drug_name_normalizer.get(normalized, normalized)
    
    def _check_drug_pair(self, med_a: Dict[str, Any], med_b: Dict[str, Any]) -> Optional[DrugInteraction]:
        """Check for interactions between two medications"""
        name_a = med_a["normalized_name"]
        name_b = med_b["normalized_name"]
        
        # Check both directions in interaction database
        interaction_key = f"{name_a}+{name_b}"
        reverse_key = f"{name_b}+{name_a}"
        
        interaction_data = self.interaction_database.get(interaction_key) or \
                          self.interaction_database.get(reverse_key)
        
        if interaction_data:
            return DrugInteraction(
                drug_a=med_a["name"],
                drug_b=med_b["name"],
                severity=interaction_data["severity"],
                mechanism=interaction_data["mechanism"],
                clinical_effect=interaction_data["clinical_effect"],
                management_recommendation=interaction_data["management"],
                evidence_level=interaction_data["evidence_level"]
            )
        
        return None
    
    def _generate_interaction_summary(self, interactions: List[Dict], severity_counts: Dict[str, int]) -> str:
        """Generate human-readable interaction summary"""
        if not interactions:
            return "No significant drug interactions detected"
        
        total = len(interactions)
        contraindicated = severity_counts.get("contraindicated", 0)
        major = severity_counts.get("major", 0)
        moderate = severity_counts.get("moderate", 0)
        minor = severity_counts.get("minor", 0)
        
        summary_parts = [f"Found {total} drug interaction(s)"]
        
        if contraindicated > 0:
            summary_parts.append(f"{contraindicated} contraindicated (avoid combination)")
        if major > 0:
            summary_parts.append(f"{major} major (monitor closely)")
        if moderate > 0:
            summary_parts.append(f"{moderate} moderate (monitor)")
        if minor > 0:
            summary_parts.append(f"{minor} minor (awareness)")
        
        return "; ".join(summary_parts)
    
    def _generate_interaction_recommendations(self, interactions: List[Dict]) -> List[str]:
        """Generate actionable recommendations for interactions"""
        if not interactions:
            return ["Continue current medication regimen - no interactions detected"]
        
        recommendations = []
        
        # Priority recommendations for severe interactions
        contraindicated = [i for i in interactions if i["severity"] == "contraindicated"]
        major = [i for i in interactions if i["severity"] == "major"]
        
        if contraindicated:
            recommendations.append("URGENT: Review contraindicated drug combinations with prescriber immediately")
            for interaction in contraindicated:
                recommendations.append(f"Consider alternative to {interaction['drug_a']} or {interaction['drug_b']}")
        
        if major:
            recommendations.append("Monitor closely for adverse effects and consider dose adjustments")
            for interaction in major:
                recommendations.append(f"{interaction['drug_a']} + {interaction['drug_b']}: {interaction['management_recommendation']}")
        
        # General monitoring recommendations
        moderate_minor = [i for i in interactions if i["severity"] in ["moderate", "minor"]]
        if moderate_minor:
            recommendations.append("Routine monitoring recommended for remaining interactions")
        
        return recommendations
    
    def _initialize_interaction_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive drug interaction database"""
        return {
            # High-risk anticoagulant interactions
            "warfarin+aspirin": {
                "severity": InteractionSeverity.MAJOR,
                "mechanism": "Additive anticoagulant effects",
                "clinical_effect": "Increased bleeding risk",
                "management": "Monitor INR closely, consider gastroprotection",
                "evidence_level": "high"
            },
            "warfarin+amiodarone": {
                "severity": InteractionSeverity.MAJOR,
                "mechanism": "CYP2C9 inhibition",
                "clinical_effect": "Increased warfarin effect, bleeding risk",
                "management": "Reduce warfarin dose by 30-50%, monitor INR",
                "evidence_level": "high"
            },
            "warfarin+metronidazole": {
                "severity": InteractionSeverity.MAJOR,
                "mechanism": "CYP2C9 inhibition",
                "clinical_effect": "Enhanced anticoagulation",
                "management": "Monitor INR daily, consider dose reduction",
                "evidence_level": "high"
            },
            
            # Digoxin interactions
            "digoxin+amiodarone": {
                "severity": InteractionSeverity.MAJOR,
                "mechanism": "P-glycoprotein inhibition",
                "clinical_effect": "Increased digoxin levels, toxicity risk",
                "management": "Reduce digoxin dose by 50%, monitor levels",
                "evidence_level": "high"
            },
            "digoxin+furosemide": {
                "severity": InteractionSeverity.MODERATE,
                "mechanism": "Electrolyte depletion",
                "clinical_effect": "Increased digoxin sensitivity",
                "management": "Monitor potassium levels, consider supplementation",
                "evidence_level": "moderate"
            },
            
            # ACE inhibitor interactions
            "lisinopril+potassium": {
                "severity": InteractionSeverity.MODERATE,
                "mechanism": "Additive hyperkalemia risk",
                "clinical_effect": "Dangerous potassium elevation",
                "management": "Monitor serum potassium regularly",
                "evidence_level": "high"
            },
            "enalapril+potassium": {
                "severity": InteractionSeverity.MODERATE,
                "mechanism": "Additive hyperkalemia risk",
                "clinical_effect": "Dangerous potassium elevation",
                "management": "Monitor serum potassium regularly",
                "evidence_level": "high"
            },
            
            # Statin interactions
            "simvastatin+amiodarone": {
                "severity": InteractionSeverity.MODERATE,
                "mechanism": "CYP3A4 inhibition",
                "clinical_effect": "Increased statin levels, myopathy risk",
                "management": "Limit simvastatin dose to 20mg daily",
                "evidence_level": "high"
            },
            "atorvastatin+clarithromycin": {
                "severity": InteractionSeverity.MAJOR,
                "mechanism": "CYP3A4 inhibition",
                "clinical_effect": "Severe myopathy risk",
                "management": "Consider statin interruption during antibiotic course",
                "evidence_level": "high"
            },
            
            # CNS interactions
            "oxycodone+alprazolam": {
                "severity": InteractionSeverity.CONTRAINDICATED,
                "mechanism": "Additive CNS depression",
                "clinical_effect": "Respiratory depression, death risk",
                "management": "Avoid combination, use alternative analgesic or anxiolytic",
                "evidence_level": "high"
            },
            "morphine+lorazepam": {
                "severity": InteractionSeverity.CONTRAINDICATED,
                "mechanism": "Additive CNS depression",
                "clinical_effect": "Severe respiratory depression",
                "management": "Avoid combination, use non-benzodiazepine alternative",
                "evidence_level": "high"
            },
            
            # Antibiotic interactions
            "clarithromycin+ergotamine": {
                "severity": InteractionSeverity.CONTRAINDICATED,
                "mechanism": "CYP3A4 inhibition",
                "clinical_effect": "Ergotism, vasospasm",
                "management": "Avoid combination, use alternative antibiotic",
                "evidence_level": "high"
            },
            
            # Antidepressant interactions
            "fluoxetine+tramadol": {
                "severity": InteractionSeverity.MAJOR,
                "mechanism": "Serotonin syndrome risk",
                "clinical_effect": "Hyperthermia, altered mental status",
                "management": "Monitor for serotonin syndrome, consider alternatives",
                "evidence_level": "moderate"
            },
            
            # Diabetes medication interactions
            "metformin+iodinated contrast": {
                "severity": InteractionSeverity.MAJOR,
                "mechanism": "Lactic acidosis risk",
                "clinical_effect": "Contrast-induced nephropathy",
                "management": "Hold metformin 48h before/after contrast",
                "evidence_level": "high"
            }
        }
    
    def _initialize_drug_normalizer(self) -> Dict[str, str]:
        """Initialize drug name normalization mapping"""
        return {
            # Anticoagulants
            "coumadin": "warfarin",
            "jantoven": "warfarin",
            "bayer aspirin": "aspirin",
            "bufferin": "aspirin",
            
            # Cardiac medications
            "lanoxin": "digoxin",
            "digitek": "digoxin",
            "cordarone": "amiodarone",
            "pacerone": "amiodarone",
            
            # ACE inhibitors
            "prinivil": "lisinopril",
            "zestril": "lisinopril",
            "vasotec": "enalapril",
            
            # Statins
            "zocor": "simvastatin",
            "lipitor": "atorvastatin",
            
            # Pain medications
            "oxycontin": "oxycodone",
            "percocet": "oxycodone",
            "roxicodone": "oxycodone",
            "ms contin": "morphine",
            "xanax": "alprazolam",
            "ativan": "lorazepam",
            
            # Antibiotics
            "biaxin": "clarithromycin",
            "flagyl": "metronidazole",
            
            # Antidepressants
            "prozac": "fluoxetine",
            "sarafem": "fluoxetine",
            "ultram": "tramadol",
            
            # Diabetes
            "glucophage": "metformin",
            "fortamet": "metformin",
            
            # Diuretics
            "lasix": "furosemide"
        }