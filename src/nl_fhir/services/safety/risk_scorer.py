"""
Story 4.2: Safety Risk Scoring and Alert Generation System
Multi-factor risk assessment with actionable recommendations
"""

from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import math
from datetime import datetime


class RiskLevel(Enum):
    """Overall risk level classification"""
    MINIMAL = "minimal"     # 0-20: Routine care
    LOW = "low"            # 21-40: Standard monitoring
    MODERATE = "moderate"   # 41-60: Enhanced monitoring
    HIGH = "high"          # 61-80: Close monitoring required
    CRITICAL = "critical"   # 81-100: Immediate intervention


class AlertSeverity(Enum):
    """Safety alert severity levels"""
    INFO = "info"          # Informational only
    WARNING = "warning"    # Attention required
    ALERT = "alert"        # Action recommended
    URGENT = "urgent"      # Immediate action required


@dataclass
class SafetyAlert:
    """Safety alert model"""
    alert_id: str
    severity: AlertSeverity
    category: str
    title: str
    description: str
    affected_medications: List[str]
    required_actions: List[str]
    timeline: str
    escalation_criteria: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "affected_medications": self.affected_medications,
            "required_actions": self.required_actions,
            "timeline": self.timeline,
            "escalation_criteria": self.escalation_criteria
        }


@dataclass
class SafetyRiskScore:
    """Comprehensive safety risk score"""
    overall_score: float
    risk_level: RiskLevel
    contributing_factors: Dict[str, float]
    risk_components: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    monitoring_requirements: List[str]
    escalation_triggers: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "risk_level": self.risk_level.value,
            "contributing_factors": self.contributing_factors,
            "risk_components": self.risk_components,
            "recommendations": self.recommendations,
            "monitoring_requirements": self.monitoring_requirements,
            "escalation_triggers": self.escalation_triggers
        }


