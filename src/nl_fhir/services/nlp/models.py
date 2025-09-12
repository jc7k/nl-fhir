"""
NLP Model Management for Transformers and Medical Models
HIPAA Compliant: Secure model loading and caching
Production Ready: Memory optimization and error handling
"""

import logging
import threading
import re
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import time

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
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
        """Extract medical entities using 3-tier approach: spaCy → Transformers NER → Regex Fallback"""
        
        # TIER 1: Basic spaCy NLP with medical term lists (fast, basic medical awareness)
        spacy_nlp = self.load_spacy_medical_nlp()  # Loads en_core_web_sm
        if spacy_nlp:
            result = self._extract_with_spacy_medical(text, spacy_nlp)
            if self._is_extraction_sufficient(result, text):
                return result
        
        # TIER 2: Specialized medical NER model (slower, sophisticated medical entity recognition)
        ner_model = self.load_medical_ner_model()  # Loads clinical-ai-apollo/Medical-NER
        if ner_model and not isinstance(ner_model, dict):
            result = self._extract_with_transformers(text, ner_model)
            if self._is_extraction_sufficient(result, text):
                return result
        
        # TIER 3: Regex fallback patterns (fastest, most basic, last resort)
        fallback_nlp = self.load_fallback_nlp()
        return self._extract_with_regex(text, fallback_nlp)
    
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