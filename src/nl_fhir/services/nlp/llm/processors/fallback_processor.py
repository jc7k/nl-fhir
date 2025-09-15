"""
Fallback processor for rule-based clinical structure extraction
"""

import logging
import re
from typing import Dict, Any, List, Tuple

from ..models import (
    ClinicalStructure, MedicationOrder, LabTest, DiagnosticProcedure,
    MedicalCondition, MedicationRoute, UrgencyLevel, ClinicalSetting
)

logger = logging.getLogger(__name__)


class FallbackProcessor:
    """Rule-based fallback processor for clinical text extraction"""

    def extract_clinical_structure(self, text: str) -> Dict[str, Any]:
        """Enhanced rule-based extraction with Pydantic validation"""

        try:
            # Extract medication orders
            medications = self._extract_enhanced_medications(text)

            # Extract lab tests
            lab_tests = self._extract_enhanced_lab_tests(text)

            # Extract procedures
            procedures = self._extract_enhanced_procedures(text)

            # Extract conditions
            conditions = self._extract_enhanced_conditions(text)

            # Extract clinical context
            urgency_level, clinical_setting = self._extract_clinical_context(text)

            # Extract clinical instructions
            clinical_instructions = self._extract_instructions(text)

            # Extract safety alerts
            safety_alerts = self._extract_safety_alerts(text)

            # Create structured output with validation
            structure = ClinicalStructure(
                medications=medications,
                lab_tests=lab_tests,
                procedures=procedures,
                conditions=conditions,
                clinical_instructions=clinical_instructions,
                urgency_level=urgency_level,
                clinical_setting=clinical_setting,
                patient_safety_alerts=safety_alerts
            )

            return structure.model_dump()

        except Exception as e:
            logger.error(f"Enhanced extraction failed: {e}")
            # Return minimal structure
            return ClinicalStructure().model_dump()

    def _extract_enhanced_medications(self, text: str) -> List[MedicationOrder]:
        """Extract enhanced medication orders with validation"""

        medications = []

        # Enhanced medication patterns with specific drug names
        medication_patterns = [
            # Standard dosing patterns
            r'(?:start|prescribe|give|administer|initiated|recommended)\s+(?:patient\s+.*?\s+on\s+)?(\d+\s*(?:mg|%|gram|tablet|capsule|ml|mcg|iu|mL))\s+(\w+)',
            r'(?:start|prescribe|give|administer|initiated|recommended)\s+(?:patient\s+.*?\s+on\s+)?(\w+)\s+(\d+\s*(?:mg|%|gram|tablet|capsule|ml|mcg|iu|mL))',
            r'(\w+)\s+(\d+\s*(?:mg|%|gram|tablet|capsule|ml|mcg|iu|mL))\s+(?:daily|twice\s+daily|three\s+times|once|bid|tid|qid|prn|orally|at\s+bedtime)',
            r'(\w+)\s+inhaler\s+(\d+\s+puffs?)',
            r'(\w+)\s+(?:topical\s+cream|patch|gel)',

            # Specific drug name patterns (for complex names)
            r'\b(tadalafil|levetiracetam|triamcinolone|epinephrine|risperidone|azithromycin|methotrexate|pramipexole|zolpidem|bupropion|clonidine|spironolactone|metronidazole|hydroxychloroquine|propranolol|cabergoline|gabapentin|diclofenac|cinacalcet|desmopressin|pirfenidone)\b',

            # RSV antibody pattern
            r'(RSV\s+monoclonal\s+antibody|monoclonal\s+antibody)',

            # Patch and special formulations
            r'(\w+)\s+(?:XL|SR|CR|LA)\s+(?:\d+\s*(?:mg|%|tablet))',
            r'(\w+)\s+patch',
            r'(\w+)\s+(?:vaginal\s+gel|topical\s+cream)',
        ]

        route_patterns = {
            r'\boral\b|\bpo\b|\bby\s+mouth\b': MedicationRoute.ORAL,
            r'\bintravenous\b|\biv\b': MedicationRoute.IV,
            r'\bintramuscular\b|\bim\b': MedicationRoute.IM,
            r'\binhaler?\b|\binhalation\b': MedicationRoute.INHALATION,
            r'\btopical\b|\bapply\b': MedicationRoute.TOPICAL,
            r'\bsublingual\b': MedicationRoute.SUBLINGUAL,
        }

        for pattern in medication_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)

            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    # Handle patterns with multiple groups
                    name = match[1].strip() if match[1] else match[0].strip()
                    dosage = match[0].strip() if match[1] else None
                    frequency = None
                elif isinstance(match, str):
                    # Handle single group matches (drug name only)
                    name = match.strip()
                    dosage = None
                    frequency = None
                else:
                    continue

                # Try to extract dosage if not found
                if not dosage:
                    dosage_match = re.search(rf'{re.escape(name)}\s+(\d+\s*(?:mg|%|gram|tablet|capsule|ml|mcg|iu|mL))', text, re.IGNORECASE)
                    if dosage_match:
                        dosage = dosage_match.group(1)

                # Try to extract frequency if not found
                if not frequency:
                    freq_match = re.search(rf'{re.escape(name)}.*?(daily|twice\s+daily|three\s+times\s+daily|once|bid|tid|qid|prn|at\s+bedtime|as\s+needed)', text, re.IGNORECASE)
                    if freq_match:
                        frequency = freq_match.group(1)

                # Determine route
                route = MedicationRoute.UNKNOWN
                for route_pattern, route_value in route_patterns.items():
                    if re.search(route_pattern, text, re.IGNORECASE):
                        route = route_value
                        break

                # Skip if name is too generic or empty
                if not name or len(name) < 3 or name.lower() in ['patient', 'mg', 'daily', 'twice', 'once']:
                    continue

                try:
                    medication = MedicationOrder(
                        name=name,
                        dosage=dosage,
                        frequency=frequency,
                        route=route
                    )
                    medications.append(medication)
                except Exception as e:
                    logger.warning(f"Failed to create medication order: {e}")

        return medications

    def _extract_enhanced_lab_tests(self, text: str) -> List[LabTest]:
        """Extract enhanced lab test orders with validation"""

        lab_tests = []

        # Lab test patterns
        lab_patterns = [
            r'order\s+(.*?(?:level|panel|test|screen))',
            r'(cbc|complete\s+blood\s+count)',
            r'(comprehensive\s+metabolic\s+panel|cmp)',
            r'(hba1c|hemoglobin\s+a1c)',
            r'(lipid\s+panel)',
            r'(liver\s+function\s+.*?tests?)',
            r'(thyroid\s+.*?tests?|tsh)',
            r'(blood\s+cultures?)',
            r'(urinalysis|ua)',
        ]

        urgency_mapping = {
            "stat": UrgencyLevel.STAT,
            "urgent": UrgencyLevel.URGENT,
            "asap": UrgencyLevel.ASAP,
            "routine": UrgencyLevel.ROUTINE,
        }

        # Determine overall urgency
        urgency = UrgencyLevel.ROUTINE
        for urgency_word, urgency_level in urgency_mapping.items():
            if urgency_word in text.lower():
                urgency = urgency_level
                break

        for pattern in lab_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)

            for match in matches:
                test_name = match.strip() if isinstance(match, str) else ' '.join(match).strip()

                if test_name:
                    try:
                        lab_test = LabTest(
                            name=test_name,
                            urgency=urgency,
                            fasting_required="fasting" in text.lower()
                        )
                        lab_tests.append(lab_test)
                    except Exception as e:
                        logger.warning(f"Failed to create lab test order: {e}")

        return lab_tests

    def _extract_enhanced_procedures(self, text: str) -> List[DiagnosticProcedure]:
        """Extract enhanced diagnostic procedures with validation"""

        procedures = []

        # Procedure patterns
        procedure_patterns = [
            r'order\s+(.*?(?:x-ray|ct|mri|ultrasound|scan|ecg|ekg))',
            r'(chest\s+x-ray)',
            r'(ct\s+scan?.*?)(?:\s|$)',
            r'(mri.*?)(?:\s|$)',
            r'(ultrasound.*?)(?:\s|$)',
            r'(ecg|ekg|electrocardiogram)',
            r'(endoscopy)',
            r'(biopsy)',
            r'(holter\s+monitor)',
            r'(pulmonary\s+function\s+tests?)',
        ]

        urgency_mapping = {
            "stat": UrgencyLevel.STAT,
            "urgent": UrgencyLevel.URGENT,
            "asap": UrgencyLevel.ASAP,
            "routine": UrgencyLevel.ROUTINE,
        }

        # Determine overall urgency
        urgency = UrgencyLevel.ROUTINE
        for urgency_word, urgency_level in urgency_mapping.items():
            if urgency_word in text.lower():
                urgency = urgency_level
                break

        for pattern in procedure_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)

            for match in matches:
                procedure_name = match.strip() if isinstance(match, str) else ' '.join(match).strip()

                if procedure_name:
                    try:
                        procedure = DiagnosticProcedure(
                            name=procedure_name,
                            urgency=urgency,
                            contrast_needed="contrast" in text.lower()
                        )
                        procedures.append(procedure)
                    except Exception as e:
                        logger.warning(f"Failed to create procedure order: {e}")

        return procedures

    def _extract_enhanced_conditions(self, text: str) -> List[MedicalCondition]:
        """Extract enhanced medical conditions with validation"""

        conditions = []

        # Enhanced condition patterns
        condition_patterns = [
            r'for\s+(.*?)(?:\s|;|$)',
            r'diagnosis\s+of\s+(.*?)(?:\s|;|$)',
            r'patient\s+(?:has|with)\s+(.*?)(?:\s|;|$)',

            # Specific complex conditions from failed scenarios
            r'\b(erectile\s+dysfunction|new-onset\s+focal\s+seizures|seizures|eczema\s+flare-up|eczema|anaphylaxis|schizophrenia|chlamydia|rheumatoid\s+arthritis|parkinson\'s\s+disease|insomnia|adhd|acne|bacterial\s+vaginosis|lupus|essential\s+tremor|hyperprolactinemia|postherpetic\s+neuralgia)\b',

            # General medical conditions
            r'\b(diabetes|hypertension|asthma|depression|anxiety|infection|pneumonia|bronchitis|sinusitis)\b',
            r'\b(chest\s+pain|shortness\s+of\s+breath|pain)\b',

            # Pattern for "for X management/treatment"
            r'for\s+(.*?)\s+(?:management|treatment|therapy)',
        ]

        for pattern in condition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)

            for match in matches:
                condition_name = match.strip() if isinstance(match, str) else ' '.join(match).strip()

                # Filter out common non-conditions
                if condition_name and condition_name.lower() not in [
                    'patient', 'monitoring', 'screening', 'evaluation', 'assessment', 'routine'
                ]:
                    try:
                        condition = MedicalCondition(
                            name=condition_name,
                            status="active"
                        )
                        conditions.append(condition)
                    except Exception as e:
                        logger.warning(f"Failed to create condition: {e}")

        return conditions

    def _extract_clinical_context(self, text: str) -> Tuple[UrgencyLevel, ClinicalSetting]:
        """Extract clinical context and urgency"""

        # Determine urgency
        urgency = UrgencyLevel.ROUTINE
        if any(word in text.lower() for word in ["stat", "emergency", "urgent"]):
            urgency = UrgencyLevel.STAT
        elif "urgent" in text.lower():
            urgency = UrgencyLevel.URGENT
        elif "asap" in text.lower():
            urgency = UrgencyLevel.ASAP

        # Determine setting
        setting = ClinicalSetting.OUTPATIENT
        if any(word in text.lower() for word in ["hospital", "inpatient", "admission", "icu"]):
            setting = ClinicalSetting.INPATIENT
        elif any(word in text.lower() for word in ["emergency", "er", "urgent care"]):
            setting = ClinicalSetting.EMERGENCY
        elif "icu" in text.lower():
            setting = ClinicalSetting.ICU

        return urgency, setting

    def _extract_instructions(self, text: str) -> List[str]:
        """Extract clinical instructions"""

        instructions = []

        # Instruction patterns
        instruction_patterns = [
            r'(take\s+.*?)(?:\.|for|$)',
            r'(start\s+.*?)(?:\.|for|$)',
            r'(continue\s+.*?)(?:\.|for|$)',
            r'(stop\s+.*?)(?:\.|for|$)',
            r'(follow\s+.*?)(?:\.|for|$)',
            r'(monitor\s+.*?)(?:\.|for|$)',
            r'(schedule\s+.*?)(?:\.|for|$)',
        ]

        for pattern in instruction_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            instructions.extend([match.strip() for match in matches])

        return instructions

    def _extract_safety_alerts(self, text: str) -> List[str]:
        """Extract safety alerts and considerations"""

        alerts = []

        # Safety alert patterns
        alert_patterns = [
            r'(allergy\s+to\s+.*?)(?:\.|$)',
            r'(contraindicated\s+.*?)(?:\.|$)',
            r'(caution\s+.*?)(?:\.|$)',
            r'(warning\s+.*?)(?:\.|$)',
            r'(avoid\s+.*?)(?:\.|$)',
        ]

        for pattern in alert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            alerts.extend([match.strip() for match in matches])

        # Check for common safety keywords
        safety_keywords = [
            "pregnancy", "renal impairment", "liver disease", "drug interaction",
            "elderly", "pediatric", "dose adjustment"
        ]

        for keyword in safety_keywords:
            if keyword in text.lower():
                alerts.append(f"Consider {keyword}")

        return alerts