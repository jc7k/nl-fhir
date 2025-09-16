"""
Regex-based Medical Entity Extractor
Fallback extraction using regex patterns for medical entities.
"""

import logging
import re
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class RegexExtractor:
    """Enhanced regex-based entity extraction for medical text"""

    def __init__(self):
        self._patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for medical entity extraction"""

        # Common medication names including oncology drugs
        medication_names = r'(?:paclitaxel|fulvestrant|carboplatin|cisplatin|doxorubicin|cyclophosphamide|' \
                          r'metformin|lisinopril|amlodipine|simvastatin|omeprazole|levothyroxine|' \
                          r'sertraline|fluoxetine|prozac|lipitor|aspirin|ibuprofen|acetaminophen|' \
                          r'amoxicillin|azithromycin|ciprofloxacin|prednisone|albuterol|' \
                          r'hydrochlorothiazide|metoprolol|warfarin|furosemide|gabapentin|' \
                          r'trastuzumab|bevacizumab|rituximab|pembrolizumab|nivolumab|' \
                          r'cephalexin|captopril|enalapril|ramipril)'

        # Lab test patterns for comprehensive extraction
        lab_test_names = r'(?:cbc|complete blood count|cmp|comprehensive metabolic panel|' \
                        r'basic metabolic panel|bmp|hba1c|hemoglobin a1c|lipid panel|' \
                        r'glucose|creatinine|bun|blood urea nitrogen|tsh|troponin|' \
                        r'cardiac enzymes|pt|ptt|inr|cea|psa|bnp|d-dimer|esr|crp|' \
                        r'ana|hepatitis|urinalysis|microalbumin|vitamin d|iron|ferritin|' \
                        r'b12|folate|arterial blood gas|abg|cortisol|blood cultures|procalcitonin)'

        return {
            # Multiple patterns to catch different medication formats
            "medication_pattern": re.compile(
                rf'(?:prescribed?|give?n?|administer|start|order|medication)\s+.*?'
                rf'(?:(\d+(?:\.\d+)?\s*(?:mg|gram|g|tablet|capsule|ml|mcg|iu|units?))\s+)?'
                rf'({medication_names})'
                rf'(?:\s+(\d+(?:\.\d+)?\s*(?:mg|gram|g|tablet|capsule|ml|mcg|iu|units?)))?',
                re.IGNORECASE
            ),
            # Alternative pattern for "drug name + dosage" format
            "alt_medication_pattern": re.compile(
                rf'({medication_names})\s+(\d+(?:\.\d+)?\s*(?:mg|gram|g|tablet|capsule|ml|mcg|iu|units?))',
                re.IGNORECASE
            ),
            # Enhanced frequency pattern with medical abbreviations
            "frequency_pattern": re.compile(
                r'(?:daily|twice\s+(?:a\s+)?daily|three\s+times|four\s+times|once|weekly|monthly|'
                r'bid|tid|qid|qhs|prn|q\d+h|every\s+\d+\s+(?:hours?|days?|weeks?)|'
                r'\d+\s*(?:times?|x)\s*(?:per|/)?\s*(?:day|week|month|d|wk))',
                re.IGNORECASE
            ),
            # Patient name extraction - case insensitive with proper name patterns
            # Captures 1-3 words after "patient:" but stops at common medical terms
            "patient_pattern": re.compile(r'patient:?\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,2})(?=\s+(?:needs|requires|and|with|on|for|gets|is|was|\w+ing|in|at|\d|medication|drug|both)|$)', re.IGNORECASE),
            # Enhanced dosage pattern
            "dosage_pattern": re.compile(r'(\d+(?:\.\d+)?)\s*(mg|gram|g|tablet|capsule|ml|mcg|iu|units?)', re.IGNORECASE),
            # Condition extraction
            "condition_pattern": re.compile(
                r'(?:diagnosed?\s+with|has|suffers?\s+from|condition|disease)\s+([^.;,]+(?:cancer|diabetes|hypertension|infection|disease))',
                re.IGNORECASE
            ),
            # Route of administration
            "route_pattern": re.compile(r'\b(IV|intravenous|oral|po|injection|subcutaneous|topical|inhaled)\b', re.IGNORECASE),
            # Weight extraction pattern for pediatric dosing
            "weight_pattern": re.compile(r'(?:weight:\s*)?(\d+(?:\.\d+)?)\s*kg', re.IGNORECASE),
            # Weight-based dosage pattern (mg/kg, mg/kg/day)
            "weight_based_dosage_pattern": re.compile(r'(\d+(?:\.\d+)?)\s*(mg/kg(?:/day)?)', re.IGNORECASE),
            # Lab test extraction pattern
            "lab_test_pattern": re.compile(
                rf'(?:order|obtain|check|draw|send|lab|test)\s+.*?({lab_test_names})',
                re.IGNORECASE
            ),
            # Simple medication name extraction for complex sequences
            "simple_medication_pattern": re.compile(
                rf'({medication_names})\s*(?:[\d\./\smg²]*)?',
                re.IGNORECASE
            )
        }

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract medical entities using regex patterns"""

        result = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": [],
            "weights": []
        }

        try:
            # Extract medications using primary pattern
            self._extract_medications(text, result)

            # Extract medications using simple pattern for complex text
            self._extract_simple_medications(text, result)

            # Extract lab tests
            self._extract_lab_tests(text, result)

            # Extract frequencies
            self._extract_frequencies(text, result)

            # Extract patient names
            self._extract_patients(text, result)

            # Extract medical conditions
            self._extract_conditions(text, result)

            # Extract weights (for pediatric dosing)
            self._extract_weights(text, result)

        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")

        return result

    def _extract_medications(self, text: str, result: Dict) -> None:
        """Extract medications and associated dosages"""

        # Primary medication pattern
        med_matches = self._patterns["medication_pattern"].finditer(text)
        for match in med_matches:
            groups = match.groups()
            if len(groups) >= 2 and groups[1]:  # Group 2 (index 1) is the medication name
                med_name = groups[1]
                med_start = match.start(2)
                med_end = match.end(2)
            else:
                continue

            dosage_before = groups[0] if len(groups) > 0 and groups[0] else None
            dosage_after = groups[2] if len(groups) > 2 and groups[2] else None

            result["medications"].append({
                "text": med_name,
                "confidence": 0.9,
                "start": med_start,
                "end": med_end,
                "method": "regex"
            })

            # Add dosage if found
            if dosage_before:
                result["dosages"].append({
                    "text": dosage_before,
                    "confidence": 0.9,
                    "start": match.start(1),
                    "end": match.end(1),
                    "method": "regex"
                })
            elif dosage_after:
                result["dosages"].append({
                    "text": dosage_after,
                    "confidence": 0.9,
                    "start": match.start(3),
                    "end": match.end(3),
                    "method": "regex"
                })

        # Alternative medication pattern
        alt_med_matches = self._patterns["alt_medication_pattern"].finditer(text)
        for match in alt_med_matches:
            groups = match.groups()
            if len(groups) >= 2 and groups[0] and groups[1]:
                med_text = groups[0]
                dosage_text = groups[1]

                # Check if we already found this medication to avoid duplicates
                if not any(med["text"].lower() == med_text.lower() for med in result["medications"]):
                    result["medications"].append({
                        "text": med_text,
                        "confidence": 0.85,
                        "start": match.start(1),
                        "end": match.end(1),
                        "method": "regex"
                    })
                    result["dosages"].append({
                        "text": dosage_text,
                        "confidence": 0.85,
                        "start": match.start(2),
                        "end": match.end(2),
                        "method": "regex"
                    })

        # Extract weight-based dosages (mg/kg, mg/kg/day)
        weight_dosage_matches = self._patterns["weight_based_dosage_pattern"].finditer(text)
        for match in weight_dosage_matches:
            groups = match.groups()
            if len(groups) >= 2 and groups[0] and groups[1]:
                dosage_value = groups[0]
                dosage_unit = groups[1]
                full_dosage = f"{dosage_value}{dosage_unit}"

                # Add to dosages if not already captured
                if not any(dos["text"].lower() == full_dosage.lower() for dos in result["dosages"]):
                    result["dosages"].append({
                        "text": full_dosage,
                        "confidence": 0.9,
                        "start": match.start(),
                        "end": match.end(),
                        "method": "regex_weight_based"
                    })

    def _extract_frequencies(self, text: str, result: Dict) -> None:
        """Extract frequency patterns"""

        freq_matches = self._patterns["frequency_pattern"].finditer(text)
        for match in freq_matches:
            result["frequencies"].append({
                "text": match.group(0),
                "confidence": 0.8,
                "start": match.start(),
                "end": match.end(),
                "method": "regex"
            })

    def _extract_simple_medications(self, text: str, result: Dict) -> None:
        """Extract medications using simple pattern for complex clinical text"""

        medication_matches = self._patterns["simple_medication_pattern"].finditer(text)
        existing_medications = {med["text"].lower() for med in result["medications"]}

        for match in medication_matches:
            groups = match.groups()
            if len(groups) >= 1 and groups[0]:
                medication_name = groups[0].strip()
                # Avoid duplicates
                if medication_name.lower() not in existing_medications:
                    result["medications"].append({
                        "text": medication_name,
                        "confidence": 0.8,
                        "start": match.start(1),
                        "end": match.end(1),
                        "method": "regex_simple"
                    })
                    existing_medications.add(medication_name.lower())

    def _extract_lab_tests(self, text: str, result: Dict) -> None:
        """Extract lab test orders"""

        lab_matches = self._patterns["lab_test_pattern"].finditer(text)
        for match in lab_matches:
            groups = match.groups()
            if len(groups) >= 1 and groups[0]:
                lab_name = groups[0].strip()
                result["lab_tests"].append({
                    "text": lab_name,
                    "confidence": 0.9,
                    "start": match.start(1),
                    "end": match.end(1),
                    "method": "regex"
                })

    def _extract_patients(self, text: str, result: Dict) -> None:
        """Extract patient names"""

        patient_matches = self._patterns["patient_pattern"].finditer(text)
        for match in patient_matches:
            groups = match.groups()
            if len(groups) >= 1 and groups[0]:
                result["patients"].append({
                    "text": groups[0],
                    "confidence": 0.7,
                    "start": match.start(1),
                    "end": match.end(1),
                    "method": "regex"
                })

    def _extract_conditions(self, text: str, result: Dict) -> None:
        """Extract medical conditions"""

        condition_matches = self._patterns["condition_pattern"].finditer(text)
        for match in condition_matches:
            groups = match.groups()
            if len(groups) >= 1 and groups[0]:
                condition_text = groups[0].strip()
                result["conditions"].append({
                    "text": condition_text,
                    "confidence": 0.8,
                    "start": match.start(1),
                    "end": match.end(1),
                    "method": "regex"
                })

    def _extract_weights(self, text: str, result: Dict) -> None:
        """Extract patient weights for pediatric dosing"""

        weight_matches = self._patterns["weight_pattern"].finditer(text)
        for match in weight_matches:
            groups = match.groups()
            if len(groups) >= 1 and groups[0]:
                weight_value = groups[0]
                weight_text = f"{weight_value}kg"
                result["weights"].append({
                    "text": weight_text,
                    "confidence": 0.9,
                    "start": match.start(),
                    "end": match.end(),
                    "method": "regex"
                })

    def get_pattern_info(self) -> Dict[str, str]:
        """Get information about loaded patterns"""
        return {name: pattern.pattern for name, pattern in self._patterns.items()}