class SafetyRiskScorer:
    """Comprehensive safety risk assessment and alert generation"""
    
    def __init__(self):
        self.risk_weights = self._initialize_risk_weights()
        self.alert_thresholds = self._initialize_alert_thresholds()
        self.escalation_criteria = self._initialize_escalation_criteria()
    
    def calculate_safety_risk_score(self, bundle: Dict[str, Any], 
                                  interaction_results: Dict[str, Any],
                                  contraindication_results: Dict[str, Any],
                                  dosage_results: Dict[str, Any]) -> SafetyRiskScore:
        """
        Calculate comprehensive safety risk score for FHIR bundle
        
        Returns multi-factor risk assessment with actionable recommendations
        """
        
        # Extract patient and medication information
        medications = self._extract_medications(bundle)
        patient_info = self._extract_patient_info(bundle)
        conditions = self._extract_conditions(bundle)
        
        # Calculate individual risk components
        risk_components = {
            "drug_interactions": self._score_drug_interactions(interaction_results),
            "contraindications": self._score_contraindications(contraindication_results),
            "dosage_concerns": self._score_dosage_safety(dosage_results),
            "patient_complexity": self._score_patient_complexity(patient_info, conditions, medications),
            "monitoring_requirements": self._score_monitoring_needs(medications, conditions),
            "medication_burden": self._score_medication_burden(medications)
        }
        
        # Calculate weighted overall score
        overall_score = self._calculate_weighted_risk(risk_components)
        
        # Determine risk level
        risk_level = self._classify_risk_level(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_risk_recommendations(risk_components, risk_level)
        
        # Generate monitoring requirements
        monitoring_requirements = self._generate_monitoring_requirements(risk_components, medications)
        
        # Generate escalation triggers
        escalation_triggers = self._generate_escalation_triggers(risk_components, risk_level)
        
        # Extract contributing factors for transparency
        contributing_factors = {component: data["score"] for component, data in risk_components.items()}
        
        return SafetyRiskScore(
            overall_score=overall_score,
            risk_level=risk_level,
            contributing_factors=contributing_factors,
            risk_components=risk_components,
            recommendations=recommendations,
            monitoring_requirements=monitoring_requirements,
            escalation_triggers=escalation_triggers
        )
    
    def generate_safety_alerts(self, risk_score: SafetyRiskScore, 
                              interaction_results: Dict[str, Any],
                              contraindication_results: Dict[str, Any],
                              dosage_results: Dict[str, Any]) -> List[SafetyAlert]:
        """Generate prioritized safety alerts based on risk assessment"""
        
        alerts = []
        alert_counter = 1
        
        # Critical drug interactions
        if interaction_results.get("has_interactions"):
            contraindicated = [i for i in interaction_results.get("interactions", []) 
                             if i.get("severity") == "contraindicated"]
            major = [i for i in interaction_results.get("interactions", []) 
                    if i.get("severity") == "major"]
            
            if contraindicated:
                alert = SafetyAlert(
                    alert_id=f"ALERT-{alert_counter:03d}",
                    severity=AlertSeverity.URGENT,
                    category="Drug Interactions",
                    title="Contraindicated Drug Combination Detected",
                    description=f"Found {len(contraindicated)} contraindicated drug interaction(s) requiring immediate attention",
                    affected_medications=[i["drug_a"] for i in contraindicated] + [i["drug_b"] for i in contraindicated],
                    required_actions=[
                        "Stop contraindicated medications immediately",
                        "Consult prescriber for alternative therapy",
                        "Monitor patient for adverse effects"
                    ],
                    timeline="Immediate (within 1 hour)",
                    escalation_criteria=["Patient shows signs of adverse reaction", "Unable to contact prescriber within 2 hours"]
                )
                alerts.append(alert)
                alert_counter += 1
            
            if major:
                alert = SafetyAlert(
                    alert_id=f"ALERT-{alert_counter:03d}",
                    severity=AlertSeverity.ALERT,
                    category="Drug Interactions",
                    title="Major Drug Interactions Require Monitoring",
                    description=f"Found {len(major)} major drug interaction(s) requiring close monitoring",
                    affected_medications=[i["drug_a"] for i in major] + [i["drug_b"] for i in major],
                    required_actions=[
                        "Implement enhanced monitoring protocols",
                        "Consider dose adjustments",
                        "Educate patient about signs/symptoms to watch"
                    ],
                    timeline="Within 24 hours",
                    escalation_criteria=["Patient develops symptoms", "Lab values show adverse trends"]
                )
                alerts.append(alert)
                alert_counter += 1
        
        # Absolute contraindications
        if contraindication_results.get("has_contraindications"):
            absolute = [c for c in contraindication_results.get("contraindications", []) 
                       if c.get("severity") == "absolute"]
            
            if absolute:
                alert = SafetyAlert(
                    alert_id=f"ALERT-{alert_counter:03d}",
                    severity=AlertSeverity.URGENT,
                    category="Contraindications",
                    title="Absolute Contraindications Detected",
                    description=f"Found {len(absolute)} absolute contraindication(s) requiring medication discontinuation",
                    affected_medications=[c["medication"] for c in absolute],
                    required_actions=[
                        "Discontinue contraindicated medications",
                        "Assess for alternative therapies",
                        "Monitor for withdrawal effects if applicable"
                    ],
                    timeline="Immediate (within 1 hour)",
                    escalation_criteria=["Patient at immediate risk", "No safe alternatives available"]
                )
                alerts.append(alert)
                alert_counter += 1
        
        # Critical dosage violations
        if dosage_results.get("has_dosage_violations"):
            critical = [v for v in dosage_results.get("violations", []) 
                       if v.get("severity") == "critical"]
            
            if critical:
                alert = SafetyAlert(
                    alert_id=f"ALERT-{alert_counter:03d}",
                    severity=AlertSeverity.URGENT,
                    category="Dosage Safety",
                    title="Critical Dosage Violations Detected",
                    description=f"Found {len(critical)} critical dosage violation(s) with potential for serious harm",
                    affected_medications=[v["medication"] for v in critical],
                    required_actions=[
                        "Verify and correct dosing immediately",
                        "Assess patient for signs of overdose/underdose",
                        "Consider antidote if overdose suspected"
                    ],
                    timeline="Immediate (within 30 minutes)",
                    escalation_criteria=["Signs of toxicity present", "Dosing error confirmed"]
                )
                alerts.append(alert)
                alert_counter += 1
        
        # High overall risk score
        if risk_score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            alert = SafetyAlert(
                alert_id=f"ALERT-{alert_counter:03d}",
                severity=AlertSeverity.ALERT if risk_score.risk_level == RiskLevel.HIGH else AlertSeverity.URGENT,
                category="Overall Risk",
                title=f"{risk_score.risk_level.value.title()} Safety Risk Profile",
                description=f"Patient has {risk_score.risk_level.value} overall safety risk (score: {risk_score.overall_score:.1f}/100)",
                affected_medications=[],  # Risk may involve multiple factors
                required_actions=risk_score.recommendations[:3],  # Top 3 recommendations
                timeline="Within 24 hours" if risk_score.risk_level == RiskLevel.HIGH else "Within 4 hours",
                escalation_criteria=risk_score.escalation_triggers
            )
            alerts.append(alert)
            alert_counter += 1
        
        return alerts
    
    def _score_drug_interactions(self, interaction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Score drug interaction risk component"""
        if not interaction_results.get("has_interactions"):
            return {"score": 0, "description": "No significant drug interactions", "risk_factors": []}
        
        interactions = interaction_results.get("interactions", [])
        severity_counts = interaction_results.get("severity_breakdown", {})
        
        # Weight by severity
        score = (
            severity_counts.get("contraindicated", 0) * 30 +
            severity_counts.get("major", 0) * 20 +
            severity_counts.get("moderate", 0) * 10 +
            severity_counts.get("minor", 0) * 5
        )
        
        # Cap at reasonable maximum
        score = min(score, 80)
        
        risk_factors = []
        if severity_counts.get("contraindicated", 0) > 0:
            risk_factors.append(f"{severity_counts['contraindicated']} contraindicated interaction(s)")
        if severity_counts.get("major", 0) > 0:
            risk_factors.append(f"{severity_counts['major']} major interaction(s)")
        
        return {
            "score": score,
            "description": f"Drug interaction risk from {len(interactions)} interaction(s)",
            "risk_factors": risk_factors,
            "details": interactions
        }
    
    def _score_contraindications(self, contraindication_results: Dict[str, Any]) -> Dict[str, Any]:
        """Score contraindication risk component"""
        if not contraindication_results.get("has_contraindications"):
            return {"score": 0, "description": "No contraindications detected", "risk_factors": []}
        
        contraindications = contraindication_results.get("contraindications", [])
        severity_counts = contraindication_results.get("severity_breakdown", {})
        
        # Weight by severity
        score = (
            severity_counts.get("absolute", 0) * 25 +
            severity_counts.get("relative", 0) * 15 +
            severity_counts.get("caution", 0) * 8 +
            severity_counts.get("warning", 0) * 3
        )
        
        score = min(score, 70)
        
        risk_factors = []
        if severity_counts.get("absolute", 0) > 0:
            risk_factors.append(f"{severity_counts['absolute']} absolute contraindication(s)")
        if severity_counts.get("relative", 0) > 0:
            risk_factors.append(f"{severity_counts['relative']} relative contraindication(s)")
        
        return {
            "score": score,
            "description": f"Contraindication risk from {len(contraindications)} contraindication(s)",
            "risk_factors": risk_factors,
            "details": contraindications
        }
    
    def _score_dosage_safety(self, dosage_results: Dict[str, Any]) -> Dict[str, Any]:
        """Score dosage safety risk component"""
        if not dosage_results.get("has_dosage_violations"):
            return {"score": 0, "description": "All dosages within safe ranges", "risk_factors": []}
        
        violations = dosage_results.get("violations", [])
        severity_counts = dosage_results.get("severity_breakdown", {})
        
        # Weight by severity
        score = (
            severity_counts.get("critical", 0) * 25 +
            severity_counts.get("high", 0) * 15 +
            severity_counts.get("moderate", 0) * 8 +
            severity_counts.get("low", 0) * 3
        )
        
        score = min(score, 65)
        
        risk_factors = []
        if severity_counts.get("critical", 0) > 0:
            risk_factors.append(f"{severity_counts['critical']} critical dosage violation(s)")
        if severity_counts.get("high", 0) > 0:
            risk_factors.append(f"{severity_counts['high']} high-risk dosage violation(s)")
        
        return {
            "score": score,
            "description": f"Dosage safety risk from {len(violations)} violation(s)",
            "risk_factors": risk_factors,
            "details": violations
        }
    
    def _score_patient_complexity(self, patient_info: Dict[str, Any], 
                                 conditions: List[Dict[str, Any]], 
                                 medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score patient complexity risk factors"""
        score = 0
        risk_factors = []
        
        # Age-based risk
        age = patient_info.get("age", 0)
        if age >= 80:
            score += 15
            risk_factors.append("Age ≥80 years (increased sensitivity)")
        elif age >= 65:
            score += 10
            risk_factors.append("Age 65-79 years (geriatric considerations)")
        elif age < 18:
            score += 8
            risk_factors.append("Pediatric patient (specialized dosing)")
        
        # Comorbidity burden
        condition_count = len(conditions)
        if condition_count >= 5:
            score += 15
            risk_factors.append(f"Multiple comorbidities ({condition_count} conditions)")
        elif condition_count >= 3:
            score += 8
            risk_factors.append(f"Multiple comorbidities ({condition_count} conditions)")
        
        # High-risk conditions
        high_risk_conditions = ["kidney disease", "liver disease", "heart failure", "diabetes"]
        patient_conditions = [cond["normalized_name"] for cond in conditions]
        
        for condition in high_risk_conditions:
            if any(condition in pc for pc in patient_conditions):
                score += 5
                risk_factors.append(f"{condition.title()} (requires specialized monitoring)")
        
        return {
            "score": min(score, 40),
            "description": "Patient complexity and comorbidity risk",
            "risk_factors": risk_factors,
            "details": {
                "age": age,
                "condition_count": condition_count,
                "high_risk_conditions": [c for c in high_risk_conditions if any(c in pc for pc in patient_conditions)]
            }
        }
    
    def _score_monitoring_needs(self, medications: List[Dict[str, Any]], 
                               conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score monitoring requirement complexity"""
        high_monitoring_meds = ["warfarin", "digoxin", "lithium", "methotrexate", "amiodarone"]
        med_names = [med["normalized_name"] for med in medications]
        
        high_monitoring_count = sum(1 for med in high_monitoring_meds if any(med in mn for mn in med_names))
        
        score = high_monitoring_count * 8
        risk_factors = []
        
        if high_monitoring_count > 0:
            risk_factors.append(f"{high_monitoring_count} medication(s) requiring intensive monitoring")
        
        # Additional monitoring for conditions
        high_monitoring_conditions = ["kidney disease", "liver disease", "heart failure"]
        condition_names = [cond["normalized_name"] for cond in conditions]
        
        monitoring_conditions = sum(1 for cond in high_monitoring_conditions 
                                   if any(cond in cn for cn in condition_names))
        
        if monitoring_conditions > 0:
            score += monitoring_conditions * 5
            risk_factors.append(f"{monitoring_conditions} condition(s) requiring enhanced monitoring")
        
        return {
            "score": min(score, 35),
            "description": "Monitoring requirement complexity",
            "risk_factors": risk_factors,
            "details": {
                "high_monitoring_medications": high_monitoring_count,
                "monitoring_conditions": monitoring_conditions
            }
        }
    
    def _score_medication_burden(self, medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score medication burden (polypharmacy risk)"""
        med_count = len(medications)
        
        if med_count >= 10:
            score = 20
            risk_level = "severe polypharmacy"
        elif med_count >= 6:
            score = 15
            risk_level = "polypharmacy"
        elif med_count >= 4:
            score = 8
            risk_level = "moderate medication burden"
        else:
            score = 0
            risk_level = "minimal medication burden"
        
        risk_factors = []
        if med_count >= 6:
            risk_factors.append(f"{med_count} medications (polypharmacy risk)")
        
        return {
            "score": score,
            "description": f"Medication burden: {risk_level}",
            "risk_factors": risk_factors,
            "details": {
                "medication_count": med_count,
                "polypharmacy_threshold": med_count >= 6
            }
        }
    
    def _calculate_weighted_risk(self, risk_components: Dict[str, Dict[str, Any]]) -> float:
        """Calculate weighted overall risk score"""
        total_weighted_score = 0
        total_weight = 0
        
        for component, weight in self.risk_weights.items():
            if component in risk_components:
                component_score = risk_components[component]["score"]
                total_weighted_score += component_score * weight
                total_weight += weight
        
        # Normalize to 0-100 scale
        if total_weight > 0:
            normalized_score = (total_weighted_score / total_weight)
        else:
            normalized_score = 0
        
        return min(normalized_score, 100)
    
    def _classify_risk_level(self, score: float) -> RiskLevel:
        """Classify overall risk level based on score"""
        if score >= 81:
            return RiskLevel.CRITICAL
        elif score >= 61:
            return RiskLevel.HIGH
        elif score >= 41:
            return RiskLevel.MODERATE
        elif score >= 21:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _generate_risk_recommendations(self, risk_components: Dict[str, Dict], risk_level: RiskLevel) -> List[str]:
        """Generate prioritized risk mitigation recommendations"""
        recommendations = []
        
        # Prioritize by component scores
        sorted_components = sorted(risk_components.items(), 
                                 key=lambda x: x[1]["score"], reverse=True)
        
        for component, data in sorted_components:
            if data["score"] > 10:  # Only significant risk factors
                if component == "drug_interactions":
                    recommendations.append("Review and manage drug interactions with prescriber")
                elif component == "contraindications":
                    recommendations.append("Address contraindications and consider alternative therapies")
                elif component == "dosage_concerns":
                    recommendations.append("Verify and adjust medication dosages as needed")
                elif component == "patient_complexity":
                    recommendations.append("Implement enhanced monitoring for high-risk patient factors")
                elif component == "monitoring_requirements":
                    recommendations.append("Establish comprehensive monitoring protocols")
                elif component == "medication_burden":
                    recommendations.append("Consider medication review and deprescribing opportunities")
        
        # Risk level specific recommendations
        if risk_level == RiskLevel.CRITICAL:
            recommendations.insert(0, "URGENT: Implement immediate safety interventions")
        elif risk_level == RiskLevel.HIGH:
            recommendations.insert(0, "Prioritize safety review and intervention planning")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_monitoring_requirements(self, risk_components: Dict[str, Dict], 
                                        medications: List[Dict[str, Any]]) -> List[str]:
        """Generate monitoring requirements based on risk assessment"""
        monitoring = []
        
        # Standard monitoring for high-risk components
        if risk_components["drug_interactions"]["score"] > 15:
            monitoring.append("Enhanced drug interaction monitoring")
        
        if risk_components["dosage_concerns"]["score"] > 15:
            monitoring.append("Frequent dosage review and adjustment")
        
        if risk_components["patient_complexity"]["score"] > 20:
            monitoring.append("Comprehensive patient assessment and vital sign monitoring")
        
        # Medication-specific monitoring
        high_monitoring_meds = {
            "warfarin": "INR monitoring every 1-2 weeks",
            "digoxin": "Digoxin levels and electrolyte monitoring",
            "lithium": "Lithium levels every 3-6 months",
            "metformin": "Kidney function monitoring every 3-6 months"
        }
        
        for medication in medications:
            med_name = medication["normalized_name"]
            for high_risk_med, monitoring_req in high_monitoring_meds.items():
                if high_risk_med in med_name:
                    monitoring.append(monitoring_req)
        
        return list(set(monitoring))  # Remove duplicates
    
    def _generate_escalation_triggers(self, risk_components: Dict[str, Dict], risk_level: RiskLevel) -> List[str]:
        """Generate escalation triggers based on risk assessment"""
        triggers = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            triggers.append("Any signs of adverse drug reactions")
            triggers.append("Unexpected clinical deterioration")
        
        if risk_components["drug_interactions"]["score"] > 20:
            triggers.append("Signs of drug interaction effects")
        
        if risk_components["dosage_concerns"]["score"] > 20:
            triggers.append("Signs of medication toxicity or therapeutic failure")
        
        if risk_components["patient_complexity"]["score"] > 25:
            triggers.append("Changes in kidney or liver function")
            triggers.append("New symptoms or complications")
        
        return triggers
    
    # Helper methods for data extraction
    def _extract_medications(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract medications from FHIR bundle"""
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
    
    def _extract_patient_info(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient information from FHIR bundle"""
        patient_info = {}
        entries = bundle.get("entry", []) or []
        
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "Patient":
                birth_date = resource.get("birthDate")
                if birth_date:
                    from datetime import datetime, date
                    try:
                        birth_dt = datetime.strptime(birth_date, "%Y-%m-%d").date()
                        today = date.today()
                        age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))
                        patient_info["age"] = age
                    except:
                        pass
                
                patient_info["gender"] = resource.get("gender")
                break
        
        return patient_info
    
    def _extract_conditions(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract conditions from FHIR bundle"""
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
    
    def _normalize_medication_name(self, name: str) -> str:
        """Normalize medication name"""
        if not name:
            return ""
        import re
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
    
    def _initialize_risk_weights(self) -> Dict[str, float]:
        """Initialize risk component weights for scoring"""
        return {
            "drug_interactions": 0.25,      # 25% weight
            "contraindications": 0.22,      # 22% weight
            "dosage_concerns": 0.20,        # 20% weight
            "patient_complexity": 0.15,     # 15% weight
            "monitoring_requirements": 0.10, # 10% weight
            "medication_burden": 0.08       # 8% weight
        }
    
    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert generation thresholds"""
        return {
            "drug_interactions": {
                "urgent": {"contraindicated": 1},
                "alert": {"major": 2},
                "warning": {"moderate": 3}
            },
            "contraindications": {
                "urgent": {"absolute": 1},
                "alert": {"relative": 2},
                "warning": {"caution": 3}
            },
            "dosage_violations": {
                "urgent": {"critical": 1},
                "alert": {"high": 2},
                "warning": {"moderate": 3}
            }
        }
    
    def _initialize_escalation_criteria(self) -> Dict[str, List[str]]:
        """Initialize escalation criteria"""
        return {
            "immediate": [
                "Patient shows signs of adverse reaction",
                "Contraindicated medication combination active",
                "Critical dosage violation confirmed"
            ],
            "urgent": [
                "Unable to contact prescriber within 2 hours",
                "Patient condition deteriorating",
                "Multiple high-risk factors present"
            ],
            "routine": [
                "Monitoring parameters trending outside normal",
                "Patient reports new symptoms",
                "Medication effectiveness concerns"
            ]
        }