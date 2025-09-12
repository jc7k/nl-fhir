"""
Epic 4 Story 4.1: Adaptive FHIR Bundle Summarizer Framework
Main orchestrator for cost-optimized, multi-tier clinical summarization
"""

import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from .models import (
    ClinicalSummary, 
    BundleAnalysis, 
    ProcessingTier, 
    SummarizationEvent,
    QualityIndicators,
    ClinicalOrder,
    MinimalSummary
)
from .resource_summarizer_registry import ResourceSummarizerRegistry
from .bundle_analyzer import BundleAnalyzer
from .monitoring import ProductionMonitoringMixin


class FHIRBundleSummarizer:
    """
    Main orchestrator for adaptive FHIR bundle summarization
    Routes bundles through optimal processing tiers based on content analysis
    """
    
    def __init__(self):
        self.resource_registry = ResourceSummarizerRegistry()
        self.bundle_analyzer = BundleAnalyzer()
        self.monitoring = ProductionMonitoringMixin()
        
        # Lazy-loaded tier processors (will be implemented in subsequent stories)
        self._generic_engine = None
        self._llm_service = None
    
    async def summarize_bundle(self, 
                             fhir_bundle: Dict[str, Any], 
                             role: str = "physician",
                             request_id: Optional[str] = None,
                             context: Optional[Dict[str, Any]] = None) -> ClinicalSummary:
        """
        Main entry point for adaptive bundle summarization
        Routes through appropriate processing tier based on content analysis
        """
        start_time = time.time()
        request_id = request_id or str(uuid.uuid4())
        bundle_id = fhir_bundle.get('id', f"bundle-{request_id}")
        
        try:
            # Step 1: Analyze bundle composition and select processing tier
            analysis = await self._analyze_bundle_composition(fhir_bundle)
            analysis_time = (time.time() - start_time) * 1000
            
            processing_start = time.time()
            
            # Step 2: Route to appropriate processing tier
            if analysis.recommended_tier == ProcessingTier.RULE_BASED:
                summary = await self._process_with_rule_based(fhir_bundle, role, analysis)
            elif analysis.recommended_tier == ProcessingTier.GENERIC_TEMPLATE:
                summary = await self._process_with_generic_template(fhir_bundle, role, analysis)
            elif analysis.recommended_tier == ProcessingTier.LLM_FALLBACK:
                summary = await self._process_with_llm_fallback(fhir_bundle, role, analysis)
            else:
                summary = await self._process_emergency_fallback(fhir_bundle, role, analysis)
            
            processing_time = (time.time() - processing_start) * 1000
            total_time = (time.time() - start_time) * 1000
            
            # Step 3: Log comprehensive processing event
            event = SummarizationEvent(
                timestamp=datetime.now(),
                request_id=request_id,
                bundle_id=bundle_id,
                resource_types=analysis.resource_types,
                resource_count=analysis.resource_count,
                bundle_complexity_score=analysis.complexity_score,
                has_rare_resources=analysis.has_rare_resources,
                tier_selected=analysis.recommended_tier,
                analysis_time_ms=analysis_time,
                processing_time_ms=processing_time,
                total_time_ms=total_time,
                output_quality_score=summary.confidence_score,
                server_instance="fhir-summarizer-1",  # TODO: get from config
                api_version="4.1.0",
                user_role=role,
                specialty_context=analysis.specialty_context
            )
            
            await self.monitoring.log_summarization_event(event)
            
            return summary
            
        except Exception as e:
            # Handle processing errors with comprehensive logging
            total_time = (time.time() - start_time) * 1000
            
            error_event = SummarizationEvent(
                timestamp=datetime.now(),
                request_id=request_id,
                bundle_id=bundle_id,
                resource_types=[],
                resource_count=0,
                bundle_complexity_score=0.0,
                has_rare_resources=False,
                tier_selected=ProcessingTier.EMERGENCY_FALLBACK,
                analysis_time_ms=0.0,
                processing_time_ms=0.0,
                total_time_ms=total_time,
                server_instance="fhir-summarizer-1",
                api_version="4.1.0",
                user_role=role,
                error_occurred=True,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            await self.monitoring.log_summarization_event(error_event)
            
            # Return minimal fallback summary
            return await self._create_error_summary(fhir_bundle, str(e))
    
    async def _analyze_bundle_composition(self, fhir_bundle: Dict[str, Any]) -> BundleAnalysis:
        """Analyze bundle to determine optimal processing tier"""
        return await self.bundle_analyzer.analyze_bundle(fhir_bundle, self.resource_registry)
    
    async def _process_with_rule_based(self, 
                                     fhir_bundle: Dict[str, Any], 
                                     role: str,
                                     analysis: BundleAnalysis) -> ClinicalSummary:
        """Process bundle using rule-based summarizers (Tier 1)"""
        
        entries = fhir_bundle.get("entry", [])
        clinical_orders = []
        
        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            # Get appropriate rule-based summarizer
            summarizer = self.resource_registry.get_summarizer(resource_type)
            if summarizer:
                try:
                    order = await summarizer.summarize_resource(resource, role)
                    clinical_orders.append(order)
                except Exception as e:
                    # Individual resource processing error - create fallback order
                    fallback_order = ClinicalOrder(
                        order_type=resource_type or "unknown",
                        description=f"Clinical order of type {resource_type} - processing error occurred",
                        processing_tier=ProcessingTier.RULE_BASED,
                        confidence_score=0.3,
                        safety_alerts=[f"Processing error: {str(e)}"]
                    )
                    clinical_orders.append(fallback_order)
        
        # Generate patient context from bundle
        patient_context = self._extract_patient_context(fhir_bundle, "rule_based")
        
        return ClinicalSummary(
            summary_type="comprehensive" if len(clinical_orders) > 3 else "medication_only",
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=min(0.95, analysis.confidence_score),
            patient_context=patient_context,
            primary_orders=clinical_orders,
            quality_indicators=QualityIndicators(
                completeness_score=0.95,
                clinical_accuracy_confidence=0.95,
                terminology_consistency=1.0,  # Rule-based is deterministic
                missing_critical_information=False,
                processing_confidence=analysis.confidence_score
            ),
            processing_metadata={
                "tier": "rule_based",
                "rule_coverage": analysis.rule_based_coverage,
                "processing_method": "deterministic_rules"
            }
        )
    
    async def _process_with_generic_template(self, 
                                           fhir_bundle: Dict[str, Any], 
                                           role: str,
                                           analysis: BundleAnalysis) -> ClinicalSummary:
        """Process bundle using generic template engine (Tier 2)"""
        # Placeholder - will be implemented in Story 4.4
        # For now, return a minimal summary indicating template processing would be used
        
        patient_context = self._extract_patient_context(fhir_bundle, "generic_template")
        
        return ClinicalSummary(
            summary_type="complex",
            processing_tier=ProcessingTier.GENERIC_TEMPLATE,
            confidence_score=0.8,
            patient_context=patient_context,
            primary_orders=[
                ClinicalOrder(
                    order_type="template_placeholder",
                    description="Generic template processing - implementation pending Story 4.4",
                    processing_tier=ProcessingTier.GENERIC_TEMPLATE,
                    confidence_score=0.8
                )
            ],
            quality_indicators=QualityIndicators(
                completeness_score=0.8,
                clinical_accuracy_confidence=0.8,
                terminology_consistency=0.9,
                missing_critical_information=False,
                processing_confidence=analysis.confidence_score
            ),
            fallback_information="Generic template engine not yet implemented - Story 4.4 pending"
        )
    
    async def _process_with_llm_fallback(self, 
                                       fhir_bundle: Dict[str, Any], 
                                       role: str,
                                       analysis: BundleAnalysis) -> ClinicalSummary:
        """Process complex bundle using LLM integration (Tier 3)"""
        # Placeholder - will be implemented in Story 4.4
        # For now, return a summary indicating LLM processing would be used
        
        patient_context = self._extract_patient_context(fhir_bundle, "llm_fallback")
        
        return ClinicalSummary(
            summary_type="complex",
            processing_tier=ProcessingTier.LLM_FALLBACK,
            confidence_score=0.9,
            patient_context=patient_context,
            primary_orders=[
                ClinicalOrder(
                    order_type="llm_placeholder",
                    description="LLM processing - implementation pending Story 4.4",
                    processing_tier=ProcessingTier.LLM_FALLBACK,
                    confidence_score=0.9
                )
            ],
            quality_indicators=QualityIndicators(
                completeness_score=0.9,
                clinical_accuracy_confidence=0.85,
                terminology_consistency=0.8,
                missing_critical_information=False,
                processing_confidence=analysis.confidence_score
            ),
            fallback_information="LLM integration not yet implemented - Story 4.4 pending"
        )
    
    async def _process_emergency_fallback(self, 
                                        fhir_bundle: Dict[str, Any], 
                                        role: str,
                                        analysis: BundleAnalysis) -> ClinicalSummary:
        """Emergency fallback processing for system failures"""
        entries = fhir_bundle.get("entry", [])
        resource_types = [entry.get("resource", {}).get("resourceType") 
                         for entry in entries if entry.get("resource", {}).get("resourceType")]
        
        fallback_orders = [
            ClinicalOrder(
                order_type=rt,
                description=f"Clinical order of type {rt} - detailed processing unavailable",
                processing_tier=ProcessingTier.EMERGENCY_FALLBACK,
                confidence_score=0.3,
                safety_alerts=["Emergency fallback processing - manual review recommended"]
            ) for rt in set(resource_types)
        ]
        
        return ClinicalSummary(
            summary_type="minimal",
            processing_tier=ProcessingTier.EMERGENCY_FALLBACK,
            confidence_score=0.3,
            patient_context="Bundle processing encountered technical issues - manual review recommended",
            primary_orders=fallback_orders,
            clinical_alerts=["Emergency fallback processing active - manual review recommended"],
            quality_indicators=QualityIndicators(
                completeness_score=0.3,
                clinical_accuracy_confidence=0.3,
                terminology_consistency=0.5,
                missing_critical_information=True,
                processing_confidence=0.3
            ),
            fallback_information="Emergency fallback active - all advanced processing tiers unavailable"
        )
    
    def _extract_patient_context(self, fhir_bundle: Dict[str, Any], processing_method: str) -> str:
        """Extract non-PHI patient context information"""
        entries = fhir_bundle.get("entry", [])
        resource_count = len(entries)
        resource_types = set(entry.get("resource", {}).get("resourceType") 
                           for entry in entries 
                           if entry.get("resource", {}).get("resourceType"))
        
        context_parts = [
            f"Clinical bundle containing {resource_count} resources",
            f"Resource types: {', '.join(sorted(resource_types))}",
            f"Processed using: {processing_method.replace('_', ' ')}"
        ]
        
        return " | ".join(context_parts)
    
    async def _create_error_summary(self, fhir_bundle: Dict[str, Any], error_message: str) -> ClinicalSummary:
        """Create minimal summary for error conditions"""
        entries = fhir_bundle.get("entry", [])
        
        return ClinicalSummary(
            summary_type="minimal",
            processing_tier=ProcessingTier.EMERGENCY_FALLBACK,
            confidence_score=0.1,
            patient_context="Processing error occurred - bundle analysis failed",
            primary_orders=[
                ClinicalOrder(
                    order_type="error",
                    description="Bundle processing failed - manual review required",
                    processing_tier=ProcessingTier.EMERGENCY_FALLBACK,
                    confidence_score=0.1,
                    safety_alerts=[f"Processing error: {error_message}"]
                )
            ],
            clinical_alerts=["Critical processing error - immediate manual review required"],
            quality_indicators=QualityIndicators(
                completeness_score=0.1,
                clinical_accuracy_confidence=0.1,
                terminology_consistency=0.1,
                missing_critical_information=True,
                processing_confidence=0.1
            ),
            fallback_information=f"Error processing bundle: {error_message}"
        )