"""
Main NLP Pipeline for Epic 2 Implementation
HIPAA Compliant: Secure medical text processing
Production Ready: Unified entity extraction, RAG, and LLM processing
"""

import logging
from typing import Dict, List, Any, Optional
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .entity_extractor import MedicalEntityExtractor
from .rag_service import RAGService
from .llm_processor import LLMProcessor
from .diagnostic_report_patterns import extract_diagnostic_reports

logger = logging.getLogger(__name__)


class NLPPipeline:
    """Unified NLP pipeline integrating all Epic 2 components"""
    
    def __init__(self):
        self.entity_extractor = MedicalEntityExtractor()
        self.rag_service = RAGService()
        self.llm_processor = LLMProcessor()
        self.initialized = False
        self._executor = ThreadPoolExecutor(max_workers=3)
        
    def initialize(self) -> bool:
        """Initialize all NLP components"""
        try:
            logger.info("Initializing NLP pipeline components...")
            
            # Initialize components in parallel
            entity_init = self.entity_extractor.initialize()
            rag_init = self.rag_service.initialize()
            llm_init = self.llm_processor.initialize()
            
            if not (entity_init and rag_init and llm_init):
                logger.error("Failed to initialize some NLP components")
                return False
            
            self.initialized = True
            logger.info("NLP pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP pipeline: {e}")
            return False
    
    async def process_clinical_text(self, text: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Process clinical text through complete NLP pipeline"""
        
        if not self.initialized:
            if not self.initialize():
                logger.error(f"[{request_id}] NLP processing failed - pipeline not initialized")
                return self._create_error_response("Pipeline not initialized")
        
        start_time = time.time()
        
        try:
            logger.info(f"[{request_id}] Starting NLP pipeline processing")
            
            # Stage 1: Entity Extraction
            entities = await self._extract_entities_async(text, request_id)
            
            # Stage 2: Parallel Processing - RAG Enhancement, LLM processing, and DiagnosticReport extraction
            enhanced_entities_task = self._enhance_entities_async(entities, request_id)
            structured_output_task = self._generate_structured_output_async(text, entities, request_id)
            diagnostic_reports_task = self._extract_diagnostic_reports_async(text, request_id)

            # Wait for all to complete
            enhanced_entities, structured_output, diagnostic_reports = await asyncio.gather(
                enhanced_entities_task,
                structured_output_task,
                diagnostic_reports_task
            )
            
            # Compile final response
            total_time = time.time() - start_time
            
            response = {
                "status": "completed",
                "processing_time_ms": total_time * 1000,
                "extracted_entities": {
                    "entities": self._format_entities_for_response(entities),
                    "enhanced_entities": enhanced_entities,
                    "entity_summary": self._generate_entity_summary(entities),
                    "status": "completed"
                },
                "structured_output": structured_output,
                "diagnostic_reports": diagnostic_reports,
                "terminology_mappings": self._extract_terminology_mappings(enhanced_entities),
                "pipeline_metrics": {
                    "total_entities": len(entities),
                    "processing_stages": 3,
                    "performance_score": self._calculate_performance_score(total_time)
                }
            }
            
            logger.info(f"[{request_id}] NLP pipeline completed in {total_time:.3f}s")
            return response
            
        except Exception as e:
            logger.error(f"[{request_id}] NLP pipeline processing failed: {e}")
            return self._create_error_response(str(e))
    
    async def _extract_entities_async(self, text: str, request_id: Optional[str]) -> List[Any]:
        """Async wrapper for entity extraction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.entity_extractor.extract_entities,
            text,
            request_id
        )
    
    async def _enhance_entities_async(self, entities: List[Any], request_id: Optional[str]) -> List[Dict[str, Any]]:
        """Async wrapper for RAG enhancement"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.rag_service.enhance_entities,
            entities,
            request_id
        )
    
    async def _generate_structured_output_async(self, text: str, entities: List[Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Async wrapper for LLM structured output"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.llm_processor.process_clinical_text,
            text,
            entities,
            request_id
        )
    
    def _format_entities_for_response(self, entities: List[Any]) -> List[Dict[str, Any]]:
        """Format entities for API response"""
        
        formatted_entities = []
        
        for entity in entities:
            formatted_entity = {
                "text": entity.text,
                "type": entity.entity_type.value,
                "start_char": entity.start_char,
                "end_char": entity.end_char,
                "confidence": entity.confidence,
                "source": entity.source,
                "attributes": entity.attributes
            }
            formatted_entities.append(formatted_entity)
        
        return formatted_entities
    
    def _generate_entity_summary(self, entities: List[Any]) -> Dict[str, Any]:
        """Generate summary statistics for extracted entities"""
        
        if not entities:
            return {"total": 0, "by_type": {}, "confidence_avg": 0.0}
        
        by_type = {}
        total_confidence = 0
        
        for entity in entities:
            entity_type = entity.entity_type.value
            by_type[entity_type] = by_type.get(entity_type, 0) + 1
            total_confidence += entity.confidence
        
        return {
            "total": len(entities),
            "by_type": by_type,
            "confidence_avg": total_confidence / len(entities),
            "high_confidence_count": sum(1 for e in entities if e.confidence > 0.7)
        }
    
    def _extract_terminology_mappings(self, enhanced_entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract terminology mappings from enhanced entities"""
        
        mappings = {
            "medications": [],
            "lab_tests": [],
            "conditions": [],
            "procedures": []
        }
        
        for entity in enhanced_entities:
            entity_type = entity.get("entity_type", "unknown")
            medical_codes = entity.get("medical_codes", [])
            
            if medical_codes:
                mapping_type = self._map_entity_type_to_terminology(entity_type)
                if mapping_type in mappings:
                    mappings[mapping_type].append({
                        "text": entity.get("text", ""),
                        "codes": medical_codes,
                        "standardized_term": entity.get("standardized_term")
                    })
        
        return mappings
    
    def _map_entity_type_to_terminology(self, entity_type: str) -> str:
        """Map entity type to terminology category"""
        
        mapping = {
            "medication": "medications",
            "lab_test": "lab_tests",
            "condition": "conditions",
            "procedure": "procedures"
        }
        
        return mapping.get(entity_type, "other")
    
    def _calculate_performance_score(self, processing_time: float) -> float:
        """Calculate performance score based on processing time and quality"""
        
        # Target: <2s for excellent performance
        if processing_time < 1.0:
            return 1.0  # Excellent
        elif processing_time < 2.0:
            return 0.8  # Good
        elif processing_time < 3.0:
            return 0.6  # Acceptable
        else:
            return 0.4  # Needs optimization
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        
        return {
            "status": "error",
            "error": error_message,
            "processing_time_ms": 0,
            "extracted_entities": {
                "entities": [],
                "enhanced_entities": [],
                "entity_summary": {"total": 0, "by_type": {}, "confidence_avg": 0.0},
                "status": "failed"
            },
            "structured_output": {
                "structured_output": {},
                "method": "fallback",
                "status": "failed"
            },
            "terminology_mappings": {
                "medications": [],
                "lab_tests": [],
                "conditions": [],
                "procedures": []
            },
            "pipeline_metrics": {
                "total_entities": 0,
                "processing_stages": 0,
                "performance_score": 0.0
            }
        }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        
        return {
            "initialized": self.initialized,
            "components": {
                "entity_extractor": True,
                "rag_service": self.rag_service.initialized,
                "llm_processor": self.llm_processor.initialized
            },
            "knowledge_base_stats": self.rag_service.get_knowledge_stats() if self.rag_service.initialized else {},
            "processor_status": self.llm_processor.get_processor_status() if self.llm_processor.initialized else {}
        }
    
    def shutdown(self):
        """Shutdown pipeline and cleanup resources"""
        try:
            self._executor.shutdown(wait=True)
            logger.info("NLP pipeline shutdown completed")
        except Exception as e:
            logger.error(f"Error during pipeline shutdown: {e}")

    async def _extract_diagnostic_reports_async(self, text: str, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract diagnostic reports from clinical text asynchronously"""
        try:
            logger.debug(f"[{request_id}] Starting diagnostic report extraction")
            start_time = time.time()

            # Run diagnostic report extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            diagnostic_reports = await loop.run_in_executor(
                self._executor,
                extract_diagnostic_reports,
                text
            )

            extraction_time = time.time() - start_time
            logger.debug(f"[{request_id}] Diagnostic report extraction completed in {extraction_time*1000:.1f}ms, found {len(diagnostic_reports)} reports")

            return diagnostic_reports

        except Exception as e:
            logger.error(f"[{request_id}] Diagnostic report extraction failed: {e}")
            return []  # Return empty list on failure to avoid breaking pipeline


# Global pipeline instance
nlp_pipeline = NLPPipeline()


async def get_nlp_pipeline() -> NLPPipeline:
    """Get initialized NLP pipeline instance"""
    if not nlp_pipeline.initialized:
        nlp_pipeline.initialize()
    return nlp_pipeline