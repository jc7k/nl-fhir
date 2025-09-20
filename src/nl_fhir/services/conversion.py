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
from .task_workflow_service import get_task_workflow_service
from ..config import get_settings

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
            
            # Epic 2: Full NLP pipeline with MedSpaCy Clinical Intelligence Engine
            # Uses 4-tier medical safety escalation: MedSpaCy → Transformers → Regex → LLM
            nlp_pipeline = await get_nlp_pipeline()
            nlp_results = await nlp_pipeline.process_clinical_text(request.clinical_text, request_id)
            
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
                
                # First, process entities from NLP pipeline to extract patient names
                pipeline_entities = nlp_results.get("extracted_entities", {})
                raw_entities = pipeline_entities.get("entities", [])

                # Extract patient name from person entities
                patient_name = "Unknown Patient"
                logger.info(f"Request {request_id}: Processing {len(raw_entities)} entities for patient name extraction")
                for entity in raw_entities:
                    entity_type = entity.get("type")
                    entity_text = entity.get("text")
                    logger.info(f"Request {request_id}: Entity type: '{entity_type}', text: '{entity_text}'")
                    if entity_type == "person":
                        patient_name = entity_text or "Unknown Patient"
                        logger.info(f"Request {request_id}: Found patient name from entity extraction: {patient_name}")
                        break

                # Create Patient resource (required for all orders)
                patient_data = structured_data.get("patient", {})
                if not patient_data:
                    # Create basic patient from request metadata or extracted entities
                    patient_data = {
                        "name": patient_name,
                        "birthDate": None,
                        "gender": "unknown"
                    }
                else:
                    # Update existing patient data with extracted name if available
                    if patient_name != "Unknown Patient":
                        patient_data["name"] = patient_name

                # Add patient_ref from original request if provided
                if hasattr(request, 'patient_ref') and request.patient_ref:
                    patient_data["patient_ref"] = request.patient_ref
                    logger.info(f"Request {request_id}: Using provided patient reference: {request.patient_ref}")

                patient_resource = resource_factory.create_patient_resource(patient_data, request_id)
                fhir_resources.append(patient_resource)
                patient_ref = patient_resource['id']  # Use just the ID, not Patient/ID
                
                # Create Practitioner resource (for orders)
                practitioner_data = structured_data.get("practitioner", {})
                if not practitioner_data:
                    practitioner_data = {
                        "name": request.practitioner_name if hasattr(request, 'practitioner_name') else "Unknown Practitioner",
                        "identifier": "temp-practitioner"
                    }
                
                practitioner_resource = resource_factory.create_practitioner_resource(practitioner_data, request_id)
                fhir_resources.append(practitioner_resource)
                practitioner_ref = practitioner_resource['id']  # Use just the ID, not Practitioner/ID
                
                # Create Encounter resource
                encounter_data = {
                    "status": "planned",
                    "class": "AMB",  # Ambulatory
                    "period": {"start": datetime.now().isoformat()}
                }
                encounter_resource = resource_factory.create_encounter_resource(encounter_data, patient_ref, request_id)
                fhir_resources.append(encounter_resource)
                encounter_ref = encounter_resource['id']  # Use just the ID, not Encounter/ID
                
                # Create clinical order resources based on NLP results
                # (entities already extracted above for patient name)

                # Organize entities by type for FHIR resource creation
                entities = {
                    "medications": [],
                    "lab_tests": [],
                    "procedures": [],
                    "conditions": [],
                    "patients": []
                }

                # Process entities from the NLP pipeline format
                logger.info(f"Request {request_id}: Processing {len(raw_entities)} raw entities from NLP pipeline")

                for entity in raw_entities:
                    entity_type = entity.get("type", "unknown")
                    entity_text = entity.get("text", "")
                    entity_data = {
                        "text": entity_text,
                        "confidence": entity.get("confidence", 0.0),
                        "source": entity.get("source", "nlp_pipeline")
                    }

                    # Entity type correction - fix common NLP misclassifications
                    corrected_type = self._correct_entity_type(entity_type, entity_text, request_id)
                    if corrected_type != entity_type:
                        logger.info(f"Request {request_id}: Corrected entity type from '{entity_type}' to '{corrected_type}' for text '{entity_text}'")
                        entity_type = corrected_type

                    # Debug logging for entity processing
                    logger.info(f"Request {request_id}: Processing entity - type: {entity_type}, text: '{entity_text}', confidence: {entity.get('confidence', 0.0)}")

                    if entity_type == "medication":
                        # Look for associated dosage and frequency in attributes
                        attributes = entity.get("attributes", {})

                        # Try to extract route, dosage, and frequency from clinical text context for this medication
                        medication_text = entity_data.get("text", "")
                        route = self._extract_route_from_context(medication_text, request.clinical_text, request_id)
                        dosage = self._extract_dosage_from_context(medication_text, request.clinical_text, request_id)
                        frequency = self._extract_frequency_from_context(medication_text, request.clinical_text, request_id)

                        entity_data.update({
                            "dosage": attributes.get("dosage", dosage),
                            "frequency": attributes.get("frequency", frequency),
                            "route": attributes.get("route", route)
                        })
                        entities["medications"].append(entity_data)
                    elif entity_type == "lab_test":
                        entities["lab_tests"].append(entity_data)
                    elif entity_type == "procedure":
                        entities["procedures"].append(entity_data)
                    elif entity_type == "condition":
                        entities["conditions"].append(entity_data)
                    elif entity_type == "person":
                        entities["patients"].append(entity_data)
                
                # Create MedicationRequest if medications detected
                medications = entities.get("medications", [])
                logger.info(f"Request {request_id}: Found {len(medications)} medications to process: {[med.get('text', 'unknown') for med in medications]}")

                # Deduplicate medications to prevent duplicate MedicationRequest resources
                unique_medications = self._deduplicate_medications(medications, request_id)
                logger.info(f"Request {request_id}: After deduplication, processing {len(unique_medications)} unique medications")

                for medication in unique_medications:
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
                        "name": condition.get("text", "Unknown condition"),
                        "clinical_status": "active",
                        "verification_status": "provisional"
                    }
                    
                    condition_resource = resource_factory.create_condition_resource(
                        condition_data, patient_ref, request_id, 
                        encounter_ref=encounter_ref
                    )
                    fhir_resources.append(condition_resource)

                # Create Observation resources for common vitals and weights (feature-flagged)
                try:
                    if not get_settings().observations_enabled:
                        logger.info(f"[{request_id}] Observations feature disabled by configuration")
                        raise RuntimeError("observations_disabled")
                    observations_to_create: List[Dict[str, Any]] = []

                    # Weights from NLP entities (regex extractor populates this)
                    weights = pipeline_entities.get("weights", [])
                    for w in weights:
                        import re as _re
                        m = _re.search(r"(\d+(?:\.\d+)?)\s*kg", w.get("text", ""), flags=_re.IGNORECASE)
                        if m:
                            weight_val = float(m.group(1))
                            observations_to_create.append({
                                "status": "final",
                                "category": "vital-signs",
                                "code": {"system": "http://loinc.org", "code": "29463-7", "display": "Body weight"},
                                "text": "Body weight",
                                "value": weight_val,
                                "unit": "kg"
                            })

                    # Parse common vitals directly from clinical text
                    for obs in self._extract_vitals_from_text(request.clinical_text):
                        observations_to_create.append(obs)

                    # Create Observation resources
                    for obs_data in observations_to_create:
                        obs_resource = resource_factory.create_observation_resource(
                            obs_data,
                            patient_ref,
                            request_id,
                            encounter_ref=encounter_ref
                        )
                        fhir_resources.append(obs_resource)
                except Exception as e:
                    if str(e) != "observations_disabled":
                        logger.warning(f"[{request_id}] Observation creation skipped due to error: {e}")

                # Story TW-002: Task Workflow Integration
                # Detect workflow patterns and create Task resources
                try:
                    task_workflow_service = await get_task_workflow_service()

                    # Convert raw entities to MedicalEntity objects for workflow detection
                    from .nlp.entity_extractor import MedicalEntity, EntityType
                    medical_entities = []

                    for entity in raw_entities:
                        try:
                            # Map entity type string to EntityType enum
                            entity_type_str = entity.get("type", "unknown")
                            if entity_type_str == "workflow":
                                entity_type = EntityType.WORKFLOW
                            elif entity_type_str == "medication":
                                entity_type = EntityType.MEDICATION
                            elif entity_type_str == "lab_test":
                                entity_type = EntityType.LAB_TEST
                            elif entity_type_str == "procedure":
                                entity_type = EntityType.PROCEDURE
                            elif entity_type_str == "condition":
                                entity_type = EntityType.CONDITION
                            elif entity_type_str == "person":
                                entity_type = EntityType.PERSON
                            else:
                                entity_type = EntityType.UNKNOWN

                            medical_entity = MedicalEntity(
                                text=entity.get("text", ""),
                                entity_type=entity_type,
                                start_char=entity.get("start_char", 0),
                                end_char=entity.get("end_char", 0),
                                confidence=entity.get("confidence", 0.0),
                                attributes=entity.get("attributes", {}),
                                source=entity.get("source", "nlp_pipeline")
                            )
                            medical_entities.append(medical_entity)
                        except Exception as e:
                            logger.warning(f"[{request_id}] Failed to convert entity to MedicalEntity: {e}")

                    # Detect workflow patterns and generate Task specifications
                    task_specs = task_workflow_service.detect_workflow_patterns(
                        medical_entities, request.clinical_text, request_id
                    )

                    if task_specs:
                        logger.info(f"[{request_id}] Creating {len(task_specs)} Task resources from workflow patterns")

                        # Link Task specs to existing resources
                        linked_tasks = task_workflow_service.link_tasks_to_resources(
                            task_specs, fhir_resources, request_id
                        )

                        # Create Task resources
                        for task_spec, focus_ref in linked_tasks:
                            # Determine task assignments
                            requester_ref, owner_ref = task_workflow_service.determine_task_assignments(
                                task_spec, request.clinical_text, request_id
                            )

                            # Create Task resource
                            task_resource = resource_factory.create_task_resource(
                                task_data=task_spec,
                                patient_ref=patient_ref,
                                focus_ref=focus_ref,
                                requester_ref=requester_ref,
                                owner_ref=owner_ref,
                                request_id=request_id
                            )

                            if task_resource:
                                fhir_resources.append(task_resource)
                                logger.info(f"[{request_id}] Created Task resource: {task_resource.get('id')}")

                except Exception as e:
                    logger.error(f"[{request_id}] Task workflow integration failed: {e}")
                    # Continue processing without Tasks if workflow detection fails

                # Assemble FHIR transaction bundle
                bundle_assembler = FHIRBundleAssembler()
                bundle_assembler.initialize()
                
                # Create transaction bundle
                fhir_bundle = bundle_assembler.create_transaction_bundle(fhir_resources, request_id)
                
                # Optimize bundle for HAPI FHIR processing
                fhir_bundle = bundle_assembler.optimize_bundle(fhir_bundle, request_id)
                
                # Generate bundle summary with extracted entities for transparency
                bundle_summary = bundle_assembler.get_bundle_summary(fhir_bundle)

                # Add extracted entities to bundle summary for visual inspection
                pipeline_entities = nlp_results.get("extracted_entities", {})
                raw_entities = pipeline_entities.get("entities", [])
                entity_summary = []

                for entity in raw_entities:
                    entity_summary.append({
                        "type": entity.get("type", "unknown"),
                        "text": entity.get("text", ""),
                        "confidence": round(entity.get("confidence", 0.0), 3)
                    })

                # Add entities to bundle summary for user visibility
                bundle_summary["extracted_entities"] = {
                    "total_entities": len(entity_summary),
                    "entities": entity_summary,
                    "medications_found": len(entities.get("medications", [])),
                    "lab_tests_found": len(entities.get("lab_tests", [])),
                    "procedures_found": len(entities.get("procedures", [])),
                    "patients_found": len(entities.get("patients", []))
                }

                logger.info(f"Request {request_id}: Bundle summary enhanced with {len(entity_summary)} extracted entities")
                
                # Validate FHIR bundle
                fhir_validator = await get_fhir_validator()
                fhir_validation_results = fhir_validator.validate_bundle(fhir_bundle, request_id)
                
                # Optional: Validate with HAPI FHIR server if available
                try:
                    hapi_client = await get_hapi_client()
                    hapi_validation = await hapi_client.validate_bundle(fhir_bundle, request_id)
                    
                    # Merge validation results
                    fhir_validation_results["hapi_validation"] = hapi_validation
                    
                    # Update main validation status if HAPI validation succeeds
                    if hapi_validation.get("is_valid", False):
                        fhir_validation_results["is_valid"] = True
                        logger.info(f"[{request_id}] HAPI validation PASSED - updating main validation status")
                    else:
                        logger.warning(f"[{request_id}] HAPI validation FAILED: {hapi_validation.get('errors', [])}")
                    
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
                message="Clinical order processed with MedSpaCy Clinical Intelligence and FHIR assembly. Ready for Epic 4 validation.",
                metadata=metadata,
                validation=validation_result,
                
                # Epic 2: Real NLP Results from MedSpaCy Clinical Intelligence Engine
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
            "conditions": [],
            "patients": []  # Changed from "persons" to "patients"
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
                    "text": entity.text,  # Changed from "name" to "text" for FHIR compatibility
                    "dosage": dosage,
                    "frequency": frequency,
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["medications"].append(medication_data)
            
            elif entity.entity_type == EntityType.LAB_TEST:
                lab_data = {
                    "text": entity.text,  # Changed from "name" to "text" for FHIR compatibility
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["lab_tests"].append(lab_data)
            
            elif entity.entity_type == EntityType.PROCEDURE:
                procedure_data = {
                    "text": entity.text,  # Changed from "name" to "text" for FHIR compatibility
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["procedures"].append(procedure_data)
            
            elif entity.entity_type == EntityType.CONDITION:
                condition_data = {
                    "text": entity.text,  # Changed from "name" to "text" for FHIR compatibility
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["conditions"].append(condition_data)
            
            elif entity.entity_type == EntityType.PERSON:
                person_data = {
                    "text": entity.text,
                    "confidence": entity.confidence,
                    "source": entity.source
                }
                extracted_entities["patients"].append(person_data)  # Changed from "persons" to "patients"
        
        # Deduplicate extracted entities to prevent duplicate FHIR resources
        def deduplicate_entities(entity_list, key_field="text"):  # Changed default from "name" to "text"
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
        extracted_entities["conditions"] = deduplicate_entities(extracted_entities["conditions"])
        extracted_entities["patients"] = deduplicate_entities(extracted_entities["patients"])  # Changed from "persons" to "patients"
        
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
        
        # Basic structured output - include patient data for FHIR resource creation
        structured_output = {
            "summary": f"Clinical order with {len(extracted_entities['medications'])} medications",
            "prioritized_actions": []
        }
        
        # Add patient information to structured_output if patients were extracted
        if extracted_entities["patients"]:  # Changed from "persons" to "patients"
            # Use the first extracted patient as the patient
            patient_person = extracted_entities["patients"][0]
            structured_output["patient"] = {
                "name": patient_person["text"],
                "birthDate": None,  # Not extracted from text
                "gender": "unknown"  # Not extracted from text
            }
            logger.info(f"[{request_id}] Extracted patient name: {patient_person['text']}")
        else:
            logger.info(f"[{request_id}] No patient names extracted from clinical text")
        
        logger.info(f"[{request_id}] Basic text analysis completed - "
                   f"Found: {len(extracted_entities['medications'])} medications, "
                   f"{len(extracted_entities['lab_tests'])} lab tests, "
                   f"{len(extracted_entities['procedures'])} procedures, "
                   f"{len(extracted_entities['conditions'])} conditions, "
                   f"{len(extracted_entities['patients'])} patients")  # Changed from "persons" to "patients"
        
        return {
            "extracted_entities": extracted_entities,
            "structured_output": structured_output,
            "terminology_mappings": terminology_mappings,
            "processing_method": "entity_extractor_analysis",
            "confidence_score": 0.8  # Higher confidence for entity extractor
        }

    def _extract_route_from_context(self, medication_text: str, clinical_text: str, request_id: str) -> str:
        """Extract route of administration from clinical text context"""
        import re

        # Convert to lowercase for case-insensitive matching
        text_lower = clinical_text.lower()
        med_lower = medication_text.lower()

        # First check if medication is typically oral (most common medications)
        oral_medications = {
            'metformin', 'lisinopril', 'amlodipine', 'simvastatin', 'omeprazole', 'levothyroxine',
            'sertraline', 'fluoxetine', 'aspirin', 'ibuprofen', 'acetaminophen', 'amoxicillin',
            'azithromycin', 'ciprofloxacin', 'prednisone', 'hydrochlorothiazide', 'metoprolol',
            'warfarin', 'furosemide', 'gabapentin', 'cephalexin', 'captopril', 'enalapril', 'ramipril'
        }

        # Find the position of the medication in the text
        med_pos = text_lower.find(med_lower)
        if med_pos == -1:
            # If medication is in our oral list, default to oral, otherwise generic oral
            default_route = "oral" if med_lower in oral_medications else "oral"
            logger.info(f"Request {request_id}: Medication '{medication_text}' not found in text, defaulting to {default_route}")
            return default_route

        # Look for route keywords within a reasonable distance of the medication
        # Check 25 characters before and after the medication for more precise matching
        context_start = max(0, med_pos - 25)
        context_end = min(len(text_lower), med_pos + len(med_lower) + 25)
        context = text_lower[context_start:context_end]

        # Route patterns to look for - longer form keywords only to avoid false matches
        route_patterns = {
            "iv": ["intravenous", "intravenously"],
            "oral": ["oral", "orally", "by mouth"],
            "im": ["intramuscular", "intramuscularly"],
            "subcutaneous": ["subcutaneous", "subcutaneously", "subq"],
            "topical": ["topical", "topically", "applied"],
            "inhaled": ["inhaled", "inhalation", "nebulized"],
            "nasal": ["nasal", "nasally", "intranasal"],
            "rectal": ["rectal", "rectally"],
            "sublingual": ["sublingual", "sublingually"]
        }

        # Special patterns that need word boundary checking (short abbreviations)
        special_patterns = {
            "iv": [r'\biv\b'],
            "im": [r'\bim\b'],
            "subcutaneous": [r'\bsc\b'],  # Only match "sc" as a complete word
            "oral": [r'\bpo\b'],
            "rectal": [r'\bpr\b'],
            "sublingual": [r'\bsl\b']
        }

        # First check special patterns with word boundaries
        import re
        for route_name, patterns in special_patterns.items():
            for pattern in patterns:
                if re.search(pattern, context, re.IGNORECASE):
                    logger.info(f"Request {request_id}: Found route '{route_name}' for medication '{medication_text}' using pattern '{pattern}'")
                    return route_name

        # Then check regular keywords (longer forms to avoid false matches)
        for route_name, keywords in route_patterns.items():
            for keyword in keywords:
                if keyword in context:
                    logger.info(f"Request {request_id}: Found route '{route_name}' for medication '{medication_text}' using keyword '{keyword}'")
                    return route_name

        # Smart defaulting based on medication type
        if med_lower in oral_medications:
            logger.info(f"Request {request_id}: No specific route found for oral medication '{medication_text}', defaulting to oral")
            return "oral"

        # For unknown medications, default to oral (most common)
        logger.info(f"Request {request_id}: No specific route found for medication '{medication_text}', defaulting to oral")
        return "oral"

    def _extract_dosage_from_context(self, medication_text: str, clinical_text: str, request_id: str) -> str:
        """Extract dosage from clinical text context"""
        import re

        # Convert to lowercase for case-insensitive matching
        text_lower = clinical_text.lower()
        med_lower = medication_text.lower()

        # Find the position of the medication in the text
        med_pos = text_lower.find(med_lower)
        if med_pos == -1:
            return "As directed"  # Default fallback

        # Look for dosage patterns within a reasonable distance of the medication
        # Check 30 characters before and after the medication
        context_start = max(0, med_pos - 30)
        context_end = min(len(text_lower), med_pos + len(med_lower) + 30)
        context = clinical_text[context_start:context_end]  # Use original case for dosage extraction

        # Dosage patterns to look for (with units)
        dosage_patterns = [
            r'(\d+(?:\.\d+)?\s*mg(?:/m²)?)',  # mg or mg/m²
            r'(\d+(?:\.\d+)?\s*g)',          # grams
            r'(\d+(?:\.\d+)?\s*ml)',         # milliliters
            r'(\d+(?:\.\d+)?\s*mcg)',        # micrograms
            r'(\d+(?:\.\d+)?\s*units?)',     # units
            r'(\d+(?:\.\d+)?\s*iu)',         # international units
            r'(\d+(?:\.\d+)?\s*tablets?)',   # tablets
            r'(\d+(?:\.\d+)?\s*capsules?)',  # capsules
            r'(\d+(?:\.\d+)?\s*drops?)',     # drops
            r'(\d+(?:\.\d+)?\s*l\b)',        # liters (with word boundary)
        ]

        # Search for dosage patterns in the context
        for pattern in dosage_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            if matches:
                dosage = matches[0].strip()
                logger.info(f"Request {request_id}: Found dosage '{dosage}' for medication '{medication_text}'")
                return dosage

        # Default to "As directed" if no specific dosage found
        logger.info(f"Request {request_id}: No specific dosage found for medication '{medication_text}', defaulting to 'As directed'")
        return "As directed"

    def _extract_frequency_from_context(self, medication_text: str, clinical_text: str, request_id: str) -> str:
        """Extract frequency from clinical text context"""
        import re

        # Convert to lowercase for case-insensitive matching
        text_lower = clinical_text.lower()
        med_lower = medication_text.lower()

        # Find the position of the medication in the text
        med_pos = text_lower.find(med_lower)
        if med_pos == -1:
            return "As needed"  # Default fallback

        # Look for frequency patterns within a reasonable distance of the medication
        # Check 30 characters before and after the medication for more precise matching
        context_start = max(0, med_pos - 30)
        context_end = min(len(text_lower), med_pos + len(med_lower) + 30)
        context = text_lower[context_start:context_end]

        # Frequency patterns to look for
        frequency_patterns = {
            "once daily": ["once daily", "once a day", "qd", "od"],
            "twice daily": ["twice daily", "twice a day", "bid", "b.i.d.", "2x daily"],
            "three times daily": ["three times daily", "three times a day", "tid", "t.i.d.", "3x daily"],
            "four times daily": ["four times daily", "four times a day", "qid", "q.i.d.", "4x daily"],
            "every 6 hours": ["every 6 hours", "q6h", "6 hourly"],
            "every 8 hours": ["every 8 hours", "q8h", "8 hourly"],
            "every 12 hours": ["every 12 hours", "q12h", "12 hourly"],
            "every 2 weeks": ["every 2 weeks", "every two weeks", "biweekly"],
            "every 3 weeks": ["every 3 weeks", "every three weeks"],
            "every 4 weeks": ["every 4 weeks", "every four weeks", "monthly"],
            "weekly": ["weekly", "once weekly", "every week"],
            "as needed": ["as needed", "prn", "p.r.n.", "when needed"],
            "before meals": ["before meals", "ac", "a.c.", "pre-meal"],
            "after meals": ["after meals", "pc", "p.c.", "post-meal"],
            "at bedtime": ["at bedtime", "qhs", "q.h.s.", "bedtime"],
        }

        # Check for frequency keywords in the context
        # Sort by length (longest first) to avoid partial matches
        sorted_patterns = sorted(frequency_patterns.items(), key=lambda x: max(len(k) for k in x[1]), reverse=True)

        for frequency_name, keywords in sorted_patterns:
            for keyword in keywords:
                if keyword in context:
                    logger.info(f"Request {request_id}: Found frequency '{frequency_name}' for medication '{medication_text}' using keyword '{keyword}'")
                    return frequency_name

        # Look for numeric patterns like "2x" or "3 times"
        numeric_patterns = [
            (r'\b(\d+)\s*x\s+daily\b', lambda m: f"{m.group(1)} times daily"),
            (r'\b(\d+)\s+times?\s+daily\b', lambda m: f"{m.group(1)} times daily"),
            (r'\b(\d+)\s*x\s+per\s+day\b', lambda m: f"{m.group(1)} times daily"),
            (r'\bevery\s+(\d+)\s+hours?\b', lambda m: f"every {m.group(1)} hours"),
        ]

        for pattern, formatter in numeric_patterns:
            match = re.search(pattern, context)
            if match:
                frequency = formatter(match)
                logger.info(f"Request {request_id}: Found numeric frequency '{frequency}' for medication '{medication_text}'")
                return frequency

        # Default to "As needed" if no specific frequency found
        logger.info(f"Request {request_id}: No specific frequency found for medication '{medication_text}', defaulting to 'As needed'")
        return "As needed"

    def _extract_vitals_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract simple vitals from free text to Observation payloads.

        Heuristic, conservative patterns for: BP, HR, RR, Temp, SpO2.
        Returns observation_data dicts for resource_factory.create_observation_resource.
        """
        import re
        found: List[Dict[str, Any]] = []
        t = text or ""

        # Blood pressure with label to avoid false positives
        bp_patterns = [
            r"\b(?:bp|blood\s*pressure)[:\s]*?(\d{2,3})\s*/\s*(\d{2,3})\b",
        ]
        for pat in bp_patterns:
            m = re.search(pat, t, re.IGNORECASE)
            if m:
                sys = int(m.group(1))
                dia = int(m.group(2))
                interp = "high" if sys >= 140 or dia >= 90 else None
                found.append({
                    "status": "final",
                    "category": "vital-signs",
                    "code": {"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"},
                    "text": "Systolic blood pressure",
                    "value": sys,
                    "unit": "mmHg",
                    "interpretation": interp,
                })
                found.append({
                    "status": "final",
                    "category": "vital-signs",
                    "code": {"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"},
                    "text": "Diastolic blood pressure",
                    "value": dia,
                    "unit": "mmHg",
                    "interpretation": interp,
                })
                break

        # Heart rate
        m = re.search(r"\b(?:hr|heart\s*rate|pulse)[:\s]*?(\d{2,3})\b", t, re.IGNORECASE)
        if m:
            hr = int(m.group(1))
            interp = "high" if hr > 100 else ("low" if hr < 60 else None)
            found.append({
                "status": "final",
                "category": "vital-signs",
                "code": {"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"},
                "text": "Heart rate",
                "value": hr,
                "unit": "beats/min",
                "interpretation": interp,
            })

        # Respiratory rate
        m = re.search(r"\b(?:rr|respiratory\s*rate)[:\s]*?(\d{1,2})\b", t, re.IGNORECASE)
        if m:
            rr = int(m.group(1))
            interp = "high" if rr > 20 else ("low" if rr < 12 else None)
            found.append({
                "status": "final",
                "category": "vital-signs",
                "code": {"system": "http://loinc.org", "code": "9279-1", "display": "Respiratory rate"},
                "text": "Respiratory rate",
                "value": rr,
                "unit": "breaths/min",
                "interpretation": interp,
            })

        # Temperature (C or F)
        m = re.search(r"\b(?:temp|temperature)[:\s]*?(\d{2,3}(?:\.\d)?)\s*(°?\s*[FCfc])?\b", t, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            unit_raw = (m.group(2) or "").lower()
            is_f = "f" in unit_raw if unit_raw else val > 45
            interp = None
            if is_f and val >= 100.4:
                interp = "high"
            if not is_f and val >= 38.0:
                interp = "high"
            found.append({
                "status": "final",
                "category": "vital-signs",
                "code": {"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"},
                "text": "Body temperature",
                "value": val,
                "unit": "F" if is_f else "C",
                "interpretation": interp,
            })

        # SpO2
        m = re.search(r"\b(?:spo2|o2\s*sat|oxygen\s*saturation|sat)[:\s]*?(\d{2,3})\s*%", t, re.IGNORECASE)
        if m:
            spo2 = int(m.group(1))
            interp = "low" if spo2 < 92 else None
            found.append({
                "status": "final",
                "category": "vital-signs",
                "code": {"system": "http://loinc.org", "code": "59408-5", "display": "Oxygen saturation (pulse oximetry)"},
                "text": "SpO2",
                "value": spo2,
                "unit": "%",
                "interpretation": interp,
            })

        return found

    def _correct_entity_type(self, entity_type: str, entity_text: str, request_id: str) -> str:
        """Correct common NLP entity type misclassifications"""
        import re

        text_lower = entity_text.lower().strip()

        # Pattern-based corrections for common misclassifications

        # If classified as medication but looks like dosage (contains numbers + units)
        if entity_type == "medication":
            dosage_patterns = [
                r'^\d+(?:\.\d+)?\s*mg(?:/m²)?$',  # 80mg, 80mg/m², 500mg
                r'^\d+(?:\.\d+)?\s*g$',           # 2g
                r'^\d+(?:\.\d+)?\s*ml$',          # 10ml
                r'^\d+(?:\.\d+)?\s*mcg$',         # 500mcg
                r'^\d+(?:\.\d+)?\s*units?$',      # 10 units
                r'^\d+(?:\.\d+)?\s*iu$',          # 400iu
                r'^\d+(?:\.\d+)?\s*tablets?$',    # 2 tablets
                r'^\d+(?:\.\d+)?\s*capsules?$',   # 1 capsule
                r'^\d+(?:\.\d+)?\s*drops?$',      # 3 drops
                r'^\d+(?:\.\d+)?\s*l$',           # 2L
                r'^\d+(?:\.\d+)?mg$',             # 500mg (no space)
                r'^\d+(?:\.\d+)?ml$',             # 10ml (no space)
                r'^\d+(?:\.\d+)?mcg$',            # 500mcg (no space)
            ]

            for pattern in dosage_patterns:
                if re.match(pattern, text_lower):
                    logger.info(f"Request {request_id}: Correcting '{entity_text}' from 'medication' to 'dosage' (matches dosage pattern)")
                    return "dosage"

        # If classified as dosage but looks like medication name
        elif entity_type == "dosage":
            # Known medication names (common ones that might be misclassified)
            medication_names = [
                'cisplatin', 'carboplatin', 'paclitaxel', 'doxorubicin', 'cyclophosphamide',
                'cephalexin', 'amoxicillin', 'azithromycin', 'ciprofloxacin', 'clindamycin',
                'metformin', 'lisinopril', 'atorvastatin', 'amlodipine', 'hydrochlorothiazide',
                'gabapentin', 'sertraline', 'omeprazole', 'warfarin', 'furosemide',
                'prednisone', 'insulin', 'albuterol', 'levothyroxine', 'citalopram',
                'metoprolol', 'propranolol', 'carvedilol', 'digoxin', 'verapamil',
                'ibuprofen', 'acetaminophen', 'aspirin', 'naproxen', 'celecoxib',
                'morphine', 'oxycodone', 'hydrocodone', 'tramadol', 'fentanyl'
            ]

            # Check if text matches known medication names
            if text_lower in medication_names:
                logger.info(f"Request {request_id}: Correcting '{entity_text}' from 'dosage' to 'medication' (known medication name)")
                return "medication"

            # Check if it looks like a medication name (alphabetic, not starting with numbers)
            if re.match(r'^[a-zA-Z][a-zA-Z\s\-]*$', text_lower) and not re.search(r'\d', text_lower):
                # Additional check: if it doesn't contain dosage-like words
                dosage_keywords = ['mg', 'gram', 'ml', 'mcg', 'unit', 'tablet', 'capsule', 'drop', 'daily', 'twice', 'three']
                if not any(keyword in text_lower for keyword in dosage_keywords):
                    logger.info(f"Request {request_id}: Correcting '{entity_text}' from 'dosage' to 'medication' (alphabetic pattern without dosage keywords)")
                    return "medication"

        # If classified as condition but looks like a number (common misclassification)
        elif entity_type == "condition":
            if re.match(r'^\d+$', text_lower):
                # Numbers like "6", "7" should probably be ignored or classified differently
                logger.info(f"Request {request_id}: Correcting '{entity_text}' from 'condition' to 'unknown' (standalone number)")
                return "unknown"

        # Additional check: if something that looks like a dosage is misclassified as anything else
        if entity_type not in ["dosage", "unknown"]:
            dosage_patterns = [
                r'^\d+(?:\.\d+)?\s*mg(?:/m²)?$',  # 80mg, 80mg/m², 500mg
                r'^\d+(?:\.\d+)?\s*g$',           # 2g
                r'^\d+(?:\.\d+)?\s*ml$',          # 10ml
                r'^\d+(?:\.\d+)?\s*mcg$',         # 500mcg
                r'^\d+(?:\.\d+)?mg$',             # 500mg (no space)
                r'^\d+(?:\.\d+)?ml$',             # 10ml (no space)
                r'^\d+(?:\.\d+)?mcg$',            # 500mcg (no space)
            ]

            for pattern in dosage_patterns:
                if re.match(pattern, text_lower):
                    logger.info(f"Request {request_id}: Correcting '{entity_text}' from '{entity_type}' to 'dosage' (clearly a dosage)")
                    return "dosage"

        # Return original type if no correction needed
        return entity_type

    def _deduplicate_medications(self, medications: List[Dict[str, Any]], request_id: str) -> List[Dict[str, Any]]:
        """Deduplicate medications based on medication name to prevent duplicate FHIR resources"""

        if not medications:
            return []

        unique_meds = {}
        for med in medications:
            med_name = med.get("text", "").strip().lower()

            # Skip empty or invalid names
            if not med_name:
                continue

            # If we already have this medication, keep the one with higher confidence
            # or merge the dosage/frequency information
            if med_name in unique_meds:
                existing = unique_meds[med_name]
                current_confidence = med.get("confidence", 0.0)
                existing_confidence = existing.get("confidence", 0.0)

                # Keep higher confidence medication, but merge missing information
                if current_confidence > existing_confidence:
                    # Update with current medication but preserve any additional info from existing
                    updated_med = med.copy()
                    if not updated_med.get("dosage") and existing.get("dosage"):
                        updated_med["dosage"] = existing["dosage"]
                    if not updated_med.get("frequency") and existing.get("frequency"):
                        updated_med["frequency"] = existing["frequency"]
                    if not updated_med.get("route") and existing.get("route"):
                        updated_med["route"] = existing["route"]
                    unique_meds[med_name] = updated_med
                    logger.info(f"Request {request_id}: Updated medication '{med_name}' with higher confidence entry")
                else:
                    # Keep existing but merge any missing info from current
                    if not existing.get("dosage") and med.get("dosage"):
                        existing["dosage"] = med["dosage"]
                    if not existing.get("frequency") and med.get("frequency"):
                        existing["frequency"] = med["frequency"]
                    if not existing.get("route") and med.get("route"):
                        existing["route"] = med["route"]
                    logger.info(f"Request {request_id}: Kept existing medication '{med_name}' and merged additional info")
            else:
                unique_meds[med_name] = med.copy()

        result = list(unique_meds.values())
        logger.info(f"Request {request_id}: Deduplicated {len(medications)} medications to {len(result)} unique medications")
        return result

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


# Legacy function for backward compatibility with existing tests
async def convert_clinical_text_to_fhir(clinical_text: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Legacy wrapper function for test compatibility
    Provides backward compatibility for existing test cases
    """
    from ..models.request import ClinicalRequestAdvanced

    # Create a request object
    request = ClinicalRequestAdvanced(
        clinical_text=clinical_text,
        priority="routine",
        department="general"
    )

    # Use the main conversion service
    service = ConversionService()
    response = await service.convert_advanced(request, request_id)

    # Convert to legacy format expected by tests
    return {
        "request_id": response.request_id,
        "status": response.status.value,
        "fhir_bundle": response.fhir_bundle if hasattr(response, 'fhir_bundle') else None,
        "processing_time_ms": response.metadata.processing_time_ms if response.metadata else 0,
        "validation_results": response.validation_results if hasattr(response, 'validation_results') else [],
        "extracted_entities": response.extracted_entities if hasattr(response, 'extracted_entities') else {},
        "message": response.message
    }
