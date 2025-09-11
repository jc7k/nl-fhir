"""
Story 4.2: Contraindication and Allergy Detection System
Medical contraindication checking with age, condition, and allergy considerations
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass
import re
from datetime import datetime, date


class ContraindicationSeverity(Enum):
    """Contraindication severity levels"""
    ABSOLUTE = "absolute"      # Never use
    RELATIVE = "relative"      # Use with extreme caution
    CAUTION = "caution"       # Monitor closely
    WARNING = "warning"       # Be aware


@dataclass
class Contraindication:
    """Medical contraindication model"""
    medication: str
    condition: str
    severity: ContraindicationSeverity
    reason: str
    alternative_suggestions: List[str]
    monitoring_requirements: List[str]
    evidence_level: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "medication": self.medication,
            "condition": self.condition,
            "severity": self.severity.value,
            "reason": self.reason,
            "alternative_suggestions": self.alternative_suggestions,
            "monitoring_requirements": self.monitoring_requirements,
            "evidence_level": self.evidence_level
        }


class ContraindicationChecker:
    """Comprehensive contraindication and allergy detection"""
    
    def __init__(self):
        self.contraindication_database = self._initialize_contraindication_database()
        self.age_based_contraindications = self._initialize_age_contraindications()
        self.pregnancy_categories = self._initialize_pregnancy_categories()
        self.allergy_cross_reactions = self._initialize_allergy_database()
    
    def check_bundle_contraindications(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check all contraindications in a FHIR bundle
        
        Returns comprehensive contraindication analysis
        """
        medications = self._extract_medications(bundle)
        conditions = self._extract_conditions(bundle)
        allergies = self._extract_allergies(bundle)
        patient_info = self._extract_patient_info(bundle)
        
        contraindications = []
        
        # Check medication-condition contraindications
        for medication in medications:
            for condition in conditions:
                contraindication = self._check_medication_condition(medication, condition)
                if contraindication:
                    contraindications.append(contraindication.to_dict())
        
        # Check age-based contraindications
        if patient_info.get("age"):
            age_contraindications = self._check_age_contraindications(medications, patient_info["age"])
            contraindications.extend([c.to_dict() for c in age_contraindications])
        
        # Check pregnancy-related contraindications
        if patient_info.get("gender") == "female":
            pregnancy_contraindications = self._check_pregnancy_contraindications(medications, conditions)
            contraindications.extend([c.to_dict() for c in pregnancy_contraindications])
        
        # Check allergy contraindications
        if allergies:
            allergy_contraindications = self._check_allergy_contraindications(medications, allergies)
            contraindications.extend([c.to_dict() for c in allergy_contraindications])
        
        # Generate summary
        severity_counts = self._count_by_severity(contraindications)
        summary = self._generate_contraindication_summary(contraindications, severity_counts)
        
        return {
            "has_contraindications": len(contraindications) > 0,
            "contraindication_count": len(contraindications),
            "contraindications": contraindications,
            "severity_breakdown": severity_counts,
            "summary": summary,
            "recommendations": self._generate_contraindication_recommendations(contraindications)
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
                        "normalized_name": self._normalize_medication_name(med_name),
                        "resource": resource
                    })
        
        return medications
    
    def _extract_conditions(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all conditions from FHIR bundle"""
        conditions = []
        entries = bundle.get("entry", []) or []
        
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "Condition":
                condition_name = self._get_condition_name(resource)
                if condition_name:
                    conditions.append({
                        "name": condition_name,
                        "normalized_name": self._normalize_condition_name(condition_name),
                        "resource": resource
                    })
        
        return conditions
    
    def _extract_allergies(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all allergies from FHIR bundle"""
        allergies = []
        entries = bundle.get("entry", []) or []
        
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "AllergyIntolerance":
                allergy_name = self._get_allergy_name(resource)
                if allergy_name:
                    allergies.append({
                        "name": allergy_name,
                        "normalized_name": self._normalize_allergy_name(allergy_name),
                        "resource": resource
                    })
        
        return allergies
    
    def _extract_patient_info(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient demographics from FHIR bundle"""
        patient_info = {}
        entries = bundle.get("entry", []) or []
        
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "Patient":
                # Extract age
                birth_date = resource.get("birthDate")
                if birth_date:
                    try:
                        birth_dt = datetime.strptime(birth_date, "%Y-%m-%d").date()
                        today = date.today()
                        age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))
                        patient_info["age"] = age
                    except:
                        pass
                
                # Extract gender
                gender = resource.get("gender")
                if gender:
                    patient_info["gender"] = gender
                
                break
        
        return patient_info
    
    def _get_medication_name(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract medication name from MedicationRequest resource"""
        med_concept = resource.get("medicationCodeableConcept", {})
        if med_concept.get("text"):
            return med_concept["text"]
        
        codings = med_concept.get("coding", [])
        if codings and isinstance(codings, list):
            return codings[0].get("display") or codings[0].get("code")
        
        return None
    
    def _get_condition_name(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract condition name from Condition resource"""
        code = resource.get("code", {})
        if code.get("text"):
            return code["text"]
        
        codings = code.get("coding", [])
        if codings and isinstance(codings, list):
            return codings[0].get("display") or codings[0].get("code")
        
        return None
    
    def _get_allergy_name(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract allergy name from AllergyIntolerance resource"""
        code = resource.get("code", {})
        if code.get("text"):
            return code["text"]
        
        codings = code.get("coding", [])
        if codings and isinstance(codings, list):
            return codings[0].get("display") or codings[0].get("code")
        
        return None
    
    def _normalize_medication_name(self, name: str) -> str:
        """Normalize medication name for contraindication checking"""
        if not name:
            return ""
        
        normalized = name.lower().strip()
        normalized = re.sub(r'\d+\s*(mg|mcg|g|ml|units?)\b', '', normalized)
        normalized = re.sub(r'\b(tablet|capsule|injection|solution)s?\b', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _normalize_condition_name(self, name: str) -> str:
        """Normalize condition name for contraindication checking"""
        if not name:
            return ""
        
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Map common variations
        mappings = {
            "diabetes mellitus": "diabetes",
            "diabetes type 2": "diabetes",
            "diabetes type 1": "diabetes",
            "myocardial infarction": "heart attack",
            "congestive heart failure": "heart failure",
            "chronic kidney disease": "kidney disease",
            "end stage renal disease": "kidney disease"
        }
        
        return mappings.get(normalized, normalized)
    
    def _normalize_allergy_name(self, name: str) -> str:
        """Normalize allergy name for cross-reaction checking"""
        if not name:
            return ""
        
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _check_medication_condition(self, medication: Dict[str, Any], condition: Dict[str, Any]) -> Optional[Contraindication]:
        """Check for contraindication between medication and condition"""
        med_name = medication["normalized_name"]
        condition_name = condition["normalized_name"]
        
        # Check contraindication database
        key = f"{med_name}+{condition_name}"
        contraindication_data = self.contraindication_database.get(key)
        
        if contraindication_data:
            return Contraindication(
                medication=medication["name"],
                condition=condition["name"],
                severity=contraindication_data["severity"],
                reason=contraindication_data["reason"],
                alternative_suggestions=contraindication_data["alternatives"],
                monitoring_requirements=contraindication_data["monitoring"],
                evidence_level=contraindication_data["evidence_level"]
            )
        
        return None
    
    def _check_age_contraindications(self, medications: List[Dict[str, Any]], age: int) -> List[Contraindication]:
        """Check for age-based contraindications"""
        contraindications = []
        
        for medication in medications:
            med_name = medication["normalized_name"]
            
            # Check pediatric contraindications (< 18 years)
            if age < 18:
                pediatric_data = self.age_based_contraindications.get(f"{med_name}+pediatric")
                if pediatric_data:
                    contraindications.append(Contraindication(
                        medication=medication["name"],
                        condition=f"Pediatric patient (age {age})",
                        severity=pediatric_data["severity"],
                        reason=pediatric_data["reason"],
                        alternative_suggestions=pediatric_data["alternatives"],
                        monitoring_requirements=pediatric_data["monitoring"],
                        evidence_level=pediatric_data["evidence_level"]
                    ))
            
            # Check geriatric contraindications (>= 65 years)
            if age >= 65:
                geriatric_data = self.age_based_contraindications.get(f"{med_name}+geriatric")
                if geriatric_data:
                    contraindications.append(Contraindication(
                        medication=medication["name"],
                        condition=f"Geriatric patient (age {age})",
                        severity=geriatric_data["severity"],
                        reason=geriatric_data["reason"],
                        alternative_suggestions=geriatric_data["alternatives"],
                        monitoring_requirements=geriatric_data["monitoring"],
                        evidence_level=geriatric_data["evidence_level"]
                    ))
        
        return contraindications
    
    def _check_pregnancy_contraindications(self, medications: List[Dict[str, Any]], conditions: List[Dict[str, Any]]) -> List[Contraindication]:
        """Check for pregnancy-related contraindications"""
        contraindications = []
        
        # Check if pregnancy is indicated
        is_pregnant = any("pregnan" in cond["normalized_name"] for cond in conditions)
        is_breastfeeding = any("breastfeed" in cond["normalized_name"] or "lactation" in cond["normalized_name"] for cond in conditions)
        
        if is_pregnant or is_breastfeeding:
            for medication in medications:
                med_name = medication["normalized_name"]
                pregnancy_data = self.pregnancy_categories.get(med_name)
                
                if pregnancy_data and pregnancy_data["category"] in ["D", "X"]:
                    condition_desc = "Pregnancy" if is_pregnant else "Breastfeeding"
                    contraindications.append(Contraindication(
                        medication=medication["name"],
                        condition=condition_desc,
                        severity=ContraindicationSeverity.ABSOLUTE if pregnancy_data["category"] == "X" else ContraindicationSeverity.RELATIVE,
                        reason=f"Pregnancy category {pregnancy_data['category']}: {pregnancy_data['reason']}",
                        alternative_suggestions=pregnancy_data["alternatives"],
                        monitoring_requirements=pregnancy_data["monitoring"],
                        evidence_level="high"
                    ))
        
        return contraindications
    
    def _check_allergy_contraindications(self, medications: List[Dict[str, Any]], allergies: List[Dict[str, Any]]) -> List[Contraindication]:
        """Check for allergy-based contraindications"""
        contraindications = []
        
        for medication in medications:
            med_name = medication["normalized_name"]
            
            for allergy in allergies:
                allergy_name = allergy["normalized_name"]
                
                # Direct allergy match
                if allergy_name in med_name or med_name in allergy_name:
                    contraindications.append(Contraindication(
                        medication=medication["name"],
                        condition=f"Known allergy to {allergy['name']}",
                        severity=ContraindicationSeverity.ABSOLUTE,
                        reason="Direct allergy match",
                        alternative_suggestions=["Consult with allergist for safe alternatives"],
                        monitoring_requirements=["Emergency treatment available"],
                        evidence_level="high"
                    ))
                
                # Cross-reaction check
                cross_reactions = self.allergy_cross_reactions.get(allergy_name, [])
                if any(cr in med_name for cr in cross_reactions):
                    contraindications.append(Contraindication(
                        medication=medication["name"],
                        condition=f"Cross-reaction with {allergy['name']} allergy",
                        severity=ContraindicationSeverity.RELATIVE,
                        reason="Potential cross-allergic reaction",
                        alternative_suggestions=["Consider alternative medication class"],
                        monitoring_requirements=["Monitor for allergic reactions"],
                        evidence_level="moderate"
                    ))
        
        return contraindications
    
    def _count_by_severity(self, contraindications: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count contraindications by severity"""
        counts = {severity.value: 0 for severity in ContraindicationSeverity}
        for contraindication in contraindications:
            severity = contraindication["severity"]
            counts[severity] += 1
        return counts
    
    def _generate_contraindication_summary(self, contraindications: List[Dict], severity_counts: Dict[str, int]) -> str:
        """Generate human-readable contraindication summary"""
        if not contraindications:
            return "No contraindications detected"
        
        total = len(contraindications)
        absolute = severity_counts.get("absolute", 0)
        relative = severity_counts.get("relative", 0)
        caution = severity_counts.get("caution", 0)
        warning = severity_counts.get("warning", 0)
        
        summary_parts = [f"Found {total} contraindication(s)"]
        
        if absolute > 0:
            summary_parts.append(f"{absolute} absolute (avoid)")
        if relative > 0:
            summary_parts.append(f"{relative} relative (extreme caution)")
        if caution > 0:
            summary_parts.append(f"{caution} caution required")
        if warning > 0:
            summary_parts.append(f"{warning} warnings")
        
        return "; ".join(summary_parts)
    
    def _generate_contraindication_recommendations(self, contraindications: List[Dict]) -> List[str]:
        """Generate actionable recommendations for contraindications"""
        if not contraindications:
            return ["No contraindications found - current medications appear appropriate"]
        
        recommendations = []
        
        # Priority recommendations for severe contraindications
        absolute = [c for c in contraindications if c["severity"] == "absolute"]
        relative = [c for c in contraindications if c["severity"] == "relative"]
        
        if absolute:
            recommendations.append("CRITICAL: Stop contraindicated medications immediately")
            for contraindication in absolute:
                recommendations.append(f"Discontinue {contraindication['medication']} - {contraindication['reason']}")
                if contraindication["alternative_suggestions"]:
                    recommendations.extend(contraindication["alternative_suggestions"])
        
        if relative:
            recommendations.append("HIGH PRIORITY: Review relative contraindications with prescriber")
            for contraindication in relative:
                recommendations.append(f"{contraindication['medication']}: {contraindication['reason']}")
        
        # General monitoring recommendations
        all_monitoring = []
        for contraindication in contraindications:
            all_monitoring.extend(contraindication.get("monitoring_requirements", []))
        
        unique_monitoring = list(set(all_monitoring))
        if unique_monitoring:
            recommendations.append("Required monitoring:")
            recommendations.extend(unique_monitoring)
        
        return recommendations
    
    def _initialize_contraindication_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive contraindication database"""
        return {
            # Cardiovascular contraindications
            "metoprolol+asthma": {
                "severity": ContraindicationSeverity.ABSOLUTE,
                "reason": "Beta-blockers can cause severe bronchospasm in asthma",
                "alternatives": ["Calcium channel blockers", "ACE inhibitors"],
                "monitoring": ["Respiratory function"],
                "evidence_level": "high"
            },
            "propranolol+asthma": {
                "severity": ContraindicationSeverity.ABSOLUTE,
                "reason": "Non-selective beta-blocker contraindicated in asthma",
                "alternatives": ["Cardioselective beta-blockers if essential", "Alternative antihypertensives"],
                "monitoring": ["Respiratory function"],
                "evidence_level": "high"
            },
            "diltiazem+heart failure": {
                "severity": ContraindicationSeverity.RELATIVE,
                "reason": "Negative inotropic effect may worsen heart failure",
                "alternatives": ["ACE inhibitors", "ARBs", "Beta-blockers"],
                "monitoring": ["Left ventricular function", "Symptoms"],
                "evidence_level": "high"
            },
            
            # Kidney disease contraindications
            "metformin+kidney disease": {
                "severity": ContraindicationSeverity.ABSOLUTE,
                "reason": "Risk of lactic acidosis with reduced kidney function",
                "alternatives": ["Insulin", "Sulfonylureas", "DPP-4 inhibitors"],
                "monitoring": ["Kidney function"],
                "evidence_level": "high"
            },
            "nsaid+kidney disease": {
                "severity": ContraindicationSeverity.RELATIVE,
                "reason": "Further reduction in kidney function",
                "alternatives": ["Acetaminophen", "Topical analgesics"],
                "monitoring": ["Serum creatinine", "BUN"],
                "evidence_level": "high"
            },
            
            # Liver disease contraindications
            "acetaminophen+liver disease": {
                "severity": ContraindicationSeverity.RELATIVE,
                "reason": "Hepatotoxicity risk with compromised liver function",
                "alternatives": ["Low-dose options", "Alternative analgesics"],
                "monitoring": ["Liver function tests"],
                "evidence_level": "high"
            },
            "simvastatin+liver disease": {
                "severity": ContraindicationSeverity.ABSOLUTE,
                "reason": "Risk of hepatotoxicity",
                "alternatives": ["Lifestyle modifications", "Alternative lipid management"],
                "monitoring": ["Liver function tests"],
                "evidence_level": "high"
            },
            
            # GI contraindications
            "nsaid+peptic ulcer": {
                "severity": ContraindicationSeverity.RELATIVE,
                "reason": "Risk of GI bleeding and ulcer perforation",
                "alternatives": ["Acetaminophen", "COX-2 selective NSAIDs with PPI"],
                "monitoring": ["GI symptoms", "Hemoglobin"],
                "evidence_level": "high"
            },
            "aspirin+peptic ulcer": {
                "severity": ContraindicationSeverity.RELATIVE,
                "reason": "Increased bleeding risk",
                "alternatives": ["Clopidogrel", "Aspirin with PPI"],
                "monitoring": ["GI symptoms", "Complete blood count"],
                "evidence_level": "high"
            },
            
            # Psychiatric contraindications
            "fluoxetine+bipolar disorder": {
                "severity": ContraindicationSeverity.CAUTION,
                "reason": "Risk of triggering manic episodes",
                "alternatives": ["Mood stabilizers first", "Atypical antipsychotics"],
                "monitoring": ["Mood symptoms", "Manic episodes"],
                "evidence_level": "moderate"
            }
        }
    
    def _initialize_age_contraindications(self) -> Dict[str, Dict[str, Any]]:
        """Initialize age-based contraindication database"""
        return {
            # Pediatric contraindications
            "aspirin+pediatric": {
                "severity": ContraindicationSeverity.ABSOLUTE,
                "reason": "Risk of Reye's syndrome in children",
                "alternatives": ["Acetaminophen", "Ibuprofen (>6 months)"],
                "monitoring": ["Fever", "Neurological symptoms"],
                "evidence_level": "high"
            },
            "tetracycline+pediatric": {
                "severity": ContraindicationSeverity.ABSOLUTE,
                "reason": "Tooth discoloration and growth inhibition",
                "alternatives": ["Penicillins", "Macrolides", "Cephalosporins"],
                "monitoring": ["Dental development"],
                "evidence_level": "high"
            },
            "fluoroquinolone+pediatric": {
                "severity": ContraindicationSeverity.RELATIVE,
                "reason": "Cartilage damage risk",
                "alternatives": ["Beta-lactam antibiotics", "Macrolides"],
                "monitoring": ["Joint symptoms"],
                "evidence_level": "high"
            },
            
            # Geriatric contraindications
            "diphenhydramine+geriatric": {
                "severity": ContraindicationSeverity.CAUTION,
                "reason": "Anticholinergic effects, falls risk",
                "alternatives": ["Loratadine", "Cetirizine"],
                "monitoring": ["Cognitive function", "Falls assessment"],
                "evidence_level": "high"
            },
            "benzodiazepine+geriatric": {
                "severity": ContraindicationSeverity.CAUTION,
                "reason": "Increased sedation, falls, cognitive impairment",
                "alternatives": ["Non-benzodiazepine sleep aids", "CBT"],
                "monitoring": ["Cognitive function", "Falls risk"],
                "evidence_level": "high"
            },
            "nsaid+geriatric": {
                "severity": ContraindicationSeverity.CAUTION,
                "reason": "Increased GI bleeding and cardiovascular risk",
                "alternatives": ["Acetaminophen", "Topical preparations"],
                "monitoring": ["GI symptoms", "Kidney function", "Blood pressure"],
                "evidence_level": "high"
            }
        }
    
    def _initialize_pregnancy_categories(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pregnancy safety categories"""
        return {
            # Category X (Contraindicated)
            "warfarin": {
                "category": "X",
                "reason": "Teratogenic effects, fetal bleeding",
                "alternatives": ["Heparin", "Low molecular weight heparin"],
                "monitoring": ["Coagulation studies"]
            },
            "isotretinoin": {
                "category": "X",
                "reason": "Severe birth defects",
                "alternatives": ["Topical retinoids", "Alternative acne treatments"],
                "monitoring": ["Pregnancy testing"]
            },
            
            # Category D (Use only if benefits outweigh risks)
            "lisinopril": {
                "category": "D",
                "reason": "Fetal kidney damage, oligohydramnios",
                "alternatives": ["Methyldopa", "Labetalol", "Nifedipine"],
                "monitoring": ["Fetal growth", "Amniotic fluid"]
            },
            "atenolol": {
                "category": "D",
                "reason": "Fetal growth restriction",
                "alternatives": ["Methyldopa", "Labetalol"],
                "monitoring": ["Fetal growth", "Heart rate"]
            },
            "phenytoin": {
                "category": "D",
                "reason": "Fetal hydantoin syndrome",
                "alternatives": ["Lamotrigine", "Levetiracetam"],
                "monitoring": ["Fetal development", "Drug levels"]
            }
        }
    
    def _initialize_allergy_database(self) -> Dict[str, List[str]]:
        """Initialize allergy cross-reaction database"""
        return {
            "penicillin": ["amoxicillin", "ampicillin", "cephalexin", "cefazolin"],
            "sulfa": ["sulfamethoxazole", "furosemide", "hydrochlorothiazide"],
            "aspirin": ["ibuprofen", "naproxen", "diclofenac", "celecoxib"],
            "codeine": ["morphine", "oxycodone", "hydrocodone"],
            "latex": ["avocado", "banana", "kiwi", "chestnut"]
        }