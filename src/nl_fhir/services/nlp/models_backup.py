"""
NLP Model Management for Transformers and Medical Models
HIPAA Compliant: Secure model loading and caching
Production Ready: Memory optimization and error handling
"""

import logging
import threading
import re
import os
from typing import Optional, Dict, Any, List
import time

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("Transformers not available - using basic NLP")
    TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
    logger.info("spaCy available for enhanced medical NLP")
except ImportError:
    logger.warning("spaCy not available - using regex fallback only")
    SPACY_AVAILABLE = False

try:
    import medspacy
    from medspacy.ner import TargetRule
    MEDSPACY_AVAILABLE = True
    logger.info("MedSpaCy available for clinical intelligence")
except ImportError:
    logger.warning("MedSpaCy not available - using basic spaCy only")
    MEDSPACY_AVAILABLE = False


class NLPModelManager:
    """Manages Transformers and medical NLP models with caching and optimization"""
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialization_status = {}
        
    def load_medical_ner_model(self, model_name: str = "clinical-ai-apollo/Medical-NER") -> Optional[Any]:
        """Load and cache medical NER model with error handling"""
        
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available, using fallback NLP")
            return None
            
        with self._lock:
            if model_name in self._models:
                return self._models[model_name]
                
            try:
                logger.info(f"Loading medical NER model: {model_name}")
                start_time = time.time()
                
                # Load NER pipeline for medical entities
                ner_pipeline = pipeline(
                    "ner", 
                    model=model_name,
                    aggregation_strategy="simple",
                    device=-1  # CPU inference
                )
                
                # Basic validation
                test_result = ner_pipeline("Test medical order: 50mg Prozac daily")
                if not isinstance(test_result, list):
                    raise ValueError(f"Model {model_name} failed basic validation")
                
                load_time = time.time() - start_time
                logger.info(f"Successfully loaded {model_name} in {load_time:.2f}s")
                
                self._models[model_name] = ner_pipeline
                self._initialization_status[model_name] = "loaded"
                
                return ner_pipeline
                
            except Exception as e:
                logger.error(f"Failed to load medical NER model {model_name}: {e}")
                self._initialization_status[model_name] = "failed"
                
                # Fallback to basic regex-based NLP
                logger.info("Using fallback regex-based NLP")
                return self.load_fallback_nlp()
                
    def load_spacy_medical_nlp(self, model_name: str = "en_core_web_sm") -> Optional[Any]:
        """Load spaCy model for enhanced medical NLP"""
        
        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available, falling back to regex")
            return None
            
        with self._lock:
            if f"spacy_{model_name}" in self._models:
                return self._models[f"spacy_{model_name}"]
                
            try:
                logger.info(f"Loading spaCy medical NLP model: {model_name}")
                start_time = time.time()
                
                nlp = spacy.load(model_name)
                
                # Test basic functionality
                test_doc = nlp("Test patient John Doe on 5mg Lisinopril daily")
                if not test_doc:
                    raise ValueError(f"spaCy model {model_name} failed validation")
                
                load_time = time.time() - start_time
                logger.info(f"Successfully loaded spaCy model in {load_time:.2f}s")
                
                self._models[f"spacy_{model_name}"] = nlp
                self._initialization_status[f"spacy_{model_name}"] = "loaded"
                
                return nlp
                
            except Exception as e:
                logger.error(f"Failed to load spaCy model {model_name}: {e}")
                self._initialization_status[f"spacy_{model_name}"] = "failed"
                return None
    
    def load_medspacy_clinical_engine(self, base_model: str = "en_core_web_sm") -> Optional[Any]:
        """
        Load MedSpaCy Clinical Intelligence Engine with ConText and clinical NER
        This is the core enhancement for Epic 2.5 - replaces basic spaCy with clinical intelligence
        """
        
        if not MEDSPACY_AVAILABLE or not SPACY_AVAILABLE:
            logger.warning("MedSpaCy or spaCy not available, falling back to basic spaCy")
            return self.load_spacy_medical_nlp(base_model)
            
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
                    try:
                        # Get existing target matcher and add our clinical rules
                        target_matcher = nlp.get_pipe("medspacy_target_matcher")
                        
                        # Define additional clinical target rules
                        clinical_target_rules = [
                            TargetRule(literal="amoxicillin", category="MEDICATION"),
                            TargetRule(literal="lisinopril", category="MEDICATION"),
                            TargetRule(literal="metformin", category="MEDICATION"),
                            TargetRule(literal="diabetes", category="CONDITION"),
                            TargetRule(literal="hypertension", category="CONDITION"),
                            TargetRule(literal="chest pain", category="CONDITION"),
                            TargetRule(literal="shortness of breath", category="CONDITION"),
                            TargetRule(literal="CBC", category="LAB_TEST"),
                            TargetRule(literal="chest X-ray", category="PROCEDURE"),
                            TargetRule(literal="HbA1c", category="LAB_TEST"),
                            TargetRule(literal="lipid panel", category="LAB_TEST"),
                        ]
                        
                        # Add rules to target matcher
                        target_matcher.add(clinical_target_rules)
                        logger.info(f"Added {len(clinical_target_rules)} clinical target rules to MedSpaCy")
                        
                    except Exception as config_error:
                        logger.warning(f"Failed to configure additional MedSpaCy rules: {config_error}")
                        # Continue with basic MedSpaCy functionality
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
                
                # Fallback to basic spaCy
                logger.info("Falling back to basic spaCy model")
                return self.load_spacy_medical_nlp(base_model)
    
    def _configure_medspacy_pipeline(self, nlp) -> Any:
        """Configure MedSpaCy pipeline with clinical intelligence components"""
        
        try:
            # MedSpaCy 1.0.0 comes pre-configured with basic components
            # We can add additional target rules to enhance medical entity recognition
            
            # Get the target matcher component
            target_matcher = nlp.get_pipe("medspacy_target_matcher")
            
            # Define ENHANCED clinical target rules for F1 optimization
            clinical_target_rules = [
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

                # Emergency medication patterns
                TargetRule(literal="epinephrine", category="MEDICATION"),
                TargetRule(literal="adrenaline", category="MEDICATION"),
                TargetRule(literal="atropine", category="MEDICATION"),
                TargetRule(literal="adenosine", category="MEDICATION"),
                TargetRule(literal="amiodarone", category="MEDICATION"),
                TargetRule(literal="dopamine", category="MEDICATION"),
                TargetRule(literal="norepinephrine", category="MEDICATION"),
                TargetRule(literal="vasopressin", category="MEDICATION"),
                TargetRule(literal="naloxone", category="MEDICATION"),
                TargetRule(literal="narcan", category="MEDICATION"),
                TargetRule(literal="flumazenil", category="MEDICATION"),
                TargetRule(literal="nitroglycerin", category="MEDICATION"),
                TargetRule(literal="nitro", category="MEDICATION"),
                TargetRule(literal="furosemide", category="MEDICATION"),
                TargetRule(literal="lasix", category="MEDICATION"),

                # Emergency conditions
                TargetRule(literal="anaphylaxis", category="CONDITION"),
                TargetRule(literal="cardiac arrest", category="CONDITION"),
                TargetRule(literal="shock", category="CONDITION"),
                TargetRule(literal="myocardial infarction", category="CONDITION"),
                TargetRule(literal="MI", category="CONDITION"),
                TargetRule(literal="stroke", category="CONDITION"),
                TargetRule(literal="CVA", category="CONDITION"),
                TargetRule(literal="respiratory distress", category="CONDITION"),
                TargetRule(literal="seizure", category="CONDITION"),
                TargetRule(literal="status epilepticus", category="CONDITION"),

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

                # TIER 7: Lab tests and procedures (existing)
                TargetRule(literal="CBC", category="LAB_TEST"),
                TargetRule(literal="chest X-ray", category="PROCEDURE"),
                TargetRule(literal="HbA1c", category="LAB_TEST"),
                TargetRule(literal="lipid panel", category="LAB_TEST"),
            ]
            
            # Add target rules to the matcher
            target_matcher.add(clinical_target_rules)
            logger.info(f"Added {len(clinical_target_rules)} clinical target rules to MedSpaCy")
            
            return nlp
            
        except Exception as e:
            logger.error(f"Failed to configure MedSpaCy pipeline: {e}")
            return nlp  # Return basic nlp if MedSpaCy configuration fails
        
    def load_fallback_nlp(self) -> Dict[str, Any]:
        """Enhanced fallback regex-based NLP for medical entity extraction"""
        
        # Common medication names including oncology drugs
        medication_names = r'(?:paclitaxel|fulvestrant|carboplatin|cisplatin|doxorubicin|cyclophosphamide|' \
                          r'metformin|lisinopril|amlodipine|simvastatin|omeprazole|levothyroxine|' \
                          r'sertraline|fluoxetine|prozac|lipitor|aspirin|ibuprofen|acetaminophen|' \
                          r'amoxicillin|azithromycin|ciprofloxacin|prednisone|albuterol|' \
                          r'hydrochlorothiazide|metoprolol|warfarin|furosemide|gabapentin|' \
                          r'trastuzumab|bevacizumab|rituximab|pembrolizumab|nivolumab)'
        
        fallback_nlp = {
            "type": "regex_fallback",
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
            # Patient name extraction
            "patient_pattern": re.compile(r'patient\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', re.IGNORECASE),
            # Enhanced dosage pattern
            "dosage_pattern": re.compile(r'(\d+(?:\.\d+)?)\s*(mg|gram|g|tablet|capsule|ml|mcg|iu|units?)', re.IGNORECASE),
            # Condition extraction
            "condition_pattern": re.compile(
                r'(?:diagnosed?\s+with|has|suffers?\s+from|condition|disease)\s+([^.;,]+(?:cancer|diabetes|hypertension|infection|disease))', 
                re.IGNORECASE
            ),
            # Route of administration
            "route_pattern": re.compile(r'\b(IV|intravenous|oral|po|injection|subcutaneous|topical|inhaled)\b', re.IGNORECASE)
        }
        
        self._models["fallback_nlp"] = fallback_nlp
        self._initialization_status["fallback_nlp"] = "loaded"
        
        return fallback_nlp
        
    def load_sentence_transformer(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Optional[Any]:
        """Load sentence transformer for embeddings"""
        
        if not TRANSFORMERS_AVAILABLE:
            return None
            
        with self._lock:
            if f"embeddings_{model_name}" in self._models:
                return self._models[f"embeddings_{model_name}"]
                
            try:
                logger.info(f"Loading sentence transformer: {model_name}")
                start_time = time.time()
                
                embedder = SentenceTransformer(model_name)
                
                # Test embeddings
                test_embedding = embedder.encode("Test medical text")
                if test_embedding is None or len(test_embedding) == 0:
                    raise ValueError(f"Embeddings model {model_name} failed validation")
                
                load_time = time.time() - start_time
                logger.info(f"Successfully loaded embeddings model in {load_time:.2f}s")
                
                self._models[f"embeddings_{model_name}"] = embedder
                self._initialization_status[f"embeddings_{model_name}"] = "loaded"
                
                return embedder
                
            except Exception as e:
                logger.error(f"Failed to load sentence transformer {model_name}: {e}")
                self._initialization_status[f"embeddings_{model_name}"] = "failed"
                return None
    
    def extract_medical_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract medical entities using 4-tier approach with LLM escalation:
        Tier 1: spaCy → Tier 2: Transformers NER → Tier 3: Regex → Tier 3.5: LLM Escalation
        
        The LLM escalation tier (3.5) is triggered when confidence is below the medical safety 
        threshold (default 85%), providing high-accuracy structured output for critical medical data.
        """
        
        # TIER 1: MedSpaCy Clinical Intelligence Engine (Enhanced for Epic 2.5)
        medspacy_nlp = self.load_medspacy_clinical_engine()  # Loads MedSpaCy with clinical intelligence
        if medspacy_nlp and MEDSPACY_AVAILABLE:
            result = self._extract_with_medspacy_clinical(text, medspacy_nlp)
            if self._is_extraction_sufficient(result, text):
                # Check if confidence meets medical safety threshold
                if not self._should_escalate_to_llm(result, text):
                    logger.info("Tier 1 (MedSpaCy Clinical) successful: sufficient confidence for medical safety")
                    return result
                else:
                    logger.info("Tier 1 (MedSpaCy Clinical) insufficient confidence, continuing to Tier 2")
        else:
            # Fallback to basic spaCy if MedSpaCy unavailable
            spacy_nlp = self.load_spacy_medical_nlp()  # Loads en_core_web_sm
            if spacy_nlp:
                result = self._extract_with_spacy_medical(text, spacy_nlp)
                if self._is_extraction_sufficient(result, text):
                    # Check if confidence meets medical safety threshold
                    if not self._should_escalate_to_llm(result, text):
                        logger.info("Tier 1 (spaCy fallback) successful: sufficient confidence for medical safety")
                        return result
                    else:
                        logger.info("Tier 1 (spaCy fallback) insufficient confidence, continuing to Tier 2")
        
        # TIER 2: Specialized medical NER model (slower, sophisticated medical entity recognition)
        ner_model = self.load_medical_ner_model()  # Loads clinical-ai-apollo/Medical-NER
        if ner_model and not isinstance(ner_model, dict):
            result = self._extract_with_transformers(text, ner_model)
            if self._is_extraction_sufficient(result, text):
                # Check if confidence meets medical safety threshold
                if not self._should_escalate_to_llm(result, text):
                    logger.info("Tier 2 (Transformers) successful: sufficient confidence for medical safety")
                    return result
                else:
                    logger.info("Tier 2 (Transformers) insufficient confidence, continuing to Tier 3")
        
        # TIER 3: Regex fallback patterns (fastest, most basic)
        fallback_nlp = self.load_fallback_nlp()
        result = self._extract_with_regex(text, fallback_nlp)
        
        # TIER 3.5: LLM ESCALATION (triggered by low confidence for medical safety)
        if self._should_escalate_to_llm(result, text):
            logger.info("Tier 3.5: Escalating to LLM for medical safety and accuracy")
            
            # Generate unique request ID for tracking
            import uuid
            request_id = f"escalation-{str(uuid.uuid4())[:8]}"
            
            llm_result = self._extract_with_llm_escalation(text, request_id)
            
            # Validate LLM result has better entity coverage
            llm_entity_count = sum(len(entities) for entities in llm_result.values())
            regex_entity_count = sum(len(entities) for entities in result.values())
            
            if llm_entity_count >= regex_entity_count:
                logger.info(f"LLM escalation successful: {llm_entity_count} entities vs {regex_entity_count} from regex")
                return llm_result
            else:
                logger.warning(f"LLM escalation yielded fewer entities ({llm_entity_count} vs {regex_entity_count}), using regex result")
                return result
        else:
            logger.info("Tier 3 (Regex) sufficient: confidence meets medical safety threshold")
            return result
    
    def _extract_with_medspacy_clinical(self, text: str, nlp) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract medical entities using MedSpaCy Clinical Intelligence Engine
        This method implements the core Epic 2.5 enhancement with clinical context detection
        """
        
        result = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": []
        }
        
        try:
            # Process text with MedSpaCy clinical pipeline
            doc = nlp(text)
            
            # Extract entities with clinical context
            for ent in doc.ents:
                # Get clinical context information
                clinical_context = self._get_clinical_context(ent)
                
                entity_info = {
                    "text": ent.text,
                    "confidence": 0.8,  # Base confidence for MedSpaCy entities
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "method": "medspacy_clinical",
                    "clinical_context": clinical_context
                }
                
                # Adjust confidence based on clinical context
                entity_info["confidence"] = self._adjust_confidence_for_clinical_context(
                    entity_info["confidence"], clinical_context
                )
                
                # Map MedSpaCy entity labels to our categories
                if ent.label_ == "MEDICATION":
                    result["medications"].append(entity_info)
                elif ent.label_ == "CONDITION":
                    result["conditions"].append(entity_info)
                elif ent.label_ == "LAB_TEST":
                    result["lab_tests"].append(entity_info)
                elif ent.label_ == "PROCEDURE":
                    result["procedures"].append(entity_info)
                elif ent.label_ == "VITAL_SIGN":
                    result["procedures"].append(entity_info)  # Classify vital signs as procedures
                elif ent.label_ == "ROUTE":
                    # Routes are captured but not directly mapped to our result structure
                    pass
            
            # Extract additional entities using spaCy's NER for persons
            for ent in doc.ents:
                if ent.label_ in ["PERSON"]:
                    entity_info = {
                        "text": ent.text,
                        "confidence": 0.9,  # High confidence for person entities
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "method": "medspacy_clinical_spacy_ner"
                    }
                    result["patients"].append(entity_info)
            
            # Enhanced pattern-based extraction for dosages and frequencies
            self._extract_dosages_and_frequencies_medspacy(text, result)
            
            logger.info(f"MedSpaCy clinical extraction found {sum(len(entities) for entities in result.values())} entities")
            
            return result
            
        except Exception as e:
            logger.error(f"MedSpaCy clinical extraction failed: {e}")
            # Fallback to basic spaCy extraction
            return self._extract_with_spacy_medical(text, nlp)
    
    def _get_clinical_context(self, entity) -> Dict[str, Any]:
        """Extract clinical context information from MedSpaCy entity"""
        context = {
            "is_negated": False,
            "is_hypothetical": False,
            "is_historical": False,
            "certainty": "certain"
        }
        
        try:
            # Check for clinical context attributes added by ConText component
            if hasattr(entity, 'negation'):
                context["is_negated"] = entity.negation
            if hasattr(entity, 'hypothetical'):
                context["is_hypothetical"] = entity.hypothetical
            if hasattr(entity, 'historical'):
                context["is_historical"] = entity.historical
            if hasattr(entity, 'certainty'):
                context["certainty"] = entity.certainty
                
        except Exception as e:
            logger.warning(f"Failed to extract clinical context: {e}")
            
        return context
    
    def _adjust_confidence_for_clinical_context(self, base_confidence: float, clinical_context: Dict[str, Any]) -> float:
        """Adjust entity confidence based on clinical context"""
        
        adjusted_confidence = base_confidence
        
        # Reduce confidence for negated entities (still important for clinical record)
        if clinical_context.get("is_negated", False):
            adjusted_confidence *= 0.7
            
        # Reduce confidence for hypothetical entities
        if clinical_context.get("is_hypothetical", False):
            adjusted_confidence *= 0.6
            
        # Slightly reduce confidence for historical entities
        if clinical_context.get("is_historical", False):
            adjusted_confidence *= 0.85
            
        # Adjust based on certainty
        certainty = clinical_context.get("certainty", "certain")
        if certainty == "uncertain":
            adjusted_confidence *= 0.7
        elif certainty == "possible":
            adjusted_confidence *= 0.8
            
        return min(adjusted_confidence, 1.0)
    
    def _extract_dosages_and_frequencies_medspacy(self, text: str, result: Dict) -> None:
        """Enhanced dosage and frequency extraction with clinical patterns"""
        
        # Clinical dosage patterns (enhanced for medical accuracy)
        dosage_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*(mg|gram|g|tablet|capsule|ml|mcg|iu|units?|milligrams?|grams?|milliliters?)', 
            re.IGNORECASE
        )
        
        # Clinical frequency patterns with medical abbreviations
        frequency_pattern = re.compile(
            r'(?:daily|twice\s+(?:a\s+)?daily|three\s+times|four\s+times|once|weekly|monthly|'
            r'bid|tid|qid|qhs|prn|q\d+h|every\s+\d+\s+(?:hours?|days?|weeks?)|'
            r'\d+\s*(?:times?|x)\s*(?:per|/)?\s*(?:day|week|month|d|wk))', 
            re.IGNORECASE
        )
        
        # Extract dosages
        for match in dosage_pattern.finditer(text):
            dosage_info = {
                "text": match.group(0),
                "confidence": 0.85,  # High confidence for pattern-based extraction
                "start": match.start(),
                "end": match.end(),
                "method": "medspacy_clinical_pattern"
            }
            result["dosages"].append(dosage_info)
        
        # Extract frequencies
        for match in frequency_pattern.finditer(text):
            frequency_info = {
                "text": match.group(0),
                "confidence": 0.85,  # High confidence for pattern-based extraction
                "start": match.start(),
                "end": match.end(),
                "method": "medspacy_clinical_pattern"
            }
            result["frequencies"].append(frequency_info)

    def _extract_with_transformers(self, text: str, ner_pipeline) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using transformers NER pipeline"""
        try:
            entities = ner_pipeline(text)
            
            result = {
                "medications": [],
                "dosages": [], 
                "frequencies": [],
                "patients": [],
                "conditions": [],
                "procedures": [],
                "lab_tests": []
            }
            
            for entity in entities:
                entity_type = entity.get("entity_group", "").lower()
                entity_text = entity.get("word", "").strip()
                confidence = entity.get("score", 0.0)
                
                # Quality filtering: Skip entities that are clearly noise
                # 1. Confidence-based filtering (medical context-aware thresholds)
                entity_type_lower = entity_type.lower()
                
                # Apply type-specific thresholds (avoid standard threshold override)
                should_skip = False
                
                if "drug" in entity_type_lower or "medication" in entity_type_lower:
                    # Higher threshold for medications (false positives dangerous)
                    should_skip = confidence < 0.6
                elif "diagnostic_procedure" in entity_type_lower:
                    # Lower threshold for diagnostic procedures (false negatives costly) 
                    should_skip = confidence < 0.4
                else:
                    # Standard threshold for other types
                    should_skip = confidence < 0.5
                    
                if should_skip:
                    continue
                    
                # 2. Length-based filtering (medical terms are rarely 1-2 characters)
                if len(entity_text) <= 2:
                    continue
                    
                # 3. Common word filtering (avoid medical terms that are too generic)
                generic_words = {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
                if entity_text.lower() in generic_words:
                    continue
                
                entity_info = {
                    "text": entity_text,
                    "confidence": confidence,
                    "start": entity.get("start", 0),
                    "end": entity.get("end", 0),
                    "method": "transformers_ner"
                }
                
                # Map entity types (enhanced mapping for medical accuracy)
                if "drug" in entity_type or "medication" in entity_type:
                    result["medications"].append(entity_info)
                elif "dosage" in entity_type or "dose" in entity_type:
                    result["dosages"].append(entity_info)
                elif "frequency" in entity_type:
                    result["frequencies"].append(entity_info)
                elif "patient" in entity_type or "person" in entity_type:
                    result["patients"].append(entity_info)
                elif "condition" in entity_type or "disease" in entity_type:
                    result["conditions"].append(entity_info)
                elif "diagnostic_procedure" in entity_type:
                    # Classify diagnostic procedures as lab tests or procedures based on medical context
                    text_lower = entity_text.lower()
                    lab_indicators = {'cbc', 'blood', 'urine', 'glucose', 'cholesterol', 'creatinine', 'troponin', 'hba1c', 'panel'}
                    
                    if any(indicator in text_lower for indicator in lab_indicators):
                        result["lab_tests"].append(entity_info)
                    else:
                        result["procedures"].append(entity_info)
                # Skip unmapped entity types (DETAILED_DESCRIPTION, COREFERENCE, etc.)
                    
            return result
            
        except Exception as e:
            logger.error(f"Transformers extraction failed: {e}")
            return self._extract_with_regex(text, self.load_fallback_nlp())
    
    def _extract_with_spacy_medical(self, text: str, nlp) -> Dict[str, List[Dict[str, Any]]]:
        """Extract medical entities using enhanced spaCy with medical patterns"""
        
        result = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": []
        }
        
        try:
            doc = nlp(text)
            
            # Enhanced medical terminology lists
            medication_terms = {
                "tadalafil", "lisinopril", "metformin", "aspirin", "warfarin",
                "atorvastatin", "amlodipine", "omeprazole", "losartan", "gabapentin"
            }
            
            condition_terms = {
                "dysfunction", "hypertension", "diabetes", "pain", "bleeding",
                "heart failure", "depression", "anxiety", "arthritis", "copd"
            }
            
            procedure_terms = {
                "ekg", "ecg", "troponins", "cbc", "metabolic panel", "x-ray",
                "mri", "ct scan", "ultrasound", "biopsy"
            }
            
            lab_terms = {
                "troponins", "cbc", "comprehensive metabolic panel", "lipid panel",
                "hba1c", "creatinine", "glucose", "cholesterol"
            }
            
            frequency_terms = {
                "daily", "twice daily", "three times", "as needed", "prn",
                "bid", "tid", "qid", "once", "weekly"
            }
            
            # Extract using spaCy's linguistic analysis
            for token in doc:
                token_lower = token.text.lower()
                
                # Medications (look for proper nouns that are medical terms)
                if (token.pos_ == "PROPN" or token.pos_ == "NOUN") and not token.is_stop:
                    if token_lower in medication_terms:
                        result["medications"].append({
                            'text': token.text,
                            'confidence': 0.9,
                            'start': token.idx,
                            'end': token.idx + len(token.text),
                            'method': 'spacy_medical'
                        })
                
                # Dosages (numbers followed by units)
                if token.like_num:
                    # Look for following token that might be a unit
                    if token.i + 1 < len(doc):
                        next_token = doc[token.i + 1]
                        if next_token.text.lower() in ["mg", "gram", "ml", "mcg", "tablet", "capsule"]:
                            dosage_text = f"{token.text}{next_token.text}"
                            result["dosages"].append({
                                'text': dosage_text,
                                'confidence': 0.9,
                                'start': token.idx,
                                'end': next_token.idx + len(next_token.text),
                                'method': 'spacy_medical'
                            })
                
                # Frequencies
                if token_lower in frequency_terms:
                    result["frequencies"].append({
                        'text': token.text,
                        'confidence': 0.8,
                        'start': token.idx,
                        'end': token.idx + len(token.text),
                        'method': 'spacy_medical'
                    })
                
                # Conditions
                if token_lower in condition_terms:
                    result["conditions"].append({
                        'text': token.text,
                        'confidence': 0.8,
                        'start': token.idx,
                        'end': token.idx + len(token.text),
                        'method': 'spacy_medical'
                    })
            
            # Extract multi-word medical terms using noun phrases
            for chunk in doc.noun_chunks:
                chunk_lower = chunk.text.lower()
                
                if chunk_lower in procedure_terms or chunk_lower in lab_terms:
                    category = "procedures" if chunk_lower in procedure_terms else "lab_tests"
                    result[category].append({
                        'text': chunk.text,
                        'confidence': 0.85,
                        'start': chunk.start_char,
                        'end': chunk.end_char,
                        'method': 'spacy_medical_phrase'
                    })
            
            # Extract patient names using NER
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    result["patients"].append({
                        'text': ent.text,
                        'confidence': 0.9,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'method': 'spacy_ner'
                    })
                    
        except Exception as e:
            logger.error(f"spaCy medical extraction failed: {e}")
            
        return result
    
    def _is_extraction_sufficient(self, result: Dict[str, List[Dict[str, Any]]], text: str) -> bool:
        """Check if extraction quality is sufficient to avoid escalation"""
        
        total_entities = sum(len(entities) for entities in result.values())
        
        # Rule 1: Must have at least one entity for clinical text
        if total_entities == 0:
            return False
        
        # Rule 2: For medication-related text, must have BOTH medication AND dosage
        text_lower = text.lower()
        if any(med_word in text_lower for med_word in ["prescribe", "medication", "mg", "daily", "tablet"]):
            has_medication = len(result.get("medications", [])) > 0
            has_dosage = len(result.get("dosages", [])) > 0
            if not (has_medication and has_dosage):
                return False
        
        # Rule 3: Quality threshold - expect reasonable entity count
        words = len(text.split())
        entity_density = total_entities / max(words, 1)
        
        # Should have at least 1 entity per 20 words for clinical text
        if entity_density < 0.05:
            return False
        
        return True
    
    def _should_escalate_to_llm(self, result: Dict[str, List[Dict[str, Any]]], text: str) -> bool:
        """
        Determine if results should be escalated to LLM based on confidence thresholds.
        
        For medical applications, we need high confidence (default 85% threshold).
        This prevents dangerous misinterpretations in clinical settings.
        
        Args:
            result: Dictionary of extracted entities by category
            text: Original text being processed
            
        Returns:
            bool: True if should escalate to LLM for higher accuracy
        """
        
        # Load escalation configuration from environment
        escalation_enabled = os.getenv('LLM_ESCALATION_ENABLED', 'true').lower() == 'true'
        if not escalation_enabled:
            return False
            
        escalation_threshold = float(os.getenv('LLM_ESCALATION_THRESHOLD', '0.85'))
        confidence_check_method = os.getenv('LLM_ESCALATION_CONFIDENCE_CHECK', 'weighted_average')
        min_entities_required = int(os.getenv('LLM_ESCALATION_MIN_ENTITIES', '3'))
        
        # Calculate overall confidence based on chosen method
        total_entities = 0
        total_confidence_sum = 0.0
        confidence_values = []
        
        for category, entities in result.items():
            for entity in entities:
                total_entities += 1
                confidence = entity.get('confidence', 0.0)
                total_confidence_sum += confidence
                confidence_values.append(confidence)
        
        # If no entities found, definitely escalate to LLM
        if total_entities == 0:
            logger.info("Escalating to LLM: No entities found in text")
            return True
        
        # If too few entities for clinical text, escalate
        if total_entities < min_entities_required:
            text_lower = text.lower()
            # Check if this looks like clinical text that should have more entities
            clinical_indicators = ['prescribe', 'medication', 'patient', 'mg', 'daily', 'order', 'diagnosis']
            if any(indicator in text_lower for indicator in clinical_indicators):
                logger.info(f"Escalating to LLM: Only {total_entities} entities found, expected more for clinical text")
                return True
        
        # Force escalation if patient names are mentioned but not extracted (medical safety critical)
        text_lower = text.lower()
        patient_indicators = ['patient', 'mr.', 'mrs.', 'ms.', 'dr.']
        has_patient_mention = any(indicator in text_lower for indicator in patient_indicators)
        has_patient_entities = len(result.get('patients', [])) > 0
        
        if has_patient_mention and not has_patient_entities:
            logger.info("Escalating to LLM: Patient mentioned but no patient entities extracted")
            return True
        
        # Calculate confidence score based on method
        if confidence_check_method == 'weighted_average':
            # Weighted by entity importance (medications and conditions are more critical)
            weighted_sum = 0.0
            weight_sum = 0.0
            
            for category, entities in result.items():
                # Medical safety: Higher weights for critical entity types
                if category in ['medications', 'conditions']:
                    weight = 3.0  # Critical for medical safety
                elif category in ['dosages', 'frequencies']:
                    weight = 2.0  # Important for medication safety
                else:
                    weight = 1.0  # Standard weight
                
                for entity in entities:
                    confidence = entity.get('confidence', 0.0)
                    weighted_sum += confidence * weight
                    weight_sum += weight
            
            overall_confidence = weighted_sum / weight_sum if weight_sum > 0 else 0.0
            
        elif confidence_check_method == 'minimum':
            # Use minimum confidence (most conservative)
            overall_confidence = min(confidence_values) if confidence_values else 0.0
            
        elif confidence_check_method == 'average':
            # Simple average
            overall_confidence = total_confidence_sum / total_entities if total_entities > 0 else 0.0
            
        else:
            # Default to weighted average
            logger.warning(f"Unknown confidence check method: {confidence_check_method}, using weighted_average")
            overall_confidence = total_confidence_sum / total_entities if total_entities > 0 else 0.0
        
        # Decision: escalate if confidence below medical safety threshold
        should_escalate = overall_confidence < escalation_threshold
        
        if should_escalate:
            logger.info(f"Escalating to LLM: Overall confidence {overall_confidence:.3f} below threshold {escalation_threshold}")
        else:
            logger.info(f"Pipeline sufficient: Overall confidence {overall_confidence:.3f} meets threshold {escalation_threshold}")
        
        return should_escalate
    
    def _extract_with_llm_escalation(self, text: str, request_id: str = "llm-escalation") -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract medical entities using LLM escalation with CORRECT parsing methodology.
        
        CRITICAL: This method implements the corrected LLM parsing that properly extracts
        embedded data from structured Pydantic objects. Previous parsing errors have been
        fixed to prevent misinterpretation of LLM performance.
        
        Args:
            text: Clinical text to process
            request_id: Request identifier for logging
            
        Returns:
            Dictionary of extracted entities with proper structure and confidence scores
        """
        
        # Import LLMProcessor here to avoid circular imports
        try:
            from .llm_processor import LLMProcessor
        except ImportError as e:
            logger.error(f"Failed to import LLMProcessor: {e}")
            return self._extract_with_regex(text, self.load_fallback_nlp())
        
        # Initialize LLM processor
        llm_processor = LLMProcessor()
        if not llm_processor.initialized:
            if not llm_processor.initialize():
                logger.error("Failed to initialize LLM processor, falling back to regex")
                return self._extract_with_regex(text, self.load_fallback_nlp())
        
        try:
            # Process with LLM using structured output
            llm_results = llm_processor.process_clinical_text(text, [], request_id)
            structured_output = llm_results.get("structured_output", {})
            
            if not structured_output:
                logger.warning(f"LLM returned empty structured output for request {request_id}")
                return self._extract_with_regex(text, self.load_fallback_nlp())
            
            # CORRECTED PARSING METHODOLOGY:
            # Extract ALL data including embedded fields from LLM structured objects
            extracted_entities = {
                "medications": [],
                "dosages": [],
                "frequencies": [],
                "patients": [],
                "conditions": [],
                "procedures": [],
                "lab_tests": []
            }
            
            # Extract medications AND their embedded dosage/frequency data
            for med in structured_output.get("medications", []):
                if isinstance(med, dict):
                    # Add the medication name
                    med_name = med.get("name", "")
                    if med_name:
                        extracted_entities["medications"].append({
                            "text": med_name,
                            "confidence": 0.9,
                            "start": 0,  # LLM doesn't provide position info
                            "end": 0,
                            "method": "llm_escalation",
                            "source": "llm"
                        })
                    
                    # CRITICAL FIX: Extract embedded dosage
                    dosage = med.get("dosage", "")
                    if dosage:
                        extracted_entities["dosages"].append({
                            "text": str(dosage),
                            "confidence": 0.9,
                            "start": 0,
                            "end": 0,
                            "method": "llm_escalation",
                            "source": "llm_embedded"
                        })
                    
                    # CRITICAL FIX: Extract embedded frequency
                    frequency = med.get("frequency", "")
                    if frequency:
                        extracted_entities["frequencies"].append({
                            "text": str(frequency),
                            "confidence": 0.9,
                            "start": 0,
                            "end": 0,
                            "method": "llm_escalation",
                            "source": "llm_embedded"
                        })
                    
                    # Extract embedded route if available
                    route = med.get("route", "")
                    if route and str(route).strip() and str(route) != "None":
                        # Add route as procedure for FHIR mapping
                        extracted_entities["procedures"].append({
                            "text": f"Administration route: {route}",
                            "confidence": 0.8,
                            "start": 0,
                            "end": 0,
                            "method": "llm_escalation",
                            "source": "llm_embedded"
                        })
            
            # Extract medical conditions
            for condition in structured_output.get("conditions", []):
                if isinstance(condition, dict):
                    condition_name = condition.get("name", "")
                    if condition_name:
                        extracted_entities["conditions"].append({
                            "text": condition_name,
                            "confidence": 0.9,
                            "start": 0,
                            "end": 0,
                            "method": "llm_escalation",
                            "source": "llm"
                        })
            
            # Extract lab tests with proper categorization
            for lab in structured_output.get("lab_tests", []):
                if isinstance(lab, dict):
                    lab_name = lab.get("name", "")
                    if lab_name:
                        extracted_entities["lab_tests"].append({
                            "text": lab_name,
                            "confidence": 0.9,
                            "start": 0,
                            "end": 0,
                            "method": "llm_escalation",
                            "source": "llm"
                        })
            
            # Extract procedures
            for proc in structured_output.get("procedures", []):
                if isinstance(proc, dict):
                    proc_name = proc.get("name", "")
                    if proc_name:
                        extracted_entities["procedures"].append({
                            "text": proc_name,
                            "confidence": 0.9,
                            "start": 0,
                            "end": 0,
                            "method": "llm_escalation",
                            "source": "llm"
                        })
            
            # Extract patients if present
            for patient in structured_output.get("patients", []):
                if isinstance(patient, dict):
                    patient_name = patient.get("name", "")
                    if patient_name:
                        extracted_entities["patients"].append({
                            "text": patient_name,
                            "confidence": 0.9,
                            "start": 0,
                            "end": 0,
                            "method": "llm_escalation",
                            "source": "llm"
                        })
                elif isinstance(patient, str) and patient.strip():
                    extracted_entities["patients"].append({
                        "text": patient.strip(),
                        "confidence": 0.9,
                        "start": 0,
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm"
                    })
            
            # Log successful extraction
            total_extracted = sum(len(entities) for entities in extracted_entities.values())
            logger.info(f"LLM escalation successful: extracted {total_extracted} entities from text")
            
            return extracted_entities
            
        except Exception as e:
            logger.error(f"LLM escalation failed for request {request_id}: {e}")
            # Fallback to regex on LLM failure
            return self._extract_with_regex(text, self.load_fallback_nlp())

    def _extract_with_regex(self, text: str, regex_nlp: Dict) -> Dict[str, List[Dict[str, Any]]]:
        """Enhanced regex-based entity extraction with multiple patterns"""
        
        result = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": []
        }
        
        try:
            # Extract medications using primary pattern
            med_matches = regex_nlp["medication_pattern"].finditer(text)
            for match in med_matches:
                # Safely access groups - the medication name is in group 2
                groups = match.groups()
                if len(groups) >= 2 and groups[1]:  # Group 2 (index 1) is the medication name
                    med_name = groups[1]
                    med_start = match.start(2)
                    med_end = match.end(2)
                else:
                    continue  # Skip if no medication name found
                
                dosage_before = groups[0] if len(groups) > 0 and groups[0] else None
                dosage_after = groups[2] if len(groups) > 2 and groups[2] else None
                
                result["medications"].append({
                    "text": med_name,
                    "confidence": 0.9,
                    "start": med_start,
                    "end": med_end
                })
                
                # Add dosage if found
                if dosage_before:
                    result["dosages"].append({
                        "text": dosage_before,
                        "confidence": 0.9,
                        "start": match.start(1),
                        "end": match.end(1)
                    })
                elif dosage_after:
                    result["dosages"].append({
                        "text": dosage_after,
                        "confidence": 0.9,
                        "start": match.start(3),
                        "end": match.end(3)
                    })
            
            # Try alternative medication pattern
            alt_med_matches = regex_nlp.get("alt_medication_pattern", re.compile("")).finditer(text)
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
                            "end": match.end(1)
                        })
                        result["dosages"].append({
                            "text": dosage_text,
                            "confidence": 0.85,
                            "start": match.start(2),
                            "end": match.end(2)
                        })
            
            # Extract frequencies
            freq_matches = regex_nlp["frequency_pattern"].finditer(text)
            for match in freq_matches:
                result["frequencies"].append({
                    "text": match.group(0),  # Use group 0 since pattern has no capture groups
                    "confidence": 0.8,
                    "start": match.start(),
                    "end": match.end()
                })
            
            # Extract patient names
            patient_matches = regex_nlp["patient_pattern"].finditer(text)
            for match in patient_matches:
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    result["patients"].append({
                        "text": groups[0],
                        "confidence": 0.7,
                        "start": match.start(1),
                        "end": match.end(1)
                    })
                
            # Extract medical conditions
            if "condition_pattern" in regex_nlp:
                condition_matches = regex_nlp["condition_pattern"].finditer(text)
                for match in condition_matches:
                    groups = match.groups()
                    if len(groups) >= 1 and groups[0]:
                        condition_text = groups[0].strip()
                        result["conditions"].append({
                            "text": condition_text,
                            "confidence": 0.8,
                            "start": match.start(1),
                            "end": match.end(1)
                        })
                
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")
            
        return result
    
    def get_model_status(self) -> Dict[str, str]:
        """Get status of all loaded models"""
        return self._initialization_status.copy()
        
    def clear_models(self):
        """Clear model cache to free memory"""
        with self._lock:
            self._models.clear()
            self._initialization_status.clear()
            logger.info("Cleared NLP model cache")
    
    def _calculate_quality_score(self, entities: Dict[str, List[Dict[str, Any]]], text: str) -> float:
        """
        Calculate quality score for extracted entities
        
        Args:
            entities: Dictionary of extracted entities by type
            text: Original input text
            
        Returns:
            float: Quality score between 0.0 and 1.0
        """
        try:
            # Count total entities
            total_entities = sum(len(entity_list) for entity_list in entities.values())
            
            # Base score based on entity count
            if total_entities == 0:
                return 0.0
            
            # Calculate confidence-weighted score
            confidence_scores = []
            medical_entity_count = 0
            
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    confidence = entity.get('confidence', 0.0)
                    confidence_scores.append(confidence)
                    
                    # Weight medical entities more heavily
                    if entity_type in ['medications', 'conditions', 'procedures', 'lab_tests']:
                        medical_entity_count += 1
                        confidence_scores.append(confidence)  # Double weight for medical entities
            
            if not confidence_scores:
                return 0.0
            
            # Average confidence score
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            # Bonus for having medical entities
            medical_bonus = min(0.2, medical_entity_count * 0.05)
            
            # Text length consideration - longer texts might have more entities
            text_length_bonus = min(0.1, len(text.split()) / 100)
            
            # Calculate final score
            quality_score = avg_confidence + medical_bonus + text_length_bonus
            
            # Ensure score is between 0.0 and 1.0
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            logger.warning(f"Error calculating quality score: {e}")
            return 0.5  # Return neutral score on error


# Global model manager instance
model_manager = NLPModelManager()


def get_medical_nlp_model():
    """Get cached medical NLP model"""
    return model_manager.load_medical_ner_model()


def extract_medical_entities(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract medical entities from text"""
    return model_manager.extract_medical_entities(text)


def get_sentence_transformer(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Get cached sentence transformer model"""
    return model_manager.load_sentence_transformer(model_name)