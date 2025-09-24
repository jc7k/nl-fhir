"""
NLP Patterns for DiagnosticReport Extraction
Story ID: NL-FHIR-DR-001
Identifies and extracts diagnostic report entities from clinical text
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class DiagnosticReportPattern:
    """Pattern for identifying diagnostic reports in clinical text"""
    pattern: str
    category: str
    confidence: float
    extract_fields: List[str]

class DiagnosticReportExtractor:
    """Extract diagnostic report information from clinical text"""

    # Report type patterns with category mapping
    REPORT_PATTERNS = [
        # Laboratory patterns
        DiagnosticReportPattern(
            pattern=r"(?i)(lab(?:oratory)?\s+(?:results?|report|panel)|blood\s+(?:test|work)|CBC|BMP|CMP|LFT|lipid\s+panel)",
            category="laboratory",
            confidence=0.9,
            extract_fields=["values", "conclusion"]
        ),
        DiagnosticReportPattern(
            pattern=r"(?i)(urinalysis|urine\s+(?:test|culture)|UA)",
            category="laboratory",
            confidence=0.9,
            extract_fields=["values", "bacteria"]
        ),
        DiagnosticReportPattern(
            pattern=r"(?i)(culture|sensitivity|gram\s+stain)",
            category="laboratory",
            confidence=0.85,
            extract_fields=["organism", "antibiotics"]
        ),

        # Radiology patterns
        DiagnosticReportPattern(
            pattern=r"(?i)(x-?ray|radiograph|chest\s+(?:x-?ray|film))",
            category="radiology",
            confidence=0.9,
            extract_fields=["findings", "impression"]
        ),
        DiagnosticReportPattern(
            pattern=r"(?i)(CT\s+(?:scan|imaging)|computed\s+tomography|CAT\s+scan)",
            category="radiology",
            confidence=0.95,
            extract_fields=["findings", "contrast", "impression"]
        ),
        DiagnosticReportPattern(
            pattern=r"(?i)(MRI|magnetic\s+resonance\s+imaging|MR\s+imaging)",
            category="radiology",
            confidence=0.95,
            extract_fields=["findings", "sequences", "impression"]
        ),
        DiagnosticReportPattern(
            pattern=r"(?i)(ultrasound|sonogram|echo|US\s+(?:scan|imaging))",
            category="radiology",
            confidence=0.9,
            extract_fields=["findings", "measurements"]
        ),

        # Pathology patterns
        DiagnosticReportPattern(
            pattern=r"(?i)(biopsy|histology|pathology\s+report|cytology)",
            category="pathology",
            confidence=0.95,
            extract_fields=["specimen", "microscopic", "diagnosis"]
        ),
        DiagnosticReportPattern(
            pattern=r"(?i)(frozen\s+section|permanent\s+section)",
            category="pathology",
            confidence=0.9,
            extract_fields=["margins", "diagnosis"]
        ),

        # Cardiology patterns
        DiagnosticReportPattern(
            pattern=r"(?i)(ECG|EKG|electrocardiogram)",
            category="cardiology",
            confidence=0.95,
            extract_fields=["rhythm", "rate", "intervals"]
        ),
        DiagnosticReportPattern(
            pattern=r"(?i)(echo(?:cardiogram)?|cardiac\s+ultrasound|TTE|TEE)",
            category="cardiology",
            confidence=0.9,
            extract_fields=["ejection_fraction", "wall_motion", "valves"]
        ),
        DiagnosticReportPattern(
            pattern=r"(?i)(stress\s+test|treadmill|exercise\s+ECG)",
            category="cardiology",
            confidence=0.9,
            extract_fields=["duration", "symptoms", "ecg_changes"]
        )
    ]

    # Status patterns
    STATUS_PATTERNS = {
        "preliminary": r"(?i)(preliminary|pending|initial)",
        "final": r"(?i)(final|complete|confirmed)",
        "amended": r"(?i)(amended|corrected|revised|updated)",
        "cancelled": r"(?i)(cancel(?:l)?ed|void|invalid)"
    }

    # Conclusion/Interpretation patterns
    CONCLUSION_PATTERNS = [
        r"(?i)conclusion:\s*([^.]+(?:\.[^.]+){0,2})",
        r"(?i)impression:\s*([^.]+(?:\.[^.]+){0,2})",
        r"(?i)findings?:\s*([^.]+(?:\.[^.]+){0,2})",
        r"(?i)interpretation:\s*([^.]+(?:\.[^.]+){0,2})",
        r"(?i)diagnosis:\s*([^.]+(?:\.[^.]+){0,2})"
    ]

    # Result interpretation patterns
    INTERPRETATION_PATTERNS = {
        "normal": r"(?i)(normal|within\s+normal\s+limits|unremarkable|negative|WNL)",
        "abnormal": r"(?i)(abnormal|positive|elevated|increased|high)",
        "low": r"(?i)(low|decreased|reduced|deficient)",
        "critical": r"(?i)(critical|panic|urgent|stat)"
    }

    # Common lab test patterns with LOINC mapping
    LAB_TEST_PATTERNS = {
        "cbc": {
            "pattern": r"(?i)(CBC|complete\s+blood\s+count|hemogram)",
            "loinc": "58410-2",
            "components": ["WBC", "RBC", "Hemoglobin", "Hematocrit", "Platelets"]
        },
        "metabolic_panel": {
            "pattern": r"(?i)(BMP|CMP|basic\s+metabolic|comprehensive\s+metabolic)",
            "loinc": "24323-8",
            "components": ["Glucose", "BUN", "Creatinine", "Sodium", "Potassium"]
        },
        "liver_panel": {
            "pattern": r"(?i)(LFT|liver\s+function|hepatic\s+panel)",
            "loinc": "24325-3",
            "components": ["AST", "ALT", "Bilirubin", "Alkaline Phosphatase"]
        },
        "lipid_panel": {
            "pattern": r"(?i)(lipid\s+panel|cholesterol\s+panel)",
            "loinc": "57698-3",
            "components": ["Total Cholesterol", "LDL", "HDL", "Triglycerides"]
        },
        "thyroid_panel": {
            "pattern": r"(?i)(thyroid\s+panel|TFT|thyroid\s+function)",
            "loinc": "55204-3",
            "components": ["TSH", "T3", "T4", "Free T4"]
        }
    }

    def extract_diagnostic_reports(self, clinical_text: str) -> List[Dict[str, Any]]:
        """
        Extract diagnostic report information from clinical text

        Args:
            clinical_text: Clinical narrative text

        Returns:
            List of extracted diagnostic report entities
        """
        reports = []

        # Check each pattern
        for report_pattern in self.REPORT_PATTERNS:
            matches = re.finditer(report_pattern.pattern, clinical_text)
            for match in matches:
                report = self._extract_report_details(
                    clinical_text,
                    match,
                    report_pattern
                )
                if report:
                    reports.append(report)

        # Deduplicate overlapping reports
        reports = self._deduplicate_reports(reports)

        return reports

    def _extract_report_details(self,
                               text: str,
                               match: re.Match,
                               pattern: DiagnosticReportPattern) -> Dict[str, Any]:
        """Extract detailed information about a diagnostic report"""

        # Get context around the match (±100 chars)
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 200)
        context = text[start:end]

        report = {
            "text": match.group(0),
            "category": pattern.category,
            "confidence": pattern.confidence,
            "position": {
                "start": match.start(),
                "end": match.end()
            }
        }

        # Extract status
        status = self._extract_status(context)
        if status:
            report["status"] = status

        # Extract conclusion/interpretation
        conclusion = self._extract_conclusion(context)
        if conclusion:
            report["conclusion"] = conclusion

        # Extract interpretation code
        interpretation = self._extract_interpretation(context)
        if interpretation:
            report["interpretation"] = interpretation

        # Extract specific lab test if applicable
        if pattern.category == "laboratory":
            lab_test = self._identify_lab_test(context)
            if lab_test:
                report["procedure"] = lab_test["name"]
                report["loinc_code"] = lab_test.get("loinc")
                report["components"] = lab_test.get("components", [])

        # Extract numeric values if present
        values = self._extract_numeric_values(context)
        if values:
            report["values"] = values

        # Extract date/time if present
        datetime_str = self._extract_datetime(context)
        if datetime_str:
            report["datetime"] = datetime_str

        return report

    def _extract_status(self, text: str) -> Optional[str]:
        """Extract report status from text"""

        for status, pattern in self.STATUS_PATTERNS.items():
            if re.search(pattern, text):
                return status

        return "final"  # Default to final

    def _extract_conclusion(self, text: str) -> Optional[str]:
        """Extract clinical conclusion from text"""

        for pattern in self.CONCLUSION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                conclusion = match.group(1).strip()
                # Clean up the conclusion
                conclusion = re.sub(r'\s+', ' ', conclusion)
                return conclusion[:500]  # Limit length

        return None

    def _extract_interpretation(self, text: str) -> Optional[str]:
        """Extract interpretation category from text"""

        for interp_type, pattern in self.INTERPRETATION_PATTERNS.items():
            if re.search(pattern, text):
                return interp_type

        return None

    def _identify_lab_test(self, text: str) -> Optional[Dict[str, Any]]:
        """Identify specific lab test type"""

        for test_name, test_info in self.LAB_TEST_PATTERNS.items():
            if re.search(test_info["pattern"], text):
                return {
                    "name": test_name.replace("_", " ").title(),
                    "loinc": test_info.get("loinc"),
                    "components": test_info.get("components", [])
                }

        return None

    def _extract_numeric_values(self, text: str) -> List[Dict[str, Any]]:
        """Extract numeric values with units from text"""

        values = []

        # Pattern for value with unit (e.g., "15.2 g/dL", "140 mg/dL")
        value_pattern = r"(\w+(?:\s+\w+)?)\s*[:=]\s*(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)?"

        matches = re.finditer(value_pattern, text)
        for match in matches:
            parameter = match.group(1).strip()
            value = match.group(2)
            unit = match.group(3) if match.group(3) else ""

            values.append({
                "parameter": parameter,
                "value": float(value) if '.' in value else int(value),
                "unit": unit.strip()
            })

        return values[:20]  # Limit to first 20 values

    def _extract_datetime(self, text: str) -> Optional[str]:
        """Extract date/time from text"""

        # Common date patterns
        date_patterns = [
            r"(\d{1,2}/\d{1,2}/\d{4})",
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})"
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _deduplicate_reports(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or overlapping report detections"""

        if len(reports) <= 1:
            return reports

        # Sort by position
        reports.sort(key=lambda x: x["position"]["start"])

        deduplicated = []
        last_end = -1

        for report in reports:
            # Check if this report overlaps with the previous one
            if report["position"]["start"] >= last_end:
                deduplicated.append(report)
                last_end = report["position"]["end"]
            else:
                # Keep the one with higher confidence
                if report["confidence"] > deduplicated[-1]["confidence"]:
                    deduplicated[-1] = report
                    last_end = report["position"]["end"]

        return deduplicated


# Integration function for NLP pipeline
def extract_diagnostic_reports(clinical_text: str) -> List[Dict[str, Any]]:
    """
    Main function to extract diagnostic reports from clinical text

    Args:
        clinical_text: Clinical narrative text

    Returns:
        List of diagnostic report entities
    """
    extractor = DiagnosticReportExtractor()
    return extractor.extract_diagnostic_reports(clinical_text)