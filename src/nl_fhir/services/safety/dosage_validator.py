"""
Story 4.2: Dosage Safety Validation Framework
Safe prescribing range validation with age/weight considerations
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
import re
from datetime import datetime, date


class DosageViolationSeverity(Enum):
    """Dosage violation severity levels"""
    CRITICAL = "critical"     # Potentially life-threatening
    HIGH = "high"            # Serious adverse effects likely
    MODERATE = "moderate"    # Monitoring required
    LOW = "low"             # Minor concern


@dataclass
class DosageRange:
    """Safe dosage range model"""
    min_dose: float
    max_dose: float
    unit: str
    frequency: str
    route: str
    age_group: Optional[str] = None
    weight_based: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_dose": self.min_dose,
            "max_dose": self.max_dose,
            "unit": self.unit,
            "frequency": self.frequency,
            "route": self.route,
            "age_group": self.age_group,
            "weight_based": self.weight_based
        }


@dataclass
class DosageViolation:
    """Dosage safety violation model"""
    medication: str
    prescribed_dose: str
    safe_range: DosageRange
    violation_type: str
    severity: DosageViolationSeverity
    reason: str
    recommendation: str
    monitoring_requirements: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "medication": self.medication,
            "prescribed_dose": self.prescribed_dose,
            "safe_range": self.safe_range.to_dict(),
            "violation_type": self.violation_type,
            "severity": self.severity.value,
            "reason": self.reason,
            "recommendation": self.recommendation,
            "monitoring_requirements": self.monitoring_requirements
        }


class DosageValidator:
    """Comprehensive dosage safety validation"""
    
    def __init__(self):
        self.dosage_database = self._initialize_dosage_database()
        self.age_weight_factors = self._initialize_age_weight_factors()
        self.route_conversions = self._initialize_route_conversions()
    
    def validate_bundle_dosages(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all medication dosages in a FHIR bundle
        
        Returns comprehensive dosage safety analysis
        """
        medications = self._extract_medications_with_dosage(bundle)
        patient_info = self._extract_patient_info(bundle)
        
        violations = []
        
        for medication in medications:
            dosage_violations = self._validate_medication_dosage(medication, patient_info)
            violations.extend([v.to_dict() for v in dosage_violations])
        
        # Generate summary
        severity_counts = self._count_by_severity(violations)
        summary = self._generate_dosage_summary(violations, severity_counts)
        
        return {
            "has_dosage_violations": len(violations) > 0,
            "violation_count": len(violations),
            "violations": violations,
            "severity_breakdown": severity_counts,
            "summary": summary,
            "recommendations": self._generate_dosage_recommendations(violations)
        }
    
    def _extract_medications_with_dosage(self, bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all medications with dosage information from FHIR bundle"""
        medications = []
        entries = bundle.get("entry", []) or []
        
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "MedicationRequest":
                med_name = self._get_medication_name(resource)
                dosage_info = self._extract_dosage_info(resource)
                
                if med_name and dosage_info:
                    medications.append({
                        "name": med_name,
                        "normalized_name": self._normalize_medication_name(med_name),
                        "dosage": dosage_info,
                        "resource": resource
                    })
        
        return medications
    
    def _extract_patient_info(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient demographics for dosage calculations"""
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
                        
                        # Determine age group
                        if age < 2:
                            patient_info["age_group"] = "infant"
                        elif age < 12:
                            patient_info["age_group"] = "child"
                        elif age < 18:
                            patient_info["age_group"] = "adolescent"
                        elif age >= 65:
                            patient_info["age_group"] = "geriatric"
                        else:
                            patient_info["age_group"] = "adult"
                    except:
                        pass
                
                # Extract weight if available
                # Note: Weight would typically come from Observation resources
                # This is a simplified extraction
                break
        
        # Look for weight observations
        for entry in entries:
            resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
            if resource.get("resourceType") == "Observation":
                code = resource.get("code", {})
                if "weight" in str(code).lower():
                    value_qty = resource.get("valueQuantity", {})
                    if value_qty.get("value") and value_qty.get("unit") == "kg":
                        patient_info["weight_kg"] = value_qty["value"]
                    elif value_qty.get("value") and value_qty.get("unit") == "lbs":
                        patient_info["weight_kg"] = value_qty["value"] * 0.453592
        
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
    
    def _extract_dosage_info(self, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract dosage information from MedicationRequest"""
        dosage_instructions = resource.get("dosageInstruction", [])
        if not dosage_instructions:
            return None
        
        # Use first dosage instruction
        dosage = dosage_instructions[0]
        
        dosage_info = {
            "text": dosage.get("text", ""),
            "route": self._extract_route(dosage),
            "timing": self._extract_timing(dosage),
            "dose": self._extract_dose(dosage)
        }
        
        return dosage_info
    
    def _extract_route(self, dosage: Dict[str, Any]) -> str:
        """Extract administration route"""
        route = dosage.get("route", {})
        if route.get("text"):
            return route["text"].lower()
        
        codings = route.get("coding", [])
        if codings:
            return (codings[0].get("display") or codings[0].get("code") or "oral").lower()
        
        return "oral"  # Default assumption
    
    def _extract_timing(self, dosage: Dict[str, Any]) -> Dict[str, Any]:
        """Extract timing information"""
        timing = dosage.get("timing", {})
        repeat = timing.get("repeat", {})
        
        return {
            "frequency": repeat.get("frequency", 1),
            "period": repeat.get("period", 1),
            "period_unit": repeat.get("periodUnit", "d"),
            "daily_frequency": self._calculate_daily_frequency(repeat)
        }
    
    def _extract_dose(self, dosage: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract dose information"""
        dose_and_rate = dosage.get("doseAndRate", [])
        if dose_and_rate:
            dose_qty = dose_and_rate[0].get("doseQuantity", {})
            if dose_qty.get("value") and dose_qty.get("unit"):
                return {
                    "value": dose_qty["value"],
                    "unit": dose_qty["unit"],
                    "system": dose_qty.get("system", "")
                }
        
        # Try to parse from text if structured dose not available
        text = dosage.get("text", "")
        parsed_dose = self._parse_dose_from_text(text)
        return parsed_dose
    
    def _calculate_daily_frequency(self, repeat: Dict[str, Any]) -> float:
        """Calculate how many times per day medication is taken"""
        frequency = repeat.get("frequency", 1)
        period = repeat.get("period", 1)
        period_unit = repeat.get("periodUnit", "d")
        
        # Convert to daily frequency
        if period_unit == "d":
            return frequency / period
        elif period_unit == "h":
            return (frequency / period) * 24
        elif period_unit == "wk":
            return (frequency / period) / 7
        else:
            return frequency  # Default assumption
    
    def _parse_dose_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse dose from free text"""
        if not text:
            return None
        
        # Look for dose patterns like "10 mg", "5mg", "2.5 mg"
        dose_pattern = r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?|iu)\b'
        match = re.search(dose_pattern, text.lower())
        
        if match:
            return {
                "value": float(match.group(1)),
                "unit": match.group(2),
                "system": "parsed_from_text"
            }
        
        return None
    
    def _normalize_medication_name(self, name: str) -> str:
        """Normalize medication name for dosage checking"""
        if not name:
            return ""
        
        normalized = name.lower().strip()
        # Remove dosage information to get base drug name
        normalized = re.sub(r'\d+\s*(mg|mcg|g|ml|units?)\b', '', normalized)
        normalized = re.sub(r'\b(tablet|capsule|injection|solution)s?\b', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Map to generic names
        brand_to_generic = {
            "tylenol": "acetaminophen",
            "advil": "ibuprofen", 
            "motrin": "ibuprofen",
            "zocor": "simvastatin",
            "lipitor": "atorvastatin",
            "prinivil": "lisinopril",
            "zestril": "lisinopril",
            "norvasc": "amlodipine"
        }
        
        return brand_to_generic.get(normalized, normalized)
    
    def _validate_medication_dosage(self, medication: Dict[str, Any], patient_info: Dict[str, Any]) -> List[DosageViolation]:
        """Validate dosage for a single medication"""
        violations = []
        
        med_name = medication["normalized_name"]
        dosage = medication["dosage"]
        dose_info = dosage.get("dose")
        
        if not dose_info:
            return violations
        
        # Get safe dosage ranges for this medication
        safe_ranges = self._get_safe_dosage_ranges(med_name, patient_info)
        
        for safe_range in safe_ranges:
            violation = self._check_dosage_against_range(
                medication, dose_info, dosage, safe_range, patient_info
            )
            if violation:
                violations.append(violation)
        
        return violations
    
    def _get_safe_dosage_ranges(self, med_name: str, patient_info: Dict[str, Any]) -> List[DosageRange]:
        """Get applicable safe dosage ranges for medication and patient"""
        ranges = []
        
        # Get base medication ranges
        med_ranges = self.dosage_database.get(med_name, [])
        
        age_group = patient_info.get("age_group", "adult")
        weight_kg = patient_info.get("weight_kg")
        age = patient_info.get("age")
        
        for range_data in med_ranges:
            # Check if range applies to this patient
            range_age_group = range_data.get("age_group")
            if range_age_group and range_age_group != age_group:
                continue
            
            # Apply age/weight adjustments
            dose_range = DosageRange(
                min_dose=range_data["min_dose"],
                max_dose=range_data["max_dose"],
                unit=range_data["unit"],
                frequency=range_data["frequency"],
                route=range_data["route"],
                age_group=range_age_group,
                weight_based=range_data.get("weight_based", False)
            )
            
            # Apply age/weight factors
            if age_group in self.age_weight_factors:
                factor = self.age_weight_factors[age_group].get("dose_factor", 1.0)
                dose_range.min_dose *= factor
                dose_range.max_dose *= factor
            
            # Weight-based dosing
            if dose_range.weight_based and weight_kg:
                dose_range.min_dose *= weight_kg
                dose_range.max_dose *= weight_kg
            
            ranges.append(dose_range)
        
        return ranges
    
    def _check_dosage_against_range(self, medication: Dict[str, Any], dose_info: Dict[str, Any], 
                                  dosage_info: Dict[str, Any], safe_range: DosageRange, 
                                  patient_info: Dict[str, Any]) -> Optional[DosageViolation]:
        """Check if dosage violates safe range"""
        
        prescribed_dose = dose_info["value"]
        prescribed_unit = dose_info["unit"]
        timing = dosage_info["timing"]
        route = dosage_info["route"]
        
        # Convert units if necessary
        converted_dose = self._convert_dose_units(prescribed_dose, prescribed_unit, safe_range.unit)
        if converted_dose is None:
            return None  # Cannot compare incompatible units
        
        # Calculate daily dose
        daily_frequency = timing["daily_frequency"]
        total_daily_dose = converted_dose * daily_frequency
        
        # Check route compatibility
        if not self._routes_compatible(route, safe_range.route):
            return None  # Different routes may have different dosing
        
        violation_type = None
        severity = None
        
        # Check for overdose
        if total_daily_dose > safe_range.max_dose:
            excess_ratio = total_daily_dose / safe_range.max_dose
            violation_type = "overdose"
            if excess_ratio > 3.0:
                severity = DosageViolationSeverity.CRITICAL
            elif excess_ratio > 2.0:
                severity = DosageViolationSeverity.HIGH
            elif excess_ratio > 1.5:
                severity = DosageViolationSeverity.MODERATE
            else:
                severity = DosageViolationSeverity.LOW
        
        # Check for underdose
        elif total_daily_dose < safe_range.min_dose:
            deficit_ratio = safe_range.min_dose / total_daily_dose
            violation_type = "underdose"
            if deficit_ratio > 3.0:
                severity = DosageViolationSeverity.HIGH
            elif deficit_ratio > 2.0:
                severity = DosageViolationSeverity.MODERATE
            else:
                severity = DosageViolationSeverity.LOW
        
        if violation_type:
            return DosageViolation(
                medication=medication["name"],
                prescribed_dose=f"{prescribed_dose} {prescribed_unit} {timing['frequency']}x per {timing['period']}{timing['period_unit']}",
                safe_range=safe_range,
                violation_type=violation_type,
                severity=severity,
                reason=self._generate_violation_reason(violation_type, total_daily_dose, safe_range, patient_info),
                recommendation=self._generate_dosage_recommendation(violation_type, total_daily_dose, safe_range),
                monitoring_requirements=self._get_monitoring_requirements(medication["normalized_name"], severity)
            )
        
        return None
    
    def _convert_dose_units(self, dose: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert dose between units"""
        if from_unit.lower() == to_unit.lower():
            return dose
        
        # Unit conversion factors
        conversions = {
            ("mg", "g"): 0.001,
            ("g", "mg"): 1000,
            ("mcg", "mg"): 0.001,
            ("mg", "mcg"): 1000,
            ("mcg", "g"): 0.000001,
            ("g", "mcg"): 1000000
        }
        
        conversion_key = (from_unit.lower(), to_unit.lower())
        if conversion_key in conversions:
            return dose * conversions[conversion_key]
        
        return None  # Cannot convert incompatible units
    
    def _routes_compatible(self, route1: str, route2: str) -> bool:
        """Check if administration routes are compatible for dosing comparison"""
        route1 = route1.lower()
        route2 = route2.lower()
        
        if route1 == route2:
            return True
        
        # Group compatible routes
        oral_routes = ["oral", "po", "by mouth", "sublingual"]
        parenteral_routes = ["iv", "intravenous", "im", "intramuscular", "subcutaneous", "sc"]
        
        return (route1 in oral_routes and route2 in oral_routes) or \
               (route1 in parenteral_routes and route2 in parenteral_routes)
    
    def _generate_violation_reason(self, violation_type: str, prescribed_dose: float, 
                                 safe_range: DosageRange, patient_info: Dict[str, Any]) -> str:
        """Generate human-readable reason for dosage violation"""
        age_group = patient_info.get("age_group", "adult")
        
        if violation_type == "overdose":
            return f"Prescribed dose ({prescribed_dose:.1f} {safe_range.unit}/day) exceeds maximum safe dose ({safe_range.max_dose:.1f} {safe_range.unit}/day) for {age_group} patients"
        else:  # underdose
            return f"Prescribed dose ({prescribed_dose:.1f} {safe_range.unit}/day) below therapeutic range ({safe_range.min_dose:.1f} {safe_range.unit}/day) for {age_group} patients"
    
    def _generate_dosage_recommendation(self, violation_type: str, prescribed_dose: float, 
                                      safe_range: DosageRange) -> str:
        """Generate dosage adjustment recommendation"""
        if violation_type == "overdose":
            return f"Reduce dose to maximum {safe_range.max_dose:.1f} {safe_range.unit}/day or less"
        else:  # underdose
            return f"Increase dose to at least {safe_range.min_dose:.1f} {safe_range.unit}/day for therapeutic effect"
    
    def _get_monitoring_requirements(self, medication: str, severity: DosageViolationSeverity) -> List[str]:
        """Get monitoring requirements based on medication and severity"""
        base_monitoring = {
            "acetaminophen": ["Liver function tests", "Daily maximum dose tracking"],
            "ibuprofen": ["Kidney function", "GI symptoms"],
            "simvastatin": ["Liver function tests", "Muscle symptoms"],
            "lisinopril": ["Blood pressure", "Kidney function", "Potassium levels"],
            "metformin": ["Kidney function", "Blood glucose"],
            "warfarin": ["INR", "Bleeding signs"],
            "digoxin": ["Heart rate", "Digoxin levels", "Electrolytes"]
        }
        
        monitoring = base_monitoring.get(medication, ["Vital signs", "Symptom monitoring"])
        
        if severity in [DosageViolationSeverity.CRITICAL, DosageViolationSeverity.HIGH]:
            monitoring.extend(["Immediate physician consultation", "Consider dose adjustment"])
        
        return monitoring
    
    def _count_by_severity(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count violations by severity"""
        counts = {severity.value: 0 for severity in DosageViolationSeverity}
        for violation in violations:
            severity = violation["severity"]
            counts[severity] += 1
        return counts
    
    def _generate_dosage_summary(self, violations: List[Dict], severity_counts: Dict[str, int]) -> str:
        """Generate human-readable dosage summary"""
        if not violations:
            return "All medication dosages within safe therapeutic ranges"
        
        total = len(violations)
        critical = severity_counts.get("critical", 0)
        high = severity_counts.get("high", 0)
        moderate = severity_counts.get("moderate", 0)
        low = severity_counts.get("low", 0)
        
        summary_parts = [f"Found {total} dosage concern(s)"]
        
        if critical > 0:
            summary_parts.append(f"{critical} critical (immediate action required)")
        if high > 0:
            summary_parts.append(f"{high} high priority")
        if moderate > 0:
            summary_parts.append(f"{moderate} moderate priority")
        if low > 0:
            summary_parts.append(f"{low} minor concerns")
        
        return "; ".join(summary_parts)
    
    def _generate_dosage_recommendations(self, violations: List[Dict]) -> List[str]:
        """Generate actionable recommendations for dosage violations"""
        if not violations:
            return ["All dosages appropriate - continue current regimen"]
        
        recommendations = []
        
        # Priority recommendations for severe violations
        critical = [v for v in violations if v["severity"] == "critical"]
        high = [v for v in violations if v["severity"] == "high"]
        
        if critical:
            recommendations.append("URGENT: Address critical dosage violations immediately")
            for violation in critical:
                recommendations.append(f"{violation['medication']}: {violation['recommendation']}")
        
        if high:
            recommendations.append("HIGH PRIORITY: Adjust high-risk dosages")
            for violation in high:
                recommendations.append(f"{violation['medication']}: {violation['recommendation']}")
        
        # Monitoring recommendations
        all_monitoring = []
        for violation in violations:
            all_monitoring.extend(violation.get("monitoring_requirements", []))
        
        unique_monitoring = list(set(all_monitoring))
        if unique_monitoring:
            recommendations.append("Required monitoring:")
            recommendations.extend(unique_monitoring)
        
        return recommendations
    
    def _initialize_dosage_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize comprehensive dosage safety database"""
        return {
            "acetaminophen": [
                {
                    "min_dose": 325, "max_dose": 4000, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "adult"
                },
                {
                    "min_dose": 10, "max_dose": 15, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "child", "weight_based": True
                },
                {
                    "min_dose": 160, "max_dose": 3200, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "geriatric"
                }
            ],
            "ibuprofen": [
                {
                    "min_dose": 400, "max_dose": 2400, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "adult"
                },
                {
                    "min_dose": 5, "max_dose": 10, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "child", "weight_based": True
                },
                {
                    "min_dose": 400, "max_dose": 1600, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "geriatric"
                }
            ],
            "simvastatin": [
                {
                    "min_dose": 10, "max_dose": 80, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "adult"
                },
                {
                    "min_dose": 10, "max_dose": 40, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "geriatric"
                }
            ],
            "lisinopril": [
                {
                    "min_dose": 2.5, "max_dose": 40, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "adult"
                },
                {
                    "min_dose": 2.5, "max_dose": 20, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "geriatric"
                }
            ],
            "metformin": [
                {
                    "min_dose": 500, "max_dose": 2550, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "adult"
                },
                {
                    "min_dose": 500, "max_dose": 2000, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "geriatric"
                }
            ],
            "warfarin": [
                {
                    "min_dose": 1, "max_dose": 15, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "adult"
                },
                {
                    "min_dose": 1, "max_dose": 10, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "geriatric"
                }
            ],
            "digoxin": [
                {
                    "min_dose": 0.125, "max_dose": 0.5, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "adult"
                },
                {
                    "min_dose": 0.0625, "max_dose": 0.25, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "geriatric"
                }
            ],
            "amlodipine": [
                {
                    "min_dose": 2.5, "max_dose": 10, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "adult"
                },
                {
                    "min_dose": 2.5, "max_dose": 5, "unit": "mg", "frequency": "daily",
                    "route": "oral", "age_group": "geriatric"
                }
            ]
        }
    
    def _initialize_age_weight_factors(self) -> Dict[str, Dict[str, float]]:
        """Initialize age and weight adjustment factors"""
        return {
            "infant": {"dose_factor": 0.1, "weight_factor": 1.0},
            "child": {"dose_factor": 0.5, "weight_factor": 1.0},
            "adolescent": {"dose_factor": 0.8, "weight_factor": 1.0},
            "adult": {"dose_factor": 1.0, "weight_factor": 1.0},
            "geriatric": {"dose_factor": 0.75, "weight_factor": 1.0}
        }
    
    def _initialize_route_conversions(self) -> Dict[Tuple[str, str], float]:
        """Initialize route-specific dose conversion factors"""
        return {
            ("oral", "iv"): 0.5,     # IV typically 50% of oral dose
            ("iv", "oral"): 2.0,     # Oral typically 200% of IV dose
            ("im", "oral"): 1.5,     # IM typically 150% of oral dose
            ("oral", "im"): 0.67     # Oral to IM conversion
        }