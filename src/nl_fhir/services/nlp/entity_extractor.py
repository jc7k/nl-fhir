"""
Medical Entity Extraction Service
HIPAA Compliant: No PHI logging, secure entity processing
Production Ready: Optimized for clinical text processing
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

# Import the proper medical NLP system
from .models import extract_medical_entities

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Medical entity types for FHIR mapping"""
    MEDICATION = "medication"
    DOSAGE = "dosage"
    FREQUENCY = "frequency"
    CONDITION = "condition"
    PROCEDURE = "procedure"
    LAB_TEST = "lab_test"
    PERSON = "person"
    TEMPORAL = "temporal"
    ROUTE = "route"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


@dataclass
class MedicalEntity:
    """Extracted medical entity with metadata"""
    text: str
    entity_type: EntityType
    start_char: int
    end_char: int
    confidence: float
    attributes: Dict[str, Any]
    source: str  # spacy, pattern, rule-based


class MedicalEntityExtractor:
    """Advanced medical entity extraction using multiple techniques"""
    
    def __init__(self):
        self.nlp = None
        self._pattern_rules = self._initialize_pattern_rules()
        self._medication_keywords = self._load_medication_keywords()
        self._lab_test_keywords = self._load_lab_test_keywords()
        
    def initialize(self) -> bool:
        """Initialize NLP model and components"""
        try:
            # Simple fallback NLP for now - will enhance with spaCy when available
            logger.info("Medical entity extractor initialized with rule-based extraction")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize entity extractor: {e}")
            return False
    
    def extract_entities(self, text: str, request_id: Optional[str] = None) -> List[MedicalEntity]:
        """Extract medical entities from clinical text using proper medical NLP"""
        
        start_time = time.time()
        entities = []
        
        try:
            # Use the proper medical NLP system instead of hardcoded patterns
            nlp_results = extract_medical_entities(text)
            
            # Convert results to MedicalEntity objects
            entity_type_mapping = {
                'medications': EntityType.MEDICATION,
                'lab_tests': EntityType.LAB_TEST,
                'procedures': EntityType.PROCEDURE,
                'conditions': EntityType.CONDITION,
                'dosages': EntityType.DOSAGE,
                'frequencies': EntityType.FREQUENCY,
                'routes': EntityType.ROUTE,
                'temporal': EntityType.TEMPORAL,
                'patients': EntityType.PERSON  # Changed from 'persons' to 'patients' to match NLP model output
            }
            
            # Process each entity type from the medical NLP results
            for entity_category, entity_list in nlp_results.items():
                entity_type = entity_type_mapping.get(entity_category, EntityType.UNKNOWN)
                
                for entity_data in entity_list:
                    # Extract entity information
                    text_span = entity_data.get('text', '')
                    confidence = entity_data.get('confidence', 0.8)
                    start_char = entity_data.get('start', 0)
                    end_char = entity_data.get('end', len(text_span))
                    source = entity_data.get('source', 'medical_nlp')
                    
                    # Create MedicalEntity object
                    entity = MedicalEntity(
                        text=text_span,
                        entity_type=entity_type,
                        start_char=start_char,
                        end_char=end_char,
                        confidence=confidence,
                        attributes=entity_data.get('attributes', {}),
                        source=source
                    )
                    entities.append(entity)
            
            # Merge and deduplicate entities using existing logic
            entities = self._merge_overlapping_entities(entities)
            
            # Calculate processing metrics
            processing_time = time.time() - start_time
            
            logger.info(f"[{request_id}] Extracted {len(entities)} entities in {processing_time:.3f}s using medical NLP")
            
            return entities
            
        except Exception as e:
            logger.error(f"[{request_id}] Medical NLP extraction failed, falling back to patterns: {e}")
            
            # Fallback to pattern-based extraction if medical NLP fails
            try:
                # Clean and prepare text
                cleaned_text = self._preprocess_text(text)
                
                # Rule-based pattern extraction as fallback
                pattern_entities = self._extract_pattern_entities(cleaned_text)
                entities.extend(pattern_entities)
                
                # Merge and deduplicate entities
                entities = self._merge_overlapping_entities(entities)
                
                # Calculate processing metrics
                processing_time = time.time() - start_time
                
                logger.info(f"[{request_id}] Fallback extracted {len(entities)} entities in {processing_time:.3f}s")
                
                return entities
                
            except Exception as fallback_error:
                logger.error(f"[{request_id}] Both medical NLP and fallback extraction failed: {fallback_error}")
                return []
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize clinical text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize common medical abbreviations
        text = re.sub(r'\bb\.?i\.?d\.?\b', 'twice daily', text, flags=re.IGNORECASE)
        text = re.sub(r'\bt\.?i\.?d\.?\b', 'three times daily', text, flags=re.IGNORECASE)
        text = re.sub(r'\bq\.?i\.?d\.?\b', 'four times daily', text, flags=re.IGNORECASE)
        text = re.sub(r'\bq\.?d\.?\b', 'once daily', text, flags=re.IGNORECASE)
        text = re.sub(r'\bp\.?r\.?n\.?\b', 'as needed', text, flags=re.IGNORECASE)
        
        return text
    
    def _extract_pattern_entities(self, text: str) -> List[MedicalEntity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for pattern_name, (pattern, entity_type) in self._pattern_rules.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = MedicalEntity(
                    text=match.group(),
                    entity_type=entity_type,
                    start_char=match.start(),
                    end_char=match.end(),
                    confidence=0.7,  # Pattern-based confidence
                    attributes={"pattern": pattern_name},
                    source="pattern"
                )
                entities.append(entity)
                
        return entities
    
    def _extract_keyword_entities(self, text: str) -> List[MedicalEntity]:
        """Extract entities using medical keyword matching"""
        entities = []
        text_lower = text.lower()
        
        # Check medication keywords
        for keyword in self._medication_keywords:
            start = 0
            while True:
                pos = text_lower.find(keyword.lower(), start)
                if pos == -1:
                    break
                    
                # Check word boundaries
                if (pos == 0 or not text[pos-1].isalnum()) and \
                   (pos + len(keyword) == len(text) or not text[pos + len(keyword)].isalnum()):
                    
                    entity = MedicalEntity(
                        text=text[pos:pos+len(keyword)],
                        entity_type=EntityType.MEDICATION,
                        start_char=pos,
                        end_char=pos + len(keyword),
                        confidence=0.6,  # Keyword confidence
                        attributes={"keyword_match": True},
                        source="keyword"
                    )
                    entities.append(entity)
                    
                start = pos + 1
                
        # Check lab test keywords
        for keyword in self._lab_test_keywords:
            start = 0
            while True:
                pos = text_lower.find(keyword.lower(), start)
                if pos == -1:
                    break
                    
                if (pos == 0 or not text[pos-1].isalnum()) and \
                   (pos + len(keyword) == len(text) or not text[pos + len(keyword)].isalnum()):
                    
                    entity = MedicalEntity(
                        text=text[pos:pos+len(keyword)],
                        entity_type=EntityType.LAB_TEST,
                        start_char=pos,
                        end_char=pos + len(keyword),
                        confidence=0.6,
                        attributes={"keyword_match": True},
                        source="keyword"
                    )
                    entities.append(entity)
                    
                start = pos + 1
                
        return entities
    
    def _merge_overlapping_entities(self, entities: List[MedicalEntity]) -> List[MedicalEntity]:
        """Merge overlapping entities, keeping highest confidence"""
        if not entities:
            return []
            
        # Sort by start position
        entities.sort(key=lambda e: e.start_char)
        
        merged = []
        current = entities[0]
        
        for next_entity in entities[1:]:
            # Check for overlap
            if next_entity.start_char < current.end_char:
                # Keep entity with higher confidence
                if next_entity.confidence > current.confidence:
                    current = next_entity
                # If same confidence, prefer longer entity
                elif (next_entity.confidence == current.confidence and 
                      len(next_entity.text) > len(current.text)):
                    current = next_entity
            else:
                merged.append(current)
                current = next_entity
                
        merged.append(current)
        return merged
    
    def _initialize_pattern_rules(self) -> Dict[str, Tuple[str, EntityType]]:
        """Initialize regex patterns for medical entity extraction"""
        return {
            "dosage_with_unit": (
                r'\b\d+(?:\.\d+)?\s*(?:mg|gram|g|tablet|tab|capsule|cap|ml|mcg|iu|units?)\b',
                EntityType.DOSAGE
            ),
            "frequency_daily": (
                r'\b(?:once|twice|three times|2x|3x|1x)\s+(?:daily|per day|a day)\b',
                EntityType.FREQUENCY
            ),
            "frequency_abbreviation": (
                r'\b(?:bid|tid|qid|qhs|prn|q\d+h)\b',
                EntityType.FREQUENCY
            ),
            "route_administration": (
                r'\b(?:oral|po|iv|im|subcutaneous|topical|inhaled|via nasal cannula|nasal cannula|face mask|non-rebreather)\b',
                EntityType.ROUTE
            ),
            "lab_test_order": (
                r'\b(?:order|get|obtain|check)\s+(?:cbc|bmp|cmp|lipid panel|hba1c|glucose|creatinine)\b',
                EntityType.LAB_TEST
            ),
            "temporal_expressions": (
                r'\b(?:today|tomorrow|next week|in \d+ days?|morning|evening|before meals|after meals)\b',
                EntityType.TEMPORAL
            ),
            "oxygen_therapy": (
                r'\b(?:\d+L? oxygen|oxygen therapy|supplemental oxygen|home oxygen)\b',
                EntityType.MEDICATION
            ),
            "medical_equipment": (
                r'\b(?:nasal cannula|face mask|non-rebreather|ventilator|cpap|bipap)\b',
                EntityType.PROCEDURE
            ),
            "workflow_assignment": (
                r'\b(?:assign|delegate|refer|send|forward)\s+(?:to|for)\s+(?:[A-Za-z\s]+(?:team|nurse|doctor|pharmacist|specialist|department))\b',
                EntityType.WORKFLOW
            ),
            "workflow_scheduling": (
                r'\b(?:schedule|book|arrange|plan)\s+(?:follow-up|appointment|consultation|visit|session)\s+(?:with|for)\b',
                EntityType.WORKFLOW
            ),
            "workflow_monitoring": (
                r'\b(?:monitor|track|watch|observe|check)\s+(?:for|progress|status|response|reaction)\b',
                EntityType.WORKFLOW
            ),
            "workflow_review": (
                r'\b(?:review|evaluate|assess|analyze)\s+(?:results|findings|response|progress|status)\b',
                EntityType.WORKFLOW
            ),
            "workflow_coordination": (
                r'\b(?:coordinate|manage|oversee|ensure)\s+(?:with|care|treatment|workflow)\b',
                EntityType.WORKFLOW
            )
        }
    
    def _load_medication_keywords(self) -> List[str]:
        """Load common medication names for keyword matching"""
        return [
            # Common medications
            "metformin", "lisinopril", "amoxicillin", "ibuprofen", "acetaminophen",
            "aspirin", "atorvastatin", "amlodipine", "hydrochlorothiazide", "losartan",
            "gabapentin", "sertraline", "omeprazole", "warfarin", "furosemide",
            "prednisone", "insulin", "albuterol", "levothyroxine", "citalopram",
            # Antibiotics
            "ciprofloxacin", "azithromycin", "clindamycin", "erythromycin", "levofloxacin",
            "moxifloxacin", "cephalexin", "cefuroxime", "ceftriaxone", "penicillin",
            "ampicillin", "vancomycin", "metronidazole", "trimethoprim", "sulfamethoxazole",
            "tetracycline", "minocycline", "doxycycline", "gentamicin", "tobramycin",
            # Pain/Anti-inflammatory
            "naproxen", "celecoxib", "diclofenac", "meloxicam", "ketorolac", "tramadol",
            "morphine", "oxycodone", "hydrocodone", "codeine", "fentanyl",
            # Cardiovascular
            "metoprolol", "propranolol", "carvedilol", "digoxin", "verapamil", "diltiazem",
            "nifedipine", "nitroglycerin", "isosorbide", "clopidogrel", "rivaroxaban",
            # Respiratory medications and gases
            "montelukast", "budesonide", "fluticasone", "salmeterol", "theophylline",
            "oxygen", "albuterol", "ipratropium", "levalbuterol", "tiotropium",
            # Psychiatric
            "fluoxetine", "paroxetine", "venlafaxine", "duloxetine", "escitalopram",
            "lorazepam", "clonazepam", "alprazolam", "diazepam", "quetiapine", "risperidone",
            # Oncology medications
            "paclitaxel", "carboplatin", "cisplatin", "doxorubicin", "cyclophosphamide",
            "trastuzumab", "bevacizumab", "rituximab", "pembrolizumab", "nivolumab",
            "fulvestrant",
            # Hematologic medications
            "hydroxyurea", "hydrochlorothiazide", "folic acid", "deferasirox", "deferoxamine",
            "eltrombopag", "romiplostim", "lenalidomide", "thalidomide", "pomalidomide",
            "imatinib", "dasatinib", "nilotinib", "bosutinib", "ponatinib"
        ]
    
    def _load_lab_test_keywords(self) -> List[str]:
        """Load common lab test names for keyword matching"""
        return [
            "cbc", "complete blood count", "bmp", "basic metabolic panel",
            "cmp", "comprehensive metabolic panel", "lipid panel", "cholesterol",
            "hba1c", "hemoglobin a1c", "glucose", "blood glucose", "creatinine",
            "bun", "electrolytes", "liver function", "thyroid function", "tsh",
            "psa", "urinalysis", "chest x-ray", "ct scan", "mri", "ecg", "ekg"
        ]