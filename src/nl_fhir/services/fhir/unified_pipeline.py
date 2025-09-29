"""
Unified FHIR Pipeline Orchestrator for Epic 3 Production
Complete end-to-end FHIR processing pipeline integration
HIPAA Compliant: Production-ready pipeline with comprehensive monitoring
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from uuid import uuid4
from dataclasses import dataclass, asdict

from .factory_adapter import get_fhir_resource_factory
from .bundle_assembler import get_bundle_assembler
from .validation_service import get_validation_service
from .execution_service import get_execution_service
from .failover_manager import get_failover_manager

logger = logging.getLogger(__name__)


@dataclass
class ProcessingMetadata:
    """Metadata tracking for FHIR pipeline processing"""
    request_id: str
    start_time: datetime
    processing_steps: List[str]
    performance_metrics: Dict[str, float]
    quality_scores: Dict[str, float]
    error_count: int
    warning_count: int


@dataclass
class FHIRProcessingResult:
    """Complete FHIR processing result for Epic 4 integration"""
    request_id: str
    success: bool
    processing_metadata: ProcessingMetadata
    nlp_entities: Optional[Dict[str, Any]]  # Epic 2 output
    fhir_resources: List[Dict[str, Any]]  # Story 3.1 output
    fhir_bundle: Optional[Dict[str, Any]]  # Story 3.2 output
    validation_results: Optional[Dict[str, Any]]  # Story 3.3 output
    execution_results: Optional[Dict[str, Any]]  # Story 3.3 execution
    quality_metrics: Dict[str, Any]
    bundle_summary_data: Dict[str, Any]  # Epic 4 preparation
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        result['processing_metadata']['start_time'] = self.processing_metadata.start_time.isoformat()
        return result


class UnifiedFHIRPipeline:
    """Production-ready unified FHIR processing pipeline"""
    
    def __init__(self):
        self.initialized = False
        self.resource_factory = None
        self.bundle_assembler = None
        self.validation_service = None
        self.execution_service = None
        self.failover_manager = None
        
        # Performance tracking
        self.processing_count = 0
        self.total_processing_time = 0.0
        self.validation_success_count = 0
        self.quality_scores = []
        
        # Error tracking
        self.error_patterns = {}
        self.recent_errors = []
        
    async def initialize(self) -> bool:
        """Initialize all FHIR pipeline services"""
        try:
            logger.info("Initializing unified FHIR pipeline...")
            
            # Initialize all services in parallel for performance
            services = await asyncio.gather(
                get_fhir_resource_factory(),
                get_bundle_assembler(),
                get_validation_service(),
                get_execution_service(),
                get_failover_manager(),
                return_exceptions=True
            )
            
            self.resource_factory = services[0]
            self.bundle_assembler = services[1]
            self.validation_service = services[2]
            self.execution_service = services[3]
            self.failover_manager = services[4]
            
            # Check for any initialization errors
            for i, service in enumerate(services):
                if isinstance(service, Exception):
                    logger.error(f"Failed to initialize service {i}: {service}")
                    return False
            
            # Verify all services are initialized
            services_status = [
                self.resource_factory.initialized,
                self.bundle_assembler.initialized,
                self.validation_service.initialized,
                self.execution_service.initialized,
                self.failover_manager.initialized
            ]
            
            if not all(services_status):
                logger.error(f"Some services failed to initialize: {services_status}")
                return False
            
            self.initialized = True
            logger.info("Unified FHIR pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize unified FHIR pipeline: {e}")
            return False
    
    async def process_nlp_to_fhir(
        self, 
        nlp_entities: Dict[str, Any], 
        request_id: Optional[str] = None,
        validate_bundle: bool = True,
        execute_bundle: bool = False
    ) -> FHIRProcessingResult:
        """
        Complete end-to-end FHIR pipeline processing
        
        Args:
            nlp_entities: Structured medical data from Epic 2 NLP
            request_id: Unique request identifier
            validate_bundle: Whether to validate with HAPI FHIR
            execute_bundle: Whether to execute on HAPI FHIR server
        
        Returns:
            Complete FHIR processing result
        """
        
        if not self.initialized:
            await self.initialize()
        
        if not request_id:
            request_id = f"fhir-pipeline-{str(uuid4())[:8]}"
        
        start_time = time.time()
        processing_metadata = ProcessingMetadata(
            request_id=request_id,
            start_time=datetime.now(timezone.utc),
            processing_steps=[],
            performance_metrics={},
            quality_scores={},
            error_count=0,
            warning_count=0
        )
        
        result = FHIRProcessingResult(
            request_id=request_id,
            success=False,
            processing_metadata=processing_metadata,
            nlp_entities=nlp_entities,
            fhir_resources=[],
            fhir_bundle=None,
            validation_results=None,
            execution_results=None,
            quality_metrics={},
            bundle_summary_data={},
            errors=[],
            warnings=[]
        )
        
        try:
            logger.info(f"[{request_id}] Starting unified FHIR pipeline processing")
            
            # Step 1: Create FHIR resources from NLP entities (Story 3.1)
            step_start = time.time()
            fhir_resources = await self._create_fhir_resources(nlp_entities, request_id)
            step_time = time.time() - step_start
            
            processing_metadata.processing_steps.append("resource_creation")
            processing_metadata.performance_metrics["resource_creation_time"] = step_time
            result.fhir_resources = fhir_resources
            
            if not fhir_resources:
                result.errors.append("No FHIR resources could be created from NLP entities")
                return result
            
            logger.info(f"[{request_id}] Created {len(fhir_resources)} FHIR resources in {step_time:.3f}s")
            
            # Step 2: Assemble transaction bundle (Story 3.2)
            step_start = time.time()
            fhir_bundle = await self._assemble_transaction_bundle(fhir_resources, request_id)
            step_time = time.time() - step_start
            
            processing_metadata.processing_steps.append("bundle_assembly")
            processing_metadata.performance_metrics["bundle_assembly_time"] = step_time
            result.fhir_bundle = fhir_bundle
            
            if not fhir_bundle:
                result.errors.append("Failed to assemble FHIR transaction bundle")
                return result
            
            logger.info(f"[{request_id}] Assembled bundle with {len(fhir_bundle.get('entry', []))} entries in {step_time:.3f}s")
            
            # Step 3: Validate bundle with HAPI FHIR (Story 3.3)
            if validate_bundle:
                step_start = time.time()
                validation_results = await self._validate_fhir_bundle(fhir_bundle, request_id)
                step_time = time.time() - step_start
                
                processing_metadata.processing_steps.append("bundle_validation")
                processing_metadata.performance_metrics["validation_time"] = step_time
                result.validation_results = validation_results
                
                # Track validation success
                if validation_results and validation_results.get("is_valid"):
                    self.validation_success_count += 1
                    processing_metadata.quality_scores["validation_success"] = 1.0
                else:
                    processing_metadata.quality_scores["validation_success"] = 0.0
                
                # Track bundle quality score
                quality_score = validation_results.get("bundle_quality_score", 0.0) if validation_results else 0.0
                processing_metadata.quality_scores["bundle_quality"] = quality_score
                self.quality_scores.append(quality_score)
                
                logger.info(f"[{request_id}] Validated bundle (score: {quality_score:.2f}) in {step_time:.3f}s")
            
            # Step 4: Optional bundle execution (Story 3.3)
            if execute_bundle and result.validation_results and result.validation_results.get("is_valid"):
                step_start = time.time()
                execution_results = await self._execute_fhir_bundle(fhir_bundle, request_id)
                step_time = time.time() - step_start
                
                processing_metadata.processing_steps.append("bundle_execution")
                processing_metadata.performance_metrics["execution_time"] = step_time
                result.execution_results = execution_results
                
                logger.info(f"[{request_id}] Executed bundle in {step_time:.3f}s")
            
            # Step 5: Generate quality metrics and Epic 4 preparation data
            result.quality_metrics = self._generate_quality_metrics(result)
            result.bundle_summary_data = self._prepare_epic4_summary_data(result)
            
            # Calculate total processing time
            total_time = time.time() - start_time
            processing_metadata.performance_metrics["total_processing_time"] = total_time
            self.total_processing_time += total_time
            self.processing_count += 1
            
            # Update metadata
            processing_metadata.error_count = len(result.errors)
            processing_metadata.warning_count = len(result.warnings)
            result.processing_metadata = processing_metadata
            
            # Determine overall success
            result.success = (
                len(result.fhir_resources) > 0 and
                result.fhir_bundle is not None and
                len(result.errors) == 0
            )
            
            if result.success:
                logger.info(f"[{request_id}] FHIR pipeline completed successfully in {total_time:.3f}s")
            else:
                logger.warning(f"[{request_id}] FHIR pipeline completed with issues in {total_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"[{request_id}] FHIR pipeline processing failed: {e}")
            result.errors.append(f"Pipeline processing error: {str(e)}")
            result.processing_metadata.error_count = len(result.errors)
            return result
    
    async def _create_fhir_resources(self, nlp_entities: Dict[str, Any], request_id: str) -> List[Dict[str, Any]]:
        """Create FHIR resources from NLP entities"""
        resources = []
        
        try:
            # Create Patient resource
            patient_info = nlp_entities.get("patient_info", {})
            if patient_info:
                patient_resource = self.resource_factory.create_patient_resource(patient_info, request_id)
                if patient_resource:
                    resources.append(patient_resource)
            
            # Create Condition resources
            conditions = nlp_entities.get("conditions", [])
            patient_ref = patient_info.get("patient_ref", f"PT-{request_id}")
            
            for condition in conditions:
                condition_resource = self.resource_factory.create_condition_resource(condition, patient_ref, request_id)
                if condition_resource:
                    resources.append(condition_resource)
            
            # Create MedicationRequest resources
            medications = nlp_entities.get("medications", [])
            for medication in medications:
                med_resource = self.resource_factory.create_medication_request(medication, patient_ref, request_id)
                if med_resource:
                    resources.append(med_resource)
            
            # Create ServiceRequest resources for procedures/tests
            procedures = nlp_entities.get("procedures", [])
            for procedure in procedures:
                service_resource = self.resource_factory.create_service_request(procedure, patient_ref, request_id)
                if service_resource:
                    resources.append(service_resource)
            
            return resources
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create FHIR resources: {e}")
            return []
    
    async def _assemble_transaction_bundle(self, resources: List[Dict[str, Any]], request_id: str) -> Optional[Dict[str, Any]]:
        """Assemble FHIR transaction bundle"""
        try:
            bundle = self.bundle_assembler.create_transaction_bundle(resources, request_id)
            
            # Optimize bundle for better validation success
            optimized_bundle = self.bundle_assembler.optimize_bundle(bundle, request_id)
            
            return optimized_bundle
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to assemble transaction bundle: {e}")
            return None
    
    async def _validate_fhir_bundle(self, bundle: Dict[str, Any], request_id: str) -> Optional[Dict[str, Any]]:
        """Validate FHIR bundle with HAPI FHIR"""
        try:
            validation_result = await self.validation_service.validate_bundle(bundle, request_id)
            return validation_result
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to validate FHIR bundle: {e}")
            return None
    
    async def _execute_fhir_bundle(self, bundle: Dict[str, Any], request_id: str) -> Optional[Dict[str, Any]]:
        """Execute FHIR bundle on HAPI FHIR server"""
        try:
            execution_result = await self.execution_service.execute_bundle(
                bundle, 
                request_id=request_id,
                validate_first=False,  # Already validated
                force_execution=False
            )
            return execution_result
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to execute FHIR bundle: {e}")
            return None
    
    def _generate_quality_metrics(self, result: FHIRProcessingResult) -> Dict[str, Any]:
        """Generate comprehensive quality metrics"""
        try:
            # Calculate validation success rate
            validation_success_rate = (
                self.validation_success_count / max(self.processing_count, 1) * 100
            )
            
            # Calculate average bundle quality score
            avg_quality_score = (
                sum(self.quality_scores) / max(len(self.quality_scores), 1)
                if self.quality_scores else 0.0
            )
            
            # Calculate average processing time
            avg_processing_time = (
                self.total_processing_time / max(self.processing_count, 1)
            )
            
            return {
                "validation_success_rate": validation_success_rate,
                "validation_target_met": validation_success_rate >= 95.0,
                "average_bundle_quality": avg_quality_score,
                "average_processing_time": avg_processing_time,
                "performance_target_met": avg_processing_time < 2.0,
                "total_processed": self.processing_count,
                "current_bundle_quality": result.validation_results.get("bundle_quality_score", 0.0) if result.validation_results else 0.0,
                "current_processing_time": result.processing_metadata.performance_metrics.get("total_processing_time", 0.0),
                "resource_count": len(result.fhir_resources),
                "bundle_entries": len(result.fhir_bundle.get("entry", [])) if result.fhir_bundle else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to generate quality metrics: {e}")
            return {}
    
    def _prepare_epic4_summary_data(self, result: FHIRProcessingResult) -> Dict[str, Any]:
        """Prepare data for Epic 4 reverse validation and summarization"""
        try:
            # Extract key clinical information for summarization
            summary_data = {
                "patient_summary": {},
                "clinical_orders": [],
                "medications": [],
                "conditions": [],
                "procedures": [],
                "bundle_metadata": {},
                "quality_indicators": {}
            }
            
            # Extract patient information
            if result.nlp_entities and result.nlp_entities.get("patient_info"):
                patient_info = result.nlp_entities["patient_info"]
                summary_data["patient_summary"] = {
                    "age": patient_info.get("age"),
                    "gender": patient_info.get("gender"),
                    "patient_reference": patient_info.get("patient_ref")
                }
            
            # Extract clinical orders for summarization
            if result.nlp_entities:
                summary_data["medications"] = result.nlp_entities.get("medications", [])
                summary_data["conditions"] = result.nlp_entities.get("conditions", [])
                summary_data["procedures"] = result.nlp_entities.get("procedures", [])
            
            # Add bundle metadata
            if result.fhir_bundle:
                summary_data["bundle_metadata"] = {
                    "bundle_id": result.fhir_bundle.get("id"),
                    "bundle_type": result.fhir_bundle.get("type"),
                    "entry_count": len(result.fhir_bundle.get("entry", [])),
                    "timestamp": result.fhir_bundle.get("timestamp")
                }
            
            # Add quality indicators for summary confidence
            if result.validation_results:
                summary_data["quality_indicators"] = {
                    "validation_result": result.validation_results.get("validation_result"),
                    "bundle_quality_score": result.validation_results.get("bundle_quality_score"),
                    "validation_source": result.validation_results.get("validation_source"),
                    "has_errors": len(result.validation_results.get("issues", {}).get("errors", [])) > 0,
                    "has_warnings": len(result.validation_results.get("issues", {}).get("warnings", [])) > 0
                }
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Failed to prepare Epic 4 summary data: {e}")
            return {}
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics"""
        try:
            # Calculate validation success rate
            validation_success_rate = (
                self.validation_success_count / max(self.processing_count, 1) * 100
            )
            
            # Calculate average processing time
            avg_processing_time = (
                self.total_processing_time / max(self.processing_count, 1)
            )
            
            # Get service status
            service_status = {}
            if self.initialized:
                service_status = {
                    "resource_factory": self.resource_factory.initialized if self.resource_factory else False,
                    "bundle_assembler": self.bundle_assembler.initialized if self.bundle_assembler else False,
                    "validation_service": self.validation_service.initialized if self.validation_service else False,
                    "execution_service": self.execution_service.initialized if self.execution_service else False,
                    "failover_manager": self.failover_manager.initialized if self.failover_manager else False
                }
            
            return {
                "pipeline_initialized": self.initialized,
                "service_status": service_status,
                "processing_statistics": {
                    "total_processed": self.processing_count,
                    "validation_success_rate": validation_success_rate,
                    "validation_target_met": validation_success_rate >= 95.0,
                    "average_processing_time": avg_processing_time,
                    "performance_target_met": avg_processing_time < 2.0,
                    "validation_success_count": self.validation_success_count
                },
                "quality_metrics": {
                    "average_bundle_quality": sum(self.quality_scores) / max(len(self.quality_scores), 1) if self.quality_scores else 0.0,
                    "recent_quality_trend": self.quality_scores[-10:] if len(self.quality_scores) >= 10 else self.quality_scores
                },
                "error_tracking": {
                    "recent_error_count": len(self.recent_errors),
                    "common_error_patterns": list(self.error_patterns.keys())[:5]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return {"error": str(e)}


# Global unified pipeline instance
_unified_pipeline = None

async def get_unified_fhir_pipeline() -> UnifiedFHIRPipeline:
    """Get initialized unified FHIR pipeline instance"""
    global _unified_pipeline
    
    if _unified_pipeline is None:
        _unified_pipeline = UnifiedFHIRPipeline()
        await _unified_pipeline.initialize()
    
    return _unified_pipeline