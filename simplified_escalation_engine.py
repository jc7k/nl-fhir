#!/usr/bin/env python3
"""
Simplified Escalation Engine - Phase 2 of 3-Tier Architecture Migration

This system replaces the complex 4-tier escalation with a streamlined 3-tier approach:
- Tier 1: Enhanced MedSpaCy Clinical Intelligence
- Tier 2: Smart Regex Consolidation (completed in Phase 1)
- Tier 3: LLM Medical Safety Escalation (this module)

Design Philosophy:
- Focus on medical safety validation rather than entity extraction
- Streamlined decision logic with clear confidence thresholds
- Fast escalation decisions (target <100ms)
- High-impact safety checks only
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EscalationTrigger(Enum):
    """Types of medical safety triggers that require LLM escalation"""
    HIGH_RISK_MEDICATION = "high_risk_medication"
    DRUG_INTERACTION = "drug_interaction"
    DOSAGE_SAFETY = "dosage_safety"
    INCOMPLETE_EXTRACTION = "incomplete_extraction"
    MEDICAL_COMPLEXITY = "medical_complexity"
    CRITICAL_CONDITION = "critical_condition"

class EscalationPriority(Enum):
    """Priority levels for LLM escalation"""
    IMMEDIATE = "immediate"    # <50ms target - critical safety
    HIGH = "high"             # <100ms target - important safety
    STANDARD = "standard"     # <200ms target - general enhancement

@dataclass
class EscalationDecision:
    """Decision output from escalation engine"""
    should_escalate: bool
    trigger: Optional[EscalationTrigger]
    priority: Optional[EscalationPriority]
    confidence: float
    reasoning: str
    processing_time_ms: float
    safety_flags: List[str]

class SimplifiedEscalationEngine:
    """
    Streamlined Tier 3: LLM Medical Safety Escalation

    Fast, focused safety validation with simplified decision logic.
    Only escalates to LLM when medically necessary.
    """

    def __init__(self):
        self.high_risk_medications = self._load_high_risk_medications()
        self.critical_conditions = self._load_critical_conditions()
        self.dosage_limits = self._load_dosage_safety_limits()
        self.drug_interactions = self._load_drug_interactions()

        # Performance tracking
        self.escalation_stats = {
            "total_decisions": 0,
            "escalations_triggered": 0,
            "avg_decision_time_ms": 0.0,
            "safety_catches": 0
        }

    def _load_high_risk_medications(self) -> Dict[str, Dict]:
        """Load high-risk medication patterns requiring safety validation"""
        return {
            # Narrow therapeutic window medications
            "warfarin": {
                "risk_level": "critical",
                "safety_checks": ["dosage", "interactions", "monitoring"],
                "max_safe_dose": "10mg/day"
            },
            "insulin": {
                "risk_level": "critical",
                "safety_checks": ["dosage", "timing", "patient_type"],
                "requires_units": True
            },
            "digoxin": {
                "risk_level": "critical",
                "safety_checks": ["dosage", "renal_function", "interactions"],
                "max_safe_dose": "0.25mg/day"
            },
            "lithium": {
                "risk_level": "critical",
                "safety_checks": ["dosage", "levels", "renal_function"],
                "requires_monitoring": True
            },

            # High-alert medications
            "chemotherapy": {
                "risk_level": "high",
                "safety_checks": ["protocol", "dosage", "cycle"],
                "keywords": ["methotrexate", "cisplatin", "doxorubicin"]
            },
            "opioids": {
                "risk_level": "high",
                "safety_checks": ["dosage", "respiratory", "addiction_risk"],
                "keywords": ["morphine", "fentanyl", "oxycodone", "hydrocodone"]
            }
        }

    def _load_critical_conditions(self) -> Dict[str, Dict]:
        """Load critical medical conditions requiring immediate attention"""
        return {
            "acute_mi": {
                "keywords": ["heart attack", "myocardial infarction", "stemi", "nstemi"],
                "urgency": "immediate",
                "requires_protocol": True
            },
            "sepsis": {
                "keywords": ["sepsis", "septic shock", "septicemia"],
                "urgency": "immediate",
                "requires_protocol": True
            },
            "stroke": {
                "keywords": ["stroke", "cva", "cerebrovascular accident"],
                "urgency": "immediate",
                "time_critical": True
            },
            "anaphylaxis": {
                "keywords": ["anaphylaxis", "anaphylactic", "severe allergic reaction"],
                "urgency": "immediate",
                "requires_epinephrine": True
            }
        }

    def _load_dosage_safety_limits(self) -> Dict[str, Dict]:
        """Load dosage safety limits for common medications"""
        return {
            "acetaminophen": {
                "max_daily": "4000mg",
                "max_single": "1000mg",
                "warnings": ["hepatotoxicity", "alcohol_interaction"]
            },
            "ibuprofen": {
                "max_daily": "3200mg",
                "max_single": "800mg",
                "warnings": ["gi_bleeding", "renal_impairment"]
            },
            "aspirin": {
                "max_daily": "4000mg",
                "warnings": ["bleeding_risk", "gi_bleeding"]
            }
        }

    def _load_drug_interactions(self) -> Dict[str, List[str]]:
        """Load critical drug interaction patterns"""
        return {
            "warfarin": [
                "aspirin", "ibuprofen", "clarithromycin", "fluconazole",
                "amiodarone", "metronidazole"
            ],
            "digoxin": [
                "quinidine", "verapamil", "amiodarone", "clarithromycin"
            ],
            "lithium": [
                "thiazides", "ace_inhibitors", "nsaids", "metronidazole"
            ]
        }

    def evaluate_escalation_need(
        self,
        text: str,
        tier1_results: Dict,
        tier2_results: Dict,
        request_id: Optional[str] = None
    ) -> EscalationDecision:
        """
        Main escalation decision engine

        Fast evaluation (target <100ms) to determine if LLM escalation needed

        Args:
            text: Original clinical text
            tier1_results: Enhanced MedSpaCy results
            tier2_results: Smart Regex Consolidation results
            request_id: Optional request identifier

        Returns:
            EscalationDecision with recommendation and reasoning
        """

        start_time = time.time()
        self.escalation_stats["total_decisions"] += 1

        if not request_id:
            request_id = f"escalation_{int(time.time())}"

        # Initialize decision components
        safety_flags = []
        escalation_triggers = []
        max_priority = None

        logger.info(f"[{request_id}] Evaluating escalation need - {len(text)} chars")

        # 1. High-Risk Medication Assessment (Priority 1)
        medication_risk = self._assess_medication_risks(
            tier2_results.get("medications", []),
            safety_flags,
            request_id
        )
        if medication_risk:
            escalation_triggers.append(EscalationTrigger.HIGH_RISK_MEDICATION)
            max_priority = EscalationPriority.IMMEDIATE

        # 2. Critical Condition Detection (Priority 1)
        condition_risk = self._assess_critical_conditions(
            text,
            tier2_results.get("conditions", []),
            safety_flags,
            request_id
        )
        if condition_risk:
            escalation_triggers.append(EscalationTrigger.CRITICAL_CONDITION)
            if not max_priority:
                max_priority = EscalationPriority.IMMEDIATE

        # 3. Drug Interaction Screening (Priority 2)
        interaction_risk = self._assess_drug_interactions(
            tier2_results.get("medications", []),
            safety_flags,
            request_id
        )
        if interaction_risk:
            escalation_triggers.append(EscalationTrigger.DRUG_INTERACTION)
            if not max_priority:
                max_priority = EscalationPriority.HIGH

        # 4. Dosage Safety Validation (Priority 2)
        dosage_risk = self._assess_dosage_safety(
            tier2_results.get("medications", []),
            tier2_results.get("dosages", []),
            safety_flags,
            request_id
        )
        if dosage_risk:
            escalation_triggers.append(EscalationTrigger.DOSAGE_SAFETY)
            if not max_priority:
                max_priority = EscalationPriority.HIGH

        # 5. Extraction Completeness Check (Priority 3)
        extraction_completeness = self._assess_extraction_completeness(
            text,
            tier1_results,
            tier2_results,
            safety_flags,
            request_id
        )
        if not extraction_completeness:
            escalation_triggers.append(EscalationTrigger.INCOMPLETE_EXTRACTION)
            if not max_priority:
                max_priority = EscalationPriority.STANDARD

        # 6. Medical Complexity Assessment (Priority 3)
        complexity_level = self._assess_medical_complexity(
            text,
            tier2_results,
            safety_flags,
            request_id
        )
        if complexity_level > 7.0:  # High complexity threshold
            escalation_triggers.append(EscalationTrigger.MEDICAL_COMPLEXITY)
            if not max_priority:
                max_priority = EscalationPriority.STANDARD

        # Calculate decision confidence
        confidence = self._calculate_decision_confidence(
            escalation_triggers,
            safety_flags,
            tier2_results
        )

        # Final escalation decision
        should_escalate = len(escalation_triggers) > 0
        primary_trigger = escalation_triggers[0] if escalation_triggers else None

        # Create reasoning
        reasoning = self._generate_escalation_reasoning(
            should_escalate,
            escalation_triggers,
            safety_flags,
            confidence
        )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        # Update statistics
        if should_escalate:
            self.escalation_stats["escalations_triggered"] += 1
            if safety_flags:
                self.escalation_stats["safety_catches"] += 1

        self.escalation_stats["avg_decision_time_ms"] = (
            (self.escalation_stats["avg_decision_time_ms"] * (self.escalation_stats["total_decisions"] - 1) + processing_time) /
            self.escalation_stats["total_decisions"]
        )

        decision = EscalationDecision(
            should_escalate=should_escalate,
            trigger=primary_trigger,
            priority=max_priority,
            confidence=confidence,
            reasoning=reasoning,
            processing_time_ms=processing_time,
            safety_flags=safety_flags
        )

        logger.info(
            f"[{request_id}] Escalation decision: {should_escalate} "
            f"({processing_time:.1f}ms, confidence: {confidence:.2f})"
        )

        return decision

    def _assess_medication_risks(
        self,
        medications: List[Dict],
        safety_flags: List[str],
        request_id: str
    ) -> bool:
        """Assess if medications contain high-risk compounds requiring escalation"""

        risk_found = False

        for medication in medications:
            med_text = medication.get("text", "").lower()

            # Check against high-risk medication database
            for risk_med, risk_data in self.high_risk_medications.items():
                if risk_med in med_text:
                    risk_level = risk_data.get("risk_level", "unknown")
                    safety_flags.append(f"high_risk_medication:{risk_med}:{risk_level}")
                    risk_found = True
                    logger.warning(f"[{request_id}] High-risk medication detected: {risk_med}")

                # Check keyword patterns
                keywords = risk_data.get("keywords", [])
                for keyword in keywords:
                    if keyword in med_text:
                        safety_flags.append(f"high_risk_keyword:{keyword}")
                        risk_found = True

        return risk_found

    def _assess_critical_conditions(
        self,
        text: str,
        conditions: List[Dict],
        safety_flags: List[str],
        request_id: str
    ) -> bool:
        """Assess if text contains critical medical conditions"""

        text_lower = text.lower()
        critical_found = False

        for condition_type, condition_data in self.critical_conditions.items():
            keywords = condition_data.get("keywords", [])

            for keyword in keywords:
                if keyword in text_lower:
                    urgency = condition_data.get("urgency", "standard")
                    safety_flags.append(f"critical_condition:{condition_type}:{urgency}")
                    critical_found = True
                    logger.warning(f"[{request_id}] Critical condition detected: {condition_type}")

        return critical_found

    def _assess_drug_interactions(
        self,
        medications: List[Dict],
        safety_flags: List[str],
        request_id: str
    ) -> bool:
        """Check for potential drug interactions"""

        if len(medications) < 2:
            return False  # Need at least 2 meds for interaction

        med_names = [med.get("text", "").lower() for med in medications]
        interaction_found = False

        for med_name in med_names:
            if med_name in self.drug_interactions:
                interacting_drugs = self.drug_interactions[med_name]

                for other_med in med_names:
                    if other_med != med_name and other_med in interacting_drugs:
                        safety_flags.append(f"drug_interaction:{med_name}:{other_med}")
                        interaction_found = True
                        logger.warning(f"[{request_id}] Drug interaction: {med_name} + {other_med}")

        return interaction_found

    def _assess_dosage_safety(
        self,
        medications: List[Dict],
        dosages: List[Dict],
        safety_flags: List[str],
        request_id: str
    ) -> bool:
        """Validate dosage safety for common medications"""

        dosage_risk = False

        # Extract dosage values and associate with medications
        for medication in medications:
            med_text = medication.get("text", "").lower()

            if med_text in self.dosage_limits:
                limits = self.dosage_limits[med_text]

                # Look for dosage in the medication attributes or nearby dosages
                dosage_text = medication.get("dosage", "")
                if not dosage_text and dosages:
                    # Use first available dosage as approximation
                    dosage_text = dosages[0].get("text", "")

                if dosage_text:
                    # Basic dosage extraction and validation
                    import re
                    dosage_match = re.search(r'(\d+)\s*mg', dosage_text.lower())
                    if dosage_match:
                        dosage_amount = int(dosage_match.group(1))
                        max_safe = limits.get("max_single", "0mg")
                        max_safe_amount = int(re.search(r'(\d+)', max_safe).group(1)) if re.search(r'(\d+)', max_safe) else 0

                        if dosage_amount > max_safe_amount:
                            safety_flags.append(f"dosage_exceeded:{med_text}:{dosage_amount}mg>{max_safe}")
                            dosage_risk = True
                            logger.warning(f"[{request_id}] Dosage safety concern: {med_text} {dosage_amount}mg")

        return dosage_risk

    def _assess_extraction_completeness(
        self,
        text: str,
        tier1_results: Dict,
        tier2_results: Dict,
        safety_flags: List[str],
        request_id: str
    ) -> bool:
        """Assess if extraction appears complete for medical safety"""

        text_lower = text.lower()

        # Check for obvious medication keywords that might be missed
        medication_keywords = [
            "prescribe", "administer", "give", "start", "begin", "initiate",
            "tablet", "capsule", "injection", "infusion", "dose", "dosage"
        ]

        has_medication_language = any(keyword in text_lower for keyword in medication_keywords)
        extracted_medications = len(tier2_results.get("medications", []))

        if has_medication_language and extracted_medications == 0:
            safety_flags.append("incomplete_extraction:no_medications_found")
            logger.info(f"[{request_id}] Potential incomplete extraction: medication language present but no meds found")
            return False

        # Check for dosage/frequency language without corresponding extractions
        dosage_keywords = ["mg", "ml", "units", "tablets"]
        frequency_keywords = ["daily", "twice", "tid", "bid", "q8h", "prn"]

        has_dosage_language = any(keyword in text_lower for keyword in dosage_keywords)
        has_frequency_language = any(keyword in text_lower for keyword in frequency_keywords)

        extracted_dosages = len(tier2_results.get("dosages", []))
        extracted_frequencies = len(tier2_results.get("frequencies", []))

        if has_dosage_language and extracted_dosages == 0:
            safety_flags.append("incomplete_extraction:dosages_missing")
            return False

        if has_frequency_language and extracted_frequencies == 0:
            safety_flags.append("incomplete_extraction:frequencies_missing")
            return False

        return True

    def _assess_medical_complexity(
        self,
        text: str,
        tier2_results: Dict,
        safety_flags: List[str],
        request_id: str
    ) -> float:
        """Calculate medical complexity score (0-10)"""

        complexity = 0.0

        # Text length complexity
        complexity += min(len(text) / 500, 2.0)

        # Number of medications
        med_count = len(tier2_results.get("medications", []))
        complexity += min(med_count / 3, 2.0)

        # Number of conditions
        condition_count = len(tier2_results.get("conditions", []))
        complexity += min(condition_count / 2, 2.0)

        # Medical terminology density
        medical_terms = ["diagnosis", "treatment", "protocol", "therapy", "procedure"]
        term_count = sum(1 for term in medical_terms if term in text.lower())
        complexity += min(term_count, 2.0)

        # Numeric complexity (dosages, values, ranges)
        import re
        numbers = len(re.findall(r'\d+', text))
        complexity += min(numbers / 5, 2.0)

        return min(complexity, 10.0)

    def _calculate_decision_confidence(
        self,
        triggers: List[EscalationTrigger],
        safety_flags: List[str],
        tier2_results: Dict
    ) -> float:
        """Calculate confidence in escalation decision"""

        if not triggers:
            # No escalation needed - high confidence if extraction looks complete
            total_entities = sum(len(entities) for entities in tier2_results.values() if isinstance(entities, list))
            return min(0.9, 0.5 + (total_entities * 0.1))

        # Escalation recommended - confidence based on trigger types and safety flags
        confidence = 0.5

        # High confidence for safety-critical triggers
        critical_triggers = [
            EscalationTrigger.HIGH_RISK_MEDICATION,
            EscalationTrigger.CRITICAL_CONDITION,
            EscalationTrigger.DRUG_INTERACTION
        ]

        if any(trigger in critical_triggers for trigger in triggers):
            confidence += 0.3

        # Additional confidence for multiple safety flags
        confidence += min(len(safety_flags) * 0.1, 0.2)

        return min(confidence, 0.95)

    def _generate_escalation_reasoning(
        self,
        should_escalate: bool,
        triggers: List[EscalationTrigger],
        safety_flags: List[str],
        confidence: float
    ) -> str:
        """Generate human-readable reasoning for escalation decision"""

        if not should_escalate:
            return f"No escalation needed - medical safety assessment complete (confidence: {confidence:.2f})"

        reasoning_parts = []

        # Categorize triggers
        safety_triggers = []
        quality_triggers = []

        for trigger in triggers:
            if trigger in [EscalationTrigger.HIGH_RISK_MEDICATION, EscalationTrigger.CRITICAL_CONDITION, EscalationTrigger.DRUG_INTERACTION, EscalationTrigger.DOSAGE_SAFETY]:
                safety_triggers.append(trigger.value)
            else:
                quality_triggers.append(trigger.value)

        if safety_triggers:
            reasoning_parts.append(f"Medical safety concerns: {', '.join(safety_triggers)}")

        if quality_triggers:
            reasoning_parts.append(f"Extraction quality concerns: {', '.join(quality_triggers)}")

        if safety_flags:
            flag_summary = len(safety_flags)
            reasoning_parts.append(f"{flag_summary} safety flag(s) identified")

        reasoning = " | ".join(reasoning_parts)
        reasoning += f" | Confidence: {confidence:.2f}"

        return reasoning

    def get_escalation_statistics(self) -> Dict[str, Any]:
        """Get current escalation engine statistics"""

        escalation_rate = (
            self.escalation_stats["escalations_triggered"] /
            max(self.escalation_stats["total_decisions"], 1) * 100
        )

        return {
            "total_decisions": self.escalation_stats["total_decisions"],
            "escalations_triggered": self.escalation_stats["escalations_triggered"],
            "escalation_rate_percent": escalation_rate,
            "avg_decision_time_ms": self.escalation_stats["avg_decision_time_ms"],
            "safety_catches": self.escalation_stats["safety_catches"],
            "performance_target": "100ms average decision time",
            "safety_target": "Zero missed high-risk medications"
        }

def main():
    """Test the Simplified Escalation Engine"""

    print("🚨 SIMPLIFIED ESCALATION ENGINE - Testing")
    print("=" * 55)

    engine = SimplifiedEscalationEngine()

    # Test cases with different escalation scenarios
    test_cases = [
        {
            "name": "High-Risk Medication (Warfarin)",
            "text": "Start warfarin 5mg daily for atrial fibrillation",
            "tier1_results": {"medications": [{"text": "warfarin", "confidence": 0.9}]},
            "tier2_results": {
                "medications": [{"text": "warfarin", "confidence": 0.9}],
                "dosages": [{"text": "5mg", "confidence": 0.8}],
                "frequencies": [{"text": "daily", "confidence": 0.9}],
                "conditions": [{"text": "atrial fibrillation", "confidence": 0.8}]
            }
        },
        {
            "name": "Critical Condition (MI)",
            "text": "Patient presenting with acute myocardial infarction, start aspirin 325mg",
            "tier1_results": {"conditions": [{"text": "myocardial infarction", "confidence": 0.9}]},
            "tier2_results": {
                "medications": [{"text": "aspirin", "confidence": 0.9}],
                "dosages": [{"text": "325mg", "confidence": 0.8}],
                "frequencies": [],
                "conditions": [{"text": "myocardial infarction", "confidence": 0.9}]
            }
        },
        {
            "name": "Simple Medication (Low Risk)",
            "text": "Acetaminophen 650mg for headache",
            "tier1_results": {"medications": [{"text": "acetaminophen", "confidence": 0.8}]},
            "tier2_results": {
                "medications": [{"text": "acetaminophen", "confidence": 0.8}],
                "dosages": [{"text": "650mg", "confidence": 0.9}],
                "frequencies": [],
                "conditions": [{"text": "headache", "confidence": 0.7}]
            }
        },
        {
            "name": "Drug Interaction Risk",
            "text": "Continue warfarin 2mg daily, add aspirin 81mg daily for cardioprotection",
            "tier1_results": {"medications": [{"text": "warfarin", "confidence": 0.9}, {"text": "aspirin", "confidence": 0.8}]},
            "tier2_results": {
                "medications": [
                    {"text": "warfarin", "confidence": 0.9},
                    {"text": "aspirin", "confidence": 0.8}
                ],
                "dosages": [{"text": "2mg", "confidence": 0.8}, {"text": "81mg", "confidence": 0.9}],
                "frequencies": [{"text": "daily", "confidence": 0.9}],
                "conditions": []
            }
        }
    ]

    print(f"Testing {len(test_cases)} escalation scenarios...\n")

    for i, case in enumerate(test_cases, 1):
        print(f"🧪 Test Case {i}: {case['name']}")
        print(f"   Text: {case['text']}")

        decision = engine.evaluate_escalation_need(
            case["text"],
            case["tier1_results"],
            case["tier2_results"],
            f"test_{i}"
        )

        print(f"   🎯 Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATION'}")
        print(f"   ⚡ Processing: {decision.processing_time_ms:.1f}ms")
        print(f"   🎲 Confidence: {decision.confidence:.2f}")

        if decision.should_escalate:
            print(f"   🚨 Trigger: {decision.trigger.value if decision.trigger else 'Unknown'}")
            print(f"   ⏰ Priority: {decision.priority.value if decision.priority else 'Unknown'}")
            if decision.safety_flags:
                print(f"   🛡️  Safety Flags: {len(decision.safety_flags)}")

        print(f"   💭 Reasoning: {decision.reasoning}")
        print()

    # Display engine statistics
    stats = engine.get_escalation_statistics()
    print("📊 Escalation Engine Statistics:")
    print(f"   Total Decisions: {stats['total_decisions']}")
    print(f"   Escalation Rate: {stats['escalation_rate_percent']:.1f}%")
    print(f"   Avg Decision Time: {stats['avg_decision_time_ms']:.1f}ms")
    print(f"   Safety Catches: {stats['safety_catches']}")
    print(f"   Performance Target: {stats['performance_target']}")

if __name__ == "__main__":
    main()