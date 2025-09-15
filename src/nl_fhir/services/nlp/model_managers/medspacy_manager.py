"""
MedSpaCy Clinical Intelligence Management
Handles loading and configuration of MedSpaCy clinical models with enhanced target rules.
"""

import logging
import threading
import time
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    logger.warning("spaCy not available - medspaCy requires spaCy")
    SPACY_AVAILABLE = False

try:
    import medspacy
    from medspacy.ner import TargetRule
    MEDSPACY_AVAILABLE = True
    logger.info("MedSpaCy available for clinical intelligence")
except ImportError:
    logger.warning("MedSpaCy not available - using basic spaCy only")
    MEDSPACY_AVAILABLE = False


class MedSpacyManager:
    """Manages MedSpaCy Clinical Intelligence Engine with enhanced medical rules"""

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialization_status = {}

    def load_medspacy_clinical_engine(self, base_model: str = "en_core_web_sm") -> Optional[Any]:
        """
        Load MedSpaCy Clinical Intelligence Engine with ConText and clinical NER
        This is the core enhancement for Epic 2.5 - replaces basic spaCy with clinical intelligence
        """

        if not MEDSPACY_AVAILABLE or not SPACY_AVAILABLE:
            logger.warning("MedSpaCy or spaCy not available, returning None")
            return None

        with self._lock:
            medspacy_key = f"medspacy_clinical_{base_model}"
            if medspacy_key in self._models:
                return self._models[medspacy_key]

            try:
                logger.info("Loading MedSpaCy Clinical Intelligence Engine")
                start_time = time.time()

                # Load basic MedSpaCy with default clinical components (ConText, target matcher, etc.)
                nlp = medspacy.load()

                # Add our additional clinical target rules to enhance entity recognition
                if "medspacy_target_matcher" in nlp.pipe_names:
                    self._configure_enhanced_clinical_rules(nlp)
                else:
                    logger.warning("MedSpaCy target matcher not found, using basic functionality")

                # Test clinical functionality
                test_doc = nlp("Patient John Doe denies chest pain. Start 500mg amoxicillin twice daily.")
                if not test_doc:
                    raise ValueError("MedSpaCy clinical engine failed validation")

                # Validate clinical context detection is working
                if not hasattr(test_doc, 'ents') or len(test_doc.ents) == 0:
                    logger.warning("MedSpaCy clinical engine loaded but no entities detected in test")

                load_time = time.time() - start_time
                logger.info(f"Successfully loaded MedSpaCy Clinical Engine in {load_time:.2f}s")

                self._models[medspacy_key] = nlp
                self._initialization_status[medspacy_key] = "loaded"

                return nlp

            except Exception as e:
                logger.error(f"Failed to load MedSpaCy Clinical Engine: {e}")
                self._initialization_status[medspacy_key] = "failed"
                return None

    def _configure_enhanced_clinical_rules(self, nlp) -> None:
        """Configure MedSpaCy pipeline with enhanced clinical intelligence components"""

        try:
            # Get the target matcher component
            target_matcher = nlp.get_pipe("medspacy_target_matcher")

            # Define ENHANCED clinical target rules for F1 optimization
            clinical_target_rules = self._get_clinical_target_rules()

            # Add target rules to the matcher
            target_matcher.add(clinical_target_rules)
            logger.info(f"Added {len(clinical_target_rules)} clinical target rules to MedSpaCy")

        except Exception as e:
            logger.error(f"Failed to configure enhanced MedSpaCy rules: {e}")

    def _get_clinical_target_rules(self) -> list:
        """Get comprehensive clinical target rules for enhanced medical entity recognition"""

        return [
            # TIER 1: Common medications with variations (from validation testing)
            TargetRule(literal="amoxicillin", category="MEDICATION"),
            TargetRule(literal="amoxil", category="MEDICATION"),
            TargetRule(literal="amox", category="MEDICATION"),
            TargetRule(literal="ibuprofen", category="MEDICATION"),
            TargetRule(literal="advil", category="MEDICATION"),
            TargetRule(literal="motrin", category="MEDICATION"),
            TargetRule(literal="lisinopril", category="MEDICATION"),
            TargetRule(literal="prinivil", category="MEDICATION"),
            TargetRule(literal="zestril", category="MEDICATION"),
            TargetRule(literal="cephalexin", category="MEDICATION"),  # Essential pediatric antibiotic
            TargetRule(literal="captopril", category="MEDICATION"),   # Essential ACE inhibitor
            TargetRule(literal="enalapril", category="MEDICATION"),   # Essential ACE inhibitor
            TargetRule(literal="ramipril", category="MEDICATION"),    # Essential ACE inhibitor
            TargetRule(literal="metformin", category="MEDICATION"),
            TargetRule(literal="glucophage", category="MEDICATION"),
            TargetRule(literal="albuterol", category="MEDICATION"),
            TargetRule(literal="ventolin", category="MEDICATION"),
            TargetRule(literal="proventil", category="MEDICATION"),
            TargetRule(literal="salbutamol", category="MEDICATION"),
            TargetRule(literal="prednisone", category="MEDICATION"),
            TargetRule(literal="prednisolone", category="MEDICATION"),
            TargetRule(literal="warfarin", category="MEDICATION"),
            TargetRule(literal="coumadin", category="MEDICATION"),
            TargetRule(literal="morphine", category="MEDICATION"),
            TargetRule(literal="morphine sulfate", category="MEDICATION"),
            TargetRule(literal="epinephrine", category="MEDICATION"),
            TargetRule(literal="adrenaline", category="MEDICATION"),

            # TIER 2: Enhanced Pediatric-specific patterns (target 0.472 → 0.65 F1)
            TargetRule(literal="children's ibuprofen", category="MEDICATION"),
            TargetRule(literal="children's tylenol", category="MEDICATION"),
            TargetRule(literal="children's acetaminophen", category="MEDICATION"),
            TargetRule(literal="amoxicillin suspension", category="MEDICATION"),
            TargetRule(literal="liquid amoxicillin", category="MEDICATION"),
            TargetRule(literal="ibuprofen suspension", category="MEDICATION"),
            TargetRule(literal="acetaminophen drops", category="MEDICATION"),
            TargetRule(literal="pediatric", category="SPECIALTY_MODIFIER"),
            TargetRule(literal="pediatric dose", category="DOSAGE_MODIFIER"),
            TargetRule(literal="mg/kg", category="DOSAGE_UNIT"),
            TargetRule(literal="mg per kg", category="DOSAGE_UNIT"),
            TargetRule(literal="per kilogram", category="DOSAGE_UNIT"),
            TargetRule(literal="weight-based", category="DOSAGE_MODIFIER"),
            TargetRule(literal="weight-based dosing", category="DOSAGE_MODIFIER"),
            TargetRule(literal="suspension", category="DOSAGE_FORM"),
            TargetRule(literal="drops", category="DOSAGE_FORM"),
            TargetRule(literal="liquid", category="DOSAGE_FORM"),
            TargetRule(literal="syrup", category="DOSAGE_FORM"),
            TargetRule(literal="give 5ml", category="DOSAGE_INSTRUCTION"),
            TargetRule(literal="administer", category="DOSAGE_INSTRUCTION"),
            TargetRule(literal="250mg/5ml", category="CONCENTRATION"),
            TargetRule(literal="100mg/5ml", category="CONCENTRATION"),
            TargetRule(literal="80mg/0.8ml", category="CONCENTRATION"),

            # TIER 3: Enhanced Emergency Medicine patterns (target 0.667 → 0.75 F1)
            TargetRule(literal="STAT", category="URGENCY"),
            TargetRule(literal="stat", category="URGENCY"),
            TargetRule(literal="emergency", category="URGENCY"),
            TargetRule(literal="urgent", category="URGENCY"),
            TargetRule(literal="emergent", category="URGENCY"),
            TargetRule(literal="immediate", category="URGENCY"),
            TargetRule(literal="code blue", category="URGENCY"),
            TargetRule(literal="trauma", category="URGENCY"),
            TargetRule(literal="acute", category="MODIFIER"),
            TargetRule(literal="severe", category="MODIFIER"),
            TargetRule(literal="critical", category="MODIFIER"),

            # Emergency route extraction (IV/IM/PO) - critical for F1 improvement
            TargetRule(literal="IV push", category="ROUTE"),
            TargetRule(literal="IV bolus", category="ROUTE"),
            TargetRule(literal="IV drip", category="ROUTE"),
            TargetRule(literal="intravenous push", category="ROUTE"),
            TargetRule(literal="IM injection", category="ROUTE"),
            TargetRule(literal="intramuscular", category="ROUTE"),
            TargetRule(literal="sublingual", category="ROUTE"),
            TargetRule(literal="SL", category="ROUTE"),
            TargetRule(literal="subcutaneous", category="ROUTE"),
            TargetRule(literal="SC", category="ROUTE"),
            TargetRule(literal="SQ", category="ROUTE"),
            TargetRule(literal="per os", category="ROUTE"),
            TargetRule(literal="by mouth", category="ROUTE"),
            TargetRule(literal="nebulizer", category="ROUTE"),
            TargetRule(literal="inhaled", category="ROUTE"),
            TargetRule(literal="topical", category="ROUTE"),

            # TIER 4: Enhanced frequency patterns (from ClinicalTrials.gov)
            TargetRule(literal="twice daily", category="FREQUENCY"),
            TargetRule(literal="BID", category="FREQUENCY"),
            TargetRule(literal="b.i.d.", category="FREQUENCY"),
            TargetRule(literal="three times daily", category="FREQUENCY"),
            TargetRule(literal="TID", category="FREQUENCY"),
            TargetRule(literal="t.i.d.", category="FREQUENCY"),
            TargetRule(literal="once daily", category="FREQUENCY"),
            TargetRule(literal="QD", category="FREQUENCY"),
            TargetRule(literal="as needed", category="FREQUENCY"),
            TargetRule(literal="PRN", category="FREQUENCY"),
            TargetRule(literal="p.r.n.", category="FREQUENCY"),
            TargetRule(literal="q8h", category="FREQUENCY"),
            TargetRule(literal="q12h", category="FREQUENCY"),
            TargetRule(literal="q24h", category="FREQUENCY"),
            TargetRule(literal="every 8 hours", category="FREQUENCY"),
            TargetRule(literal="every 12 hours", category="FREQUENCY"),

            # TIER 5: Enhanced condition patterns
            TargetRule(literal="type 2 diabetes", category="CONDITION"),
            TargetRule(literal="T2DM", category="CONDITION"),
            TargetRule(literal="diabetes mellitus", category="CONDITION"),
            TargetRule(literal="hypertension", category="CONDITION"),
            TargetRule(literal="HTN", category="CONDITION"),
            TargetRule(literal="high blood pressure", category="CONDITION"),
            TargetRule(literal="asthma", category="CONDITION"),
            TargetRule(literal="reactive airway disease", category="CONDITION"),
            TargetRule(literal="RAD", category="CONDITION"),
            TargetRule(literal="bacterial infection", category="CONDITION"),
            TargetRule(literal="UTI", category="CONDITION"),
            TargetRule(literal="upper respiratory infection", category="CONDITION"),
            TargetRule(literal="acute otitis media", category="CONDITION"),

            # TIER 6: Dosage and route enhancements
            TargetRule(literal="mg", category="DOSAGE_UNIT"),
            TargetRule(literal="mcg", category="DOSAGE_UNIT"),
            TargetRule(literal="milligrams", category="DOSAGE_UNIT"),
            TargetRule(literal="oral", category="ROUTE"),
            TargetRule(literal="PO", category="ROUTE"),
            TargetRule(literal="IV", category="ROUTE"),
            TargetRule(literal="intravenous", category="ROUTE"),

            # TIER 7: Lab tests and procedures
            TargetRule(literal="CBC", category="LAB_TEST"),
            TargetRule(literal="chest X-ray", category="PROCEDURE"),
            TargetRule(literal="HbA1c", category="LAB_TEST"),
            TargetRule(literal="lipid panel", category="LAB_TEST"),
        ]

    def is_available(self) -> bool:
        """Check if MedSpaCy is available"""
        return MEDSPACY_AVAILABLE and SPACY_AVAILABLE

    def get_model_status(self) -> Dict[str, str]:
        """Get status of all loaded MedSpaCy models"""
        return {k: v for k, v in self._initialization_status.items()
                if k.startswith("medspacy_")}

    def clear_models(self):
        """Clear MedSpaCy model cache to free memory"""
        with self._lock:
            medspacy_keys = [k for k in self._models.keys() if k.startswith("medspacy_")]
            for key in medspacy_keys:
                self._models.pop(key, None)
                self._initialization_status.pop(key, None)
            logger.info("Cleared MedSpaCy model cache")