"""
Story 4.2: Clinical Decision Support System
Evidence-based recommendations and clinical guidelines integration
"""

from typing import Any, Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
import re


class RecommendationType(Enum):
    """Clinical recommendation types"""
    MONITORING = "monitoring"           # Monitoring requirements
    DOSAGE_ADJUSTMENT = "dosage"       # Dosage modifications
    ALTERNATIVE_THERAPY = "alternative" # Alternative medications
    TIMING = "timing"                  # Administration timing
    LIFESTYLE = "lifestyle"            # Lifestyle modifications
    LABORATORY = "laboratory"          # Lab test requirements


class EvidenceLevel(Enum):
    """Evidence quality levels"""
    HIGH = "high"           # Strong evidence, clinical trials
    MODERATE = "moderate"   # Good evidence, observational studies
    LOW = "low"            # Limited evidence, expert opinion
    EXPERT = "expert"      # Expert consensus only


@dataclass
class ClinicalRecommendation:
    """Clinical decision support recommendation"""
    medication: str
    recommendation_type: RecommendationType
    recommendation: str
    rationale: str
    evidence_level: EvidenceLevel
    priority: str  # high, medium, low
    implementation_steps: List[str]
    monitoring_parameters: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "medication": self.medication,
            "type": self.recommendation_type.value,
            "recommendation": self.recommendation,
            "rationale": self.rationale,
            "evidence_level": self.evidence_level.value,
            "priority": self.priority,
            "implementation_steps": self.implementation_steps,
            "monitoring_parameters": self.monitoring_parameters
        }


