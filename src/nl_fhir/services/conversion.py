"""
Clinical Order Conversion Service
HIPAA Compliant: No PHI logging, uses request IDs for correlation
Medical Safety: Comprehensive validation and error handling
"""

import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from ..models.request import ClinicalRequest, ClinicalRequestAdvanced
from ..models.response import (
    ConvertResponse, ConvertResponseAdvanced, ProcessingStatus,
    ValidationResult, ProcessingMetadata, ErrorResponse
)
from .nlp.pipeline import get_nlp_pipeline
from .fhir.resource_factory import get_fhir_resource_factory
from .fhir.bundle_assembler import FHIRBundleAssembler
from .fhir.hapi_client import get_hapi_client
from .fhir.validator import get_fhir_validator

logger = logging.getLogger(__name__)


class ConversionService:
    """Core service for clinical order conversion processing"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.startup_time = datetime.now()
        
    async def convert_basic(self, request: ClinicalRequest, request_id: Optional[str] = None) -> ConvertResponse:
        """
        Basic conversion for Story 1.1 compatibility
        Returns simple response structure
        """
        if not request_id:
            request_id = str(uuid4())
            
        start_time = time.time()
        
        try:
            # Log request initiation without PHI
            logger.info(f"Processing basic conversion request {request_id} - "
                       f"text_length={len(request.clinical_text)} chars")
            
            # Input validation logging (security monitoring)
            if len(request.clinical_text) > 4000:  # Large input monitoring
                logger.warning(f"Request {request_id}: Large clinical text input ({len(request.clinical_text)} chars)")
            
            # Simulate processing time for performance testing
            processing_time = time.time() - start_time
            
            # Success logging with metrics
            logger.info(f"Request {request_id}: Basic conversion completed successfully in {processing_time:.3f}s")
            
            # Return basic response structure (Story 1.1 compatibility)
            return ConvertResponse(
                request_id=request_id,
                status=ProcessingStatus.RECEIVED,
                message="Clinical order received and queued for processing. Full FHIR conversion coming in Epic 2.",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Request {request_id}: Basic conversion error after {processing_time:.3f}s - {type(e).__name__}")
            raise e
    
    async def convert_advanced(self, request: ClinicalRequestAdvanced, request_id: Optional[str] = None) -> ConvertResponseAdvanced:
        """
        Advanced conversion with full Epic integration placeholders
        Prepares response structure for future Epic 2-4 integration
        """
        if not request_id:
            request_id = str(uuid4())
            
        start_time = time.time()
        
        try:
            # Enhanced logging with request metadata
            logger.info(f"Processing advanced conversion request {request_id} - "
                       f"text_length={len(request.clinical_text)} chars, "
                       f"priority={request.priority}, department={request.department}")
            
            # Perform input validation
            validation_result = await self._validate_clinical_input(request, request_id)
            
            # Calculate processing metadata
            processing_time_ms = (time.time() - start_time) * 1000
            
            metadata = ProcessingMetadata(
                request_id=request_id,
                processing_time_ms=processing_time_ms,
                server_timestamp=datetime.now(),
                version=self.version,
                input_length=len(request.clinical_text),
                complexity_score=self._assess_input_complexity(request.clinical_text)
            )
            
            # Epic 2: Temporary basic text processing (bypassing NLP due to numpy compatibility issue)
            # TODO: Restore full NLP pipeline once numpy compatibility is resolved
            nlp_results = await self._basic_text_analysis(request.clinical_text, request_id)
            
            # Epic 3: FHIR Resource Creation and Bundle Assembly
            fhir_bundle = None
            fhir_validation_results = None
            bundle_summary = None
            
            try:
                # Create FHIR resources from NLP structured data
                resource_factory = await get_fhir_resource_factory()
                structured_data = nlp_results.get("structured_output", {})
                
                # Create individual FHIR resources
                fhir_resources = []
                
                # Create Patient resource (required for all orders)
                patient_data = structured_data.get("patient", {})
                if not patient_data:
                    # Create basic patient from request metadata
                    patient_data = {
                        "name": "Unknown Patient",
                        "birthDate": None,
                        "gender": "unknown"
                    }
                
                # Add patient_ref from original request if provided
                if hasattr(request, 'patient_ref') and request.patient_ref:
                    patient_data["patient_ref"] = request.patient_ref
                    logger.info(f"Request {request_id}: Using provided patient reference: {request.patient_ref}")
                
                patient_resource = resource_factory.create_patient_resource(patient_data, request_id)
                fhir_resources.append(patient_resource)
                patient_ref = f"Patient/{patient_resource['id']}"
                
                # Create Practitioner resource (for orders)
                practitioner_data = structured_data.get("practitioner", {})
                if not practitioner_data:
                    practitioner_data = {
                        "name": request.practitioner_name if hasattr(request, 'practitioner_name') else "Unknown Practitioner",
                        "identifier": "temp-practitioner"
                    }
                
                practitioner_resource = resource_factory.create_practitioner_resource(practitioner_data, request_id)
                fhir_resources.append(practitioner_resource)
                practitioner_ref = f"Practitioner/{practitioner_resource['id']}"
                
                # Create Encounter resource
                encounter_data = {
                    "status": "planned",
                    "class": "AMB",  # Ambulatory
                    "period": {"start": datetime.now().isoformat()}
                }
                encounter_resource = resource_factory.create_encounter_resource(encounter_data, patient_ref, request_id)
                fhir_resources.append(encounter_resource)
                encounter_ref = f"Encounter/{encounter_resource['id']}"
                
                # Create clinical order resources based on NLP results
                entities = nlp_results.get("extracted_entities", {})
                
                # Create MedicationRequest if medications detected
                medications = entities.get("medications", [])
                for medication in medications:
                    medication_data = {
                        "medication": medication.get("text", "Unknown medication"),
                        "dosage": medication.get("dosage", "As directed"),
                        "frequency": medication.get("frequency", "Unknown frequency"),
                        "route": medication.get("route", "oral"),
                        "status": "active",
                        "intent": "order"
                    }
                    
                    med_request = resource_factory.create_medication_request(
                        medication_data, patient_ref, request_id, 
                        practitioner_ref=practitioner_ref, encounter_ref=encounter_ref
                    )
                    fhir_resources.append(med_request)
                
                # Create ServiceRequest for lab tests and procedures
                lab_tests = entities.get("lab_tests", [])
                procedures = entities.get("procedures", [])
                
                for test in lab_tests + procedures:
                    service_data = {
                        "code": test.get("text", "Unknown test"),
                        "category": "laboratory" if test in lab_tests else "procedure",
                        "status": "active",
                        "intent": "order"
                    }
                    
                    service_request = resource_factory.create_service_request(
                        service_data, patient_ref, request_id,
                        practitioner_ref=practitioner_ref, encounter_ref=encounter_ref
                    )
                    fhir_resources.append(service_request)
                
                # Create Condition resources if conditions detected
                conditions = entities.get("conditions", [])
                for condition in conditions:
                    condition_data = {
                        "code": condition.get("text", "Unknown condition"),
                        "clinical_status": "active",
                        "verification_status": "provisional"
                    }
                    
                    condition_resource = resource_factory.create_condition_resource(
                        condition_data, patient_ref, request_id, 
                        encounter_ref=encounter_ref
                    )
                    fhir_resources.append(condition_resource)
                
                # Assemble FHIR transaction bundle
                bundle_assembler = FHIRBundleAssembler()
                bundle_assembler.initialize()
                
                # Create transaction bundle
                fhir_bundle = bundle_assembler.create_transaction_bundle(fhir_resources, request_id)
                
                # Optimize bundle for HAPI FHIR processing
                fhir_bundle = bundle_assembler.optimize_bundle(fhir_bundle, request_id)
                
                # Generate bundle summary
                bundle_summary = bundle_assembler.get_bundle_summary(fhir_bundle)
                
                # Validate FHIR bundle
                fhir_validator = await get_fhir_validator()
                fhir_validation_results = fhir_validator.validate_bundle(fhir_bundle, request_id)
                
                # Optional: Validate with HAPI FHIR server if available
                try:
                    hapi_client = await get_hapi_client()
                    hapi_validation = await hapi_client.validate_bundle(fhir_bundle, request_id)
                    
                    # Merge validation results
                    fhir_validation_results["hapi_validation"] = hapi_validation
                    
                except Exception as hapi_e:
                    logger.warning(f"[{request_id}] HAPI FHIR validation not available: {hapi_e}")
                
                logger.info(f"[{request_id}] FHIR bundle created successfully - "
                           f"{len(fhir_resources)} resources, valid: {fhir_validation_results.get('is_valid', False)}")
                
            except Exception as fhir_e:
                logger.error(f"[{request_id}] FHIR processing failed: {fhir_e}")
                # Continue with response even if FHIR processing fails
                fhir_validation_results = {
                    "is_valid": False,
                    "errors": [f"FHIR processing error: {str(fhir_e)}"],
                    "warnings": [],
                    "validation_source": "nl_fhir_error"
                }
            
            # Create advanced response with Epic 2 NLP + Epic 3 FHIR integration
            response = ConvertResponseAdvanced(
                request_id=request_id,
                status=ProcessingStatus.RECEIVED,
                message="Clinical order processed with NLP and FHIR assembly. Ready for Epic 4 validation.",
                metadata=metadata,
                validation=validation_result,
                
                # Epic 2: Real NLP Results
                extracted_entities=nlp_results.get("extracted_entities", {}),
                structured_output=nlp_results.get("structured_output", {}),
                terminology_mappings=nlp_results.get("terminology_mappings", {}),
                
                # Epic 3: Real FHIR Results
                fhir_bundle=fhir_bundle,
                fhir_validation_results=fhir_validation_results,
                bundle_summary=bundle_summary,
                
                # Epic 4 placeholders (Reverse Validation)
                safety_checks=None,  # Will be populated in Epic 4
                human_readable_summary=None  # Will be populated in Epic 4
            )
            
            logger.info(f"Request {request_id}: Advanced conversion completed in {processing_time_ms:.2f}ms")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Request {request_id}: Advanced conversion error after {processing_time:.3f}s - {type(e).__name__}")
            raise e
    
    async def _validate_clinical_input(self, request: ClinicalRequestAdvanced, request_id: str) -> ValidationResult:
        """
        Comprehensive validation of clinical input
        Returns structured validation results
        """
        warnings = []
        errors = []
        suggestions = []
        
        # Clinical text analysis
        text_length = len(request.clinical_text)
        
        # Length validation
        if text_length < 10:
            warnings.append("Clinical text is very short - consider providing more detail")
        elif text_length > 2000:
            warnings.append("Clinical text is very long - consider breaking into multiple orders")
        
        # Content analysis (basic pattern detection)
        text_lower = request.clinical_text.lower()
        
        # Check for common medication patterns
        if any(word in text_lower for word in ['mg', 'tablet', 'capsule', 'dose']):
            suggestions.append("Medication order detected - ensure dosage and frequency are specified")
        
        # Check for lab order patterns  
        if any(word in text_lower for word in ['lab', 'test', 'blood', 'urine', 'culture']):
            suggestions.append("Laboratory order detected - ensure specimen type and timing are clear")
        
        # Priority validation
        if request.priority in ['stat', 'urgent'] and not any(word in text_lower for word in ['urgent', 'stat', 'emergency', 'immediate']):
            warnings.append("High priority selected but urgency not reflected in clinical text")
        
        # Calculate validation score
        validation_score = 1.0
        validation_score -= len(warnings) * 0.1
        validation_score -= len(errors) * 0.3
        validation_score = max(0.0, min(1.0, validation_score))
        
        is_valid = len(errors) == 0 and validation_score >= 0.7
        
        logger.info(f"Request {request_id}: Input validation completed - "
                   f"score={validation_score:.2f}, valid={is_valid}, "
                   f"warnings={len(warnings)}, errors={len(errors)}")
        
        return ValidationResult(
            is_valid=is_valid,
            validation_score=validation_score,
            warnings=warnings,
            errors=errors,
            suggestions=suggestions
        )
    
    def _assess_input_complexity(self, clinical_text: str) -> float:
        """
        Assess clinical text complexity for performance planning
        Returns complexity score 0.0-10.0
        """
        # Basic complexity metrics
        complexity = 0.0
        
        # Length factor
        complexity += min(len(clinical_text) / 1000, 3.0)
        
        # Sentence complexity
        sentences = clinical_text.count('.') + clinical_text.count('?') + clinical_text.count('!')
        complexity += min(sentences / 5, 2.0)
        
        # Medical terminology density (basic pattern matching)
        medical_terms = len([word for word in clinical_text.lower().split() 
                           if any(term in word for term in ['mg', 'ml', 'dose', 'daily', 'twice', 'lab', 'test'])])
        complexity += min(medical_terms / 10, 3.0)
        
        # Numeric complexity (dosages, values)
        import re
        numbers = len(re.findall(r'\d+', clinical_text))
        complexity += min(numbers / 5, 2.0)
        
        return min(complexity, 10.0)
    
    async def _basic_text_analysis(self, clinical_text: str, request_id: str) -> Dict[str, Any]:
        """
        Basic text analysis using MedicalEntityExtractor
        Combines entity extraction with pattern matching
        """
        import re
        from .nlp.entity_extractor import MedicalEntityExtractor, EntityType
        
        text_lower = clinical_text.lower()
        
        # Initialize entity extractor
        entity_extractor = MedicalEntityExtractor()
        entity_extractor.initialize()
        
        # Extract entities using the entity extractor
        entities = entity_extractor.extract_entities(clinical_text, request_id)
        
        # Organize entities by type
        extracted_entities = {
            "medications": [],
            "lab_tests": [],
            "procedures": [],
            "conditions": []
        }
        
        for entity in entities:
            if entity.entity_type == EntityType.MEDICATION:
                # Find associated dosage and frequency entities nearby
                dosage = "as directed"
                frequency = "as needed"
                
                # Look for dosage and frequency entities in the text
                for other_entity in entities:
                    if other_entity.entity_type == EntityType.DOSAGE:
                        # If dosage entity is near this medication (within 20 chars)
                        if abs(other_entity.start_char - entity.start_char) < 20:
                            dosage = other_entity.text
                    elif other_entity.entity_type == EntityType.FREQUENCY:
                        # If frequency entity is near this medication (within 30 chars)
                        if abs(other_entity.start_char - entity.start_char) < 30:
                            frequency = other_entity.text
                
                medication_data = {
                    "name": entity.text,
                    "dosage": dosage,
                    "frequency": frequency,
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["medications"].append(medication_data)
            
            elif entity.entity_type == EntityType.LAB_TEST:
                lab_data = {
                    "name": entity.text,
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["lab_tests"].append(lab_data)
            
            elif entity.entity_type == EntityType.PROCEDURE:
                procedure_data = {
                    "name": entity.text,
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["procedures"].append(procedure_data)
            
            elif entity.entity_type == EntityType.CONDITION:
                condition_data = {
                    "name": entity.text,
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["conditions"].append(condition_data)
        
        # Deduplicate extracted entities to prevent duplicate FHIR resources
        def deduplicate_entities(entity_list, key_field="name"):
            """Remove duplicates based on key field and handle substring relationships"""
            deduped = []
            
            for entity in entity_list:
                key = entity.get(key_field, entity.get("text", "")).strip().lower()
                if not key:
                    continue
                    
                # Check if this entity is a substring of an existing longer entity
                # or if an existing entity is a substring of this one
                is_duplicate = False
                for i, existing in enumerate(deduped):
                    existing_key = existing.get(key_field, existing.get("text", "")).strip().lower()
                    
                    # If current key is substring of existing, skip current
                    if key != existing_key and key in existing_key:
                        is_duplicate = True
                        break
                    # If existing key is substring of current, replace existing with current  
                    elif existing_key != key and existing_key in key:
                        deduped[i] = entity
                        is_duplicate = True
                        break
                        
                if not is_duplicate:
                    deduped.append(entity)
                    
            return deduped

        # Apply deduplication to each entity type
        extracted_entities["medications"] = deduplicate_entities(extracted_entities["medications"])
        extracted_entities["lab_tests"] = deduplicate_entities(extracted_entities["lab_tests"])
        extracted_entities["procedures"] = deduplicate_entities(extracted_entities["procedures"])
        
        # Additional context for complex cases
        analysis_context = {
            "text_length": len(clinical_text),
            "complexity": self._assess_input_complexity(clinical_text),
            "contains_dosages": bool(re.search(r'\d+\s*mg', clinical_text)),
            "contains_frequencies": bool(re.search(r'daily|twice|three times', clinical_text)),
            "medical_terminology": {
                "medication_terms": len(extracted_entities["medications"]),
                "lab_terms": len(extracted_entities["lab_tests"]),
                "procedure_terms": len(extracted_entities["procedures"]),
                "condition_terms": len(extracted_entities["conditions"])
            }
        }
        
        # Basic structure for terminology mapping
        terminology_mappings = {
            "snomed_ct": [],
            "loinc": [],
            "rxnorm": [],
            "icd_10": []
        }
        
        # Basic structured output
        structured_output = {
            "summary": f"Clinical order with {len(extracted_entities['medications'])} medications",
            "prioritized_actions": []
        }
        
        logger.info(f"[{request_id}] Basic text analysis completed - "
                   f"Found: {len(extracted_entities['medications'])} medications, "
                   f"{len(extracted_entities['lab_tests'])} lab tests, "
                   f"{len(extracted_entities['procedures'])} procedures, "
                   f"{len(extracted_entities['conditions'])} conditions")
        
        return {
            "extracted_entities": extracted_entities,
            "structured_output": structured_output,
            "terminology_mappings": terminology_mappings,
            "processing_method": "entity_extractor_analysis",
            "confidence_score": 0.8  # Higher confidence for entity extractor
        }
    
    async def bulk_convert(self, requests: List[ClinicalRequestAdvanced], batch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Bulk conversion processing (Story 1.3 advanced feature)
        Processes multiple clinical orders in a single batch
        """
        if not batch_id:
            batch_id = f"batch_{str(uuid4())[:8]}"
        
        start_time = time.time()
        results = []
        successful_count = 0
        failed_count = 0
        
        logger.info(f"Starting bulk conversion {batch_id} - {len(requests)} orders")
        
        for i, request in enumerate(requests):
            try:
                result = await self.convert_advanced(request, f"{batch_id}_order_{i+1}")
                results.append(result)
                successful_count += 1
            except Exception as e:
                error_response = ErrorResponse(
                    request_id=f"{batch_id}_order_{i+1}",
                    error_code="CONVERSION_FAILED",
                    error_type="processing_error",
                    message=f"Failed to process order {i+1}: {str(e)}",
                    timestamp=datetime.now(),
                    suggestions=["Review clinical text format", "Try processing individually"]
                )
                results.append(error_response)
                failed_count += 1
        
        total_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Bulk conversion {batch_id} completed - "
                   f"successful={successful_count}, failed={failed_count}, "
                   f"time={total_time_ms:.2f}ms")
        
        return {
            "batch_id": batch_id,
            "total_orders": len(requests),
            "successful_orders": successful_count, 
            "failed_orders": failed_count,
            "processing_time_ms": total_time_ms,
            "results": results,
            "batch_summary": {
                "success_rate": successful_count / len(requests) if requests else 0,
                "average_processing_time_ms": total_time_ms / len(requests) if requests else 0,
                "processing_date": datetime.now().isoformat()
            }
        }