class ClinicalDecisionSupport:
    """Evidence-based clinical decision support system"""
    
    def __init__(self):
        self.guideline_database = self._initialize_guideline_database()
        self.monitoring_protocols = self._initialize_monitoring_protocols()
        self.alternative_therapies = self._initialize_alternative_therapies()
        self.drug_food_interactions = self._initialize_drug_food_interactions()
    
    def generate_clinical_recommendations(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive clinical decision support recommendations
        
        Returns evidence-based recommendations for FHIR bundle
        """
        medications = self._extract_medications(bundle)
        conditions = self._extract_conditions(bundle)
        patient_info = self._extract_patient_info(bundle)
        lab_results = self._extract_lab_results(bundle)
        
        recommendations = []
        
        # Generate medication-specific recommendations
        for medication in medications:
            med_recommendations = self._get_medication_recommendations(
                medication, conditions, patient_info, lab_results
            )
            recommendations.extend([r.to_dict() for r in med_recommendations])
        
        # Generate condition-specific recommendations
        condition_recommendations = self._get_condition_based_recommendations(
            medications, conditions, patient_info
        )
        recommendations.extend([r.to_dict() for r in condition_recommendations])
        
        # Generate monitoring recommendations
        monitoring_recommendations = self._get_monitoring_recommendations(
            medications, conditions, patient_info
        )
        recommendations.extend([r.to_dict() for r in monitoring_recommendations])
        
        # Categorize and prioritize recommendations
        categorized = self._categorize_recommendations(recommendations)
        summary = self._generate_recommendations_summary(recommendations, categorized)
        
        return {
            "has_recommendations": len(recommendations) > 0,
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "categorized_recommendations": categorized,
            "summary": summary,
            "implementation_priority": self._generate_implementation_plan(recommendations)
        }
    
    def _extract_medications(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract medications with detailed information"""
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
                        "dosage": self._extract_dosage_info(resource),
                        "indication": self._extract_indication(resource),
                        "resource": resource
                    })
        
        return medications
    
    def _extract_conditions(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract patient conditions"""
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
                        "severity": self._extract_condition_severity(resource),
                        "resource": resource
                    })
        
        return conditions
    
    def _extract_patient_info(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient demographics and characteristics"""
        patient_info = {}
        entries = bundle.get("entry", []) or []
        
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "Patient":
                # Age calculation (simplified)
                birth_date = resource.get("birthDate")
                if birth_date:
                    # Calculate age and age group
                    from datetime import datetime, date
                    try:
                        birth_dt = datetime.strptime(birth_date, "%Y-%m-%d").date()
                        today = date.today()
                        age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))
                        patient_info["age"] = age
                        
                        if age >= 65:
                            patient_info["age_group"] = "geriatric"
                        elif age < 18:
                            patient_info["age_group"] = "pediatric"
                        else:
                            patient_info["age_group"] = "adult"
                    except:
                        pass
                
                patient_info["gender"] = resource.get("gender")
                break
        
        return patient_info
    
    def _extract_lab_results(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relevant laboratory results"""
        lab_results = []
        entries = bundle.get("entry", []) or []
        
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "Observation":
                code = resource.get("code", {})
                code_text = code.get("text", "").lower()
                
                # Focus on clinically relevant labs
                relevant_labs = [
                    "creatinine", "bun", "egfr", "potassium", "sodium", "glucose",
                    "hemoglobin", "hematocrit", "platelet", "inr", "pt", "ptt",
                    "alt", "ast", "bilirubin", "albumin"
                ]
                
                if any(lab in code_text for lab in relevant_labs):
                    value_qty = resource.get("valueQuantity", {})
                    if value_qty.get("value") is not None:
                        lab_results.append({
                            "name": code_text,
                            "value": value_qty["value"],
                            "unit": value_qty.get("unit", ""),
                            "interpretation": self._get_observation_interpretation(resource),
                            "resource": resource
                        })
        
        return lab_results
    
    def _get_medication_recommendations(self, medication: Dict[str, Any], conditions: List[Dict[str, Any]],
                                      patient_info: Dict[str, Any], lab_results: List[Dict[str, Any]]) -> List[ClinicalRecommendation]:
        """Generate medication-specific clinical recommendations"""
        recommendations = []
        med_name = medication["normalized_name"]
        
        # Get medication-specific guidelines
        guidelines = self.guideline_database.get(med_name, [])
        
        for guideline in guidelines:
            # Check if guideline applies to patient
            if self._guideline_applies(guideline, conditions, patient_info, lab_results):
                recommendation = ClinicalRecommendation(
                    medication=medication["name"],
                    recommendation_type=RecommendationType(guideline["type"]),
                    recommendation=guideline["recommendation"],
                    rationale=guideline["rationale"],
                    evidence_level=EvidenceLevel(guideline["evidence_level"]),
                    priority=guideline["priority"],
                    implementation_steps=guideline["implementation_steps"],
                    monitoring_parameters=guideline["monitoring_parameters"]
                )
                recommendations.append(recommendation)
        
        # Check for drug-food interactions
        food_interactions = self.drug_food_interactions.get(med_name, [])
        for interaction in food_interactions:
            recommendation = ClinicalRecommendation(
                medication=medication["name"],
                recommendation_type=RecommendationType.TIMING,
                recommendation=interaction["recommendation"],
                rationale=interaction["rationale"],
                evidence_level=EvidenceLevel(interaction["evidence_level"]),
                priority="medium",
                implementation_steps=interaction["implementation_steps"],
                monitoring_parameters=[]
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_condition_based_recommendations(self, medications: List[Dict[str, Any]], 
                                           conditions: List[Dict[str, Any]], 
                                           patient_info: Dict[str, Any]) -> List[ClinicalRecommendation]:
        """Generate condition-based medication recommendations"""
        recommendations = []
        
        # Check for missing evidence-based therapies
        for condition in conditions:
            condition_name = condition["normalized_name"]
            
            # Get recommended medications for condition
            recommended_meds = self._get_recommended_therapies(condition_name, patient_info)
            current_med_names = {med["normalized_name"] for med in medications}
            
            for rec_med in recommended_meds:
                if rec_med["medication"] not in current_med_names:
                    recommendation = ClinicalRecommendation(
                        medication=f"Consider {rec_med['medication']}",
                        recommendation_type=RecommendationType.ALTERNATIVE_THERAPY,
                        recommendation=rec_med["recommendation"],
                        rationale=rec_med["rationale"],
                        evidence_level=EvidenceLevel(rec_med["evidence_level"]),
                        priority=rec_med["priority"],
                        implementation_steps=rec_med["implementation_steps"],
                        monitoring_parameters=rec_med["monitoring_parameters"]
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _get_monitoring_recommendations(self, medications: List[Dict[str, Any]], 
                                      conditions: List[Dict[str, Any]], 
                                      patient_info: Dict[str, Any]) -> List[ClinicalRecommendation]:
        """Generate monitoring protocol recommendations"""
        recommendations = []
        
        for medication in medications:
            med_name = medication["normalized_name"]
            monitoring_protocol = self.monitoring_protocols.get(med_name)
            
            if monitoring_protocol:
                # Adjust monitoring based on patient factors
                adjusted_protocol = self._adjust_monitoring_for_patient(
                    monitoring_protocol, patient_info, conditions
                )
                
                recommendation = ClinicalRecommendation(
                    medication=medication["name"],
                    recommendation_type=RecommendationType.MONITORING,
                    recommendation=adjusted_protocol["recommendation"],
                    rationale=adjusted_protocol["rationale"],
                    evidence_level=EvidenceLevel(adjusted_protocol["evidence_level"]),
                    priority=adjusted_protocol["priority"],
                    implementation_steps=adjusted_protocol["implementation_steps"],
                    monitoring_parameters=adjusted_protocol["monitoring_parameters"]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _guideline_applies(self, guideline: Dict[str, Any], conditions: List[Dict[str, Any]],
                          patient_info: Dict[str, Any], lab_results: List[Dict[str, Any]]) -> bool:
        """Check if clinical guideline applies to current patient"""
        
        # Check age group criteria
        age_group = patient_info.get("age_group")
        if guideline.get("age_group") and guideline["age_group"] != age_group:
            return False
        
        # Check condition criteria
        required_conditions = guideline.get("required_conditions", [])
        patient_conditions = {cond["normalized_name"] for cond in conditions}
        if required_conditions and not any(req_cond in patient_conditions for req_cond in required_conditions):
            return False
        
        # Check exclusion conditions
        exclusion_conditions = guideline.get("exclusion_conditions", [])
        if exclusion_conditions and any(excl_cond in patient_conditions for excl_cond in exclusion_conditions):
            return False
        
        # Check lab value criteria
        lab_criteria = guideline.get("lab_criteria", [])
        for criterion in lab_criteria:
            lab_name = criterion["lab"]
            required_value = criterion["value"]
            operator = criterion["operator"]  # >, <, >=, <=, ==
            
            matching_lab = next((lab for lab in lab_results if lab_name in lab["name"]), None)
            if matching_lab:
                lab_value = matching_lab["value"]
                if not self._evaluate_lab_criterion(lab_value, operator, required_value):
                    return False
            else:
                # Required lab not available
                if criterion.get("required", False):
                    return False
        
        return True
    
    def _evaluate_lab_criterion(self, lab_value: float, operator: str, required_value: float) -> bool:
        """Evaluate laboratory value criterion"""
        if operator == ">":
            return lab_value > required_value
        elif operator == "<":
            return lab_value < required_value
        elif operator == ">=":
            return lab_value >= required_value
        elif operator == "<=":
            return lab_value <= required_value
        elif operator == "==":
            return lab_value == required_value
        return False
    
    def _get_recommended_therapies(self, condition: str, patient_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get evidence-based therapy recommendations for condition"""
        therapy_recommendations = {
            "diabetes": [
                {
                    "medication": "metformin",
                    "recommendation": "First-line therapy for type 2 diabetes",
                    "rationale": "Proven cardiovascular benefits and weight neutrality",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["Start 500mg BID with meals", "Titrate based on tolerance"],
                    "monitoring_parameters": ["HbA1c", "Kidney function", "GI tolerance"]
                }
            ],
            "hypertension": [
                {
                    "medication": "lisinopril",
                    "recommendation": "ACE inhibitor for cardiovascular protection",
                    "rationale": "Reduces cardiovascular events and mortality",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["Start 2.5-5mg daily", "Titrate to target BP"],
                    "monitoring_parameters": ["Blood pressure", "Kidney function", "Potassium"]
                }
            ],
            "heart failure": [
                {
                    "medication": "carvedilol",
                    "recommendation": "Beta-blocker for heart failure with reduced ejection fraction",
                    "rationale": "Mortality benefit in systolic heart failure",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["Start 3.125mg BID", "Double dose every 2 weeks as tolerated"],
                    "monitoring_parameters": ["Heart rate", "Blood pressure", "Symptoms"]
                }
            ]
        }
        
        return therapy_recommendations.get(condition, [])
    
    def _adjust_monitoring_for_patient(self, protocol: Dict[str, Any], patient_info: Dict[str, Any],
                                     conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Adjust monitoring protocol based on patient factors"""
        adjusted = protocol.copy()
        
        # Increase monitoring frequency for high-risk patients
        age_group = patient_info.get("age_group")
        if age_group == "geriatric":
            adjusted["priority"] = "high"
            adjusted["implementation_steps"].append("Increased monitoring frequency for geriatric patient")
        
        # Adjust for comorbidities
        patient_conditions = {cond["normalized_name"] for cond in conditions}
        
        if "kidney disease" in patient_conditions:
            adjusted["monitoring_parameters"].append("Enhanced kidney function monitoring")
        
        if "liver disease" in patient_conditions:
            adjusted["monitoring_parameters"].append("Enhanced liver function monitoring")
        
        return adjusted
    
    def _categorize_recommendations(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize recommendations by type and priority"""
        categorized = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "monitoring": [],
            "dosage_adjustments": [],
            "alternatives": [],
            "lifestyle": []
        }
        
        for rec in recommendations:
            # Priority categorization
            priority = rec["priority"]
            categorized[f"{priority}_priority"].append(rec)
            
            # Type categorization
            rec_type = rec["type"]
            if rec_type == "monitoring":
                categorized["monitoring"].append(rec)
            elif rec_type == "dosage":
                categorized["dosage_adjustments"].append(rec)
            elif rec_type == "alternative":
                categorized["alternatives"].append(rec)
            elif rec_type == "lifestyle":
                categorized["lifestyle"].append(rec)
        
        return categorized
    
    def _generate_recommendations_summary(self, recommendations: List[Dict], categorized: Dict[str, List]) -> str:
        """Generate human-readable recommendations summary"""
        if not recommendations:
            return "No specific clinical recommendations at this time"
        
        total = len(recommendations)
        high_priority = len(categorized["high_priority"])
        monitoring = len(categorized["monitoring"])
        alternatives = len(categorized["alternatives"])
        
        summary_parts = [f"Generated {total} clinical recommendation(s)"]
        
        if high_priority > 0:
            summary_parts.append(f"{high_priority} high priority action(s)")
        if monitoring > 0:
            summary_parts.append(f"{monitoring} monitoring protocol(s)")
        if alternatives > 0:
            summary_parts.append(f"{alternatives} therapy alternative(s)")
        
        return "; ".join(summary_parts)
    
    def _generate_implementation_plan(self, recommendations: List[Dict]) -> List[str]:
        """Generate prioritized implementation plan"""
        if not recommendations:
            return ["Continue current care plan"]
        
        plan = []
        
        # High priority recommendations first
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        if high_priority:
            plan.append("IMMEDIATE ACTIONS:")
            for rec in high_priority:
                plan.append(f"• {rec['recommendation']}")
        
        # Medium priority recommendations
        medium_priority = [r for r in recommendations if r["priority"] == "medium"]
        if medium_priority:
            plan.append("SHORT-TERM ACTIONS (within 1-2 weeks):")
            for rec in medium_priority:
                plan.append(f"• {rec['recommendation']}")
        
        # Monitoring recommendations
        monitoring = [r for r in recommendations if r["type"] == "monitoring"]
        if monitoring:
            plan.append("ONGOING MONITORING:")
            for rec in monitoring:
                plan.extend([f"• {param}" for param in rec["monitoring_parameters"]])
        
        return plan
    
    # Helper methods (simplified versions of methods from other classes)
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
    
    def _get_observation_interpretation(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract observation interpretation"""
        interp = resource.get("interpretation")
        if isinstance(interp, dict):
            return interp.get("text") or (interp.get("coding", [{}])[0].get("display") if interp.get("coding") else None)
        elif isinstance(interp, list) and interp:
            first = interp[0]
            return first.get("text") or (first.get("coding", [{}])[0].get("display") if first.get("coding") else None)
        return None
    
    def _normalize_medication_name(self, name: str) -> str:
        """Normalize medication name"""
        if not name:
            return ""
        normalized = name.lower().strip()
        normalized = re.sub(r'\d+\s*(mg|mcg|g|ml|units?)\b', '', normalized)
        normalized = re.sub(r'\b(tablet|capsule|injection|solution)s?\b', '', normalized)
        return re.sub(r'\s+', ' ', normalized).strip()
    
    def _normalize_condition_name(self, name: str) -> str:
        """Normalize condition name"""
        if not name:
            return ""
        normalized = name.lower().strip()
        mappings = {
            "diabetes mellitus": "diabetes",
            "diabetes type 2": "diabetes",
            "myocardial infarction": "heart attack",
            "congestive heart failure": "heart failure"
        }
        return mappings.get(normalized, normalized)
    
    def _extract_dosage_info(self, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract dosage information"""
        dosage_instructions = resource.get("dosageInstruction", [])
        if dosage_instructions:
            return {"text": dosage_instructions[0].get("text", "")}
        return None
    
    def _extract_indication(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract medication indication"""
        reason_code = resource.get("reasonCode", [])
        if reason_code:
            return reason_code[0].get("text") or (reason_code[0].get("coding", [{}])[0].get("display") if reason_code[0].get("coding") else None)
        return None
    
    def _extract_condition_severity(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract condition severity"""
        severity = resource.get("severity", {})
        return severity.get("text") or (severity.get("coding", [{}])[0].get("display") if severity.get("coding") else None)
    
    def _initialize_guideline_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize clinical guidelines database"""
        return {
            "metformin": [
                {
                    "type": "monitoring",
                    "recommendation": "Monitor kidney function every 3-6 months",
                    "rationale": "Risk of lactic acidosis with kidney impairment",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["Check baseline creatinine", "Schedule regular follow-up"],
                    "monitoring_parameters": ["Serum creatinine", "eGFR", "BUN"],
                    "lab_criteria": [{"lab": "creatinine", "operator": "<", "value": 1.5, "required": True}]
                },
                {
                    "type": "dosage",
                    "recommendation": "Reduce dose if eGFR 30-45 mL/min/1.73m²",
                    "rationale": "Prevent lactic acidosis in reduced kidney function",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["Calculate eGFR", "Adjust dose accordingly"],
                    "monitoring_parameters": ["Kidney function", "Lactate levels"],
                    "lab_criteria": [{"lab": "egfr", "operator": "<", "value": 45, "required": False}]
                }
            ],
            "warfarin": [
                {
                    "type": "monitoring",
                    "recommendation": "Monitor INR weekly initially, then monthly when stable",
                    "rationale": "Narrow therapeutic window requires close monitoring",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["Check baseline INR", "Establish monitoring schedule"],
                    "monitoring_parameters": ["INR", "Bleeding signs", "Bruising"],
                    "age_group": "adult"
                },
                {
                    "type": "monitoring",
                    "recommendation": "Monitor INR every 1-2 weeks",
                    "rationale": "Increased bleeding risk in elderly patients",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["More frequent monitoring", "Lower target INR"],
                    "monitoring_parameters": ["INR", "Bleeding signs", "Falls risk"],
                    "age_group": "geriatric"
                }
            ],
            "simvastatin": [
                {
                    "type": "monitoring",
                    "recommendation": "Monitor liver enzymes at baseline, 12 weeks, then annually",
                    "rationale": "Risk of hepatotoxicity",
                    "evidence_level": "moderate",
                    "priority": "medium",
                    "implementation_steps": ["Check baseline ALT/AST", "Schedule follow-up"],
                    "monitoring_parameters": ["ALT", "AST", "Muscle symptoms"]
                },
                {
                    "type": "dosage",
                    "recommendation": "Limit to 20mg daily with amiodarone",
                    "rationale": "Increased statin levels and myopathy risk",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["Review drug interactions", "Adjust dose"],
                    "monitoring_parameters": ["Muscle pain", "CK levels"]
                }
            ],
            "lisinopril": [
                {
                    "type": "monitoring",
                    "recommendation": "Monitor potassium and creatinine within 1-2 weeks of initiation",
                    "rationale": "Risk of hyperkalemia and acute kidney injury",
                    "evidence_level": "high",
                    "priority": "high",
                    "implementation_steps": ["Check baseline labs", "Schedule early follow-up"],
                    "monitoring_parameters": ["Potassium", "Creatinine", "Blood pressure"]
                }
            ]
        }
    
    def _initialize_monitoring_protocols(self) -> Dict[str, Dict[str, Any]]:
        """Initialize medication monitoring protocols"""
        return {
            "digoxin": {
                "recommendation": "Monitor digoxin levels, electrolytes, and kidney function",
                "rationale": "Narrow therapeutic window and multiple factors affecting levels",
                "evidence_level": "high",
                "priority": "high",
                "implementation_steps": ["Check baseline levels", "Monitor electrolytes", "Assess kidney function"],
                "monitoring_parameters": ["Digoxin level", "Potassium", "Magnesium", "Creatinine"]
            },
            "lithium": {
                "recommendation": "Monitor lithium levels every 5-7 days initially, then every 3-6 months",
                "rationale": "Narrow therapeutic window and risk of toxicity",
                "evidence_level": "high",
                "priority": "high",
                "implementation_steps": ["Check levels 12h post-dose", "Monitor hydration status"],
                "monitoring_parameters": ["Lithium level", "Creatinine", "Thyroid function", "Tremor"]
            }
        }
    
    def _initialize_alternative_therapies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize alternative therapy database"""
        return {
            "diabetes": [
                {"medication": "sitagliptin", "indication": "Alternative to metformin if contraindicated"},
                {"medication": "insulin", "indication": "Advanced diabetes or metformin failure"}
            ],
            "hypertension": [
                {"medication": "amlodipine", "indication": "Alternative to ACE inhibitors"},
                {"medication": "hydrochlorothiazide", "indication": "Add-on therapy for blood pressure control"}
            ]
        }
    
    def _initialize_drug_food_interactions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize drug-food interaction database"""
        return {
            "warfarin": [
                {
                    "recommendation": "Maintain consistent vitamin K intake",
                    "rationale": "Variable vitamin K affects INR stability",
                    "evidence_level": "high",
                    "implementation_steps": ["Educate about vitamin K foods", "Maintain consistent diet"]
                }
            ],
            "metformin": [
                {
                    "recommendation": "Take with meals to reduce GI upset",
                    "rationale": "Food reduces gastrointestinal side effects",
                    "evidence_level": "moderate",
                    "implementation_steps": ["Take with breakfast and dinner", "Start with lower doses"]
                }
            ],
            "alendronate": [
                {
                    "recommendation": "Take on empty stomach with water, remain upright 30 minutes",
                    "rationale": "Food significantly reduces absorption",
                    "evidence_level": "high",
                    "implementation_steps": ["Take first thing in morning", "Wait 30 minutes before eating"]
                }
            ]
        }