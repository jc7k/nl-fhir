"""
Epic 4 Story 4.1: Adaptive FHIR Bundle Summarizer Framework
Main orchestrator for cost-optimized, multi-tier clinical summarization
"""

import time
import uuid
from typing import Dict, Any, Optional, List
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
        
        # Lazy-load tier processors so new engines can be attached without increasing startup cost
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
            
            # Step 2: Process with 100% rule-based coverage (Tier 2/3 removed)
            # All bundles now route to enhanced rule-based processing with 100% FHIR coverage
            summary = await self._process_with_rule_based(fhir_bundle, role, analysis)
            
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
                server_instance="fhir-summarizer-1",  # Use explicit identifier until deployment metadata is exposed via configuration
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
                tier_selected=ProcessingTier.RULE_BASED,
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
        """Process bundle using rule-based summarizers (Tier 1) - 100% FHIR coverage"""

        entries = fhir_bundle.get("entry", [])
        clinical_orders = []
        processing_errors = []

        # Process each resource in the bundle
        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

            # Get appropriate rule-based summarizer (100% coverage guaranteed)
            summarizer = self.resource_registry.get_summarizer(resource_type)
            try:
                order = await summarizer.summarize_resource(resource, role)
                clinical_orders.append(order)
            except Exception as e:
                # Track processing errors but continue with fallback
                processing_errors.append(f"{resource_type}: {str(e)}")
                fallback_order = ClinicalOrder(
                    order_type=resource_type or "unknown",
                    description=f"Clinical order of type {resource_type} - processing error occurred",
                    processing_tier=ProcessingTier.RULE_BASED,
                    confidence_score=0.3,
                    safety_alerts=[f"Processing error: {str(e)}"]
                )
                clinical_orders.append(fallback_order)

        # Create comprehensive bundle-level summary
        bundle_summary = self._create_comprehensive_bundle_summary(clinical_orders, fhir_bundle, role)

        # Calculate summary confidence based on successful processing
        success_rate = (len(clinical_orders) - len(processing_errors)) / max(1, len(clinical_orders))
        summary_confidence = min(0.95, analysis.confidence_score * success_rate)

        return ClinicalSummary(
            summary_type=self._determine_summary_type(clinical_orders),
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=summary_confidence,
            patient_context=bundle_summary["patient_context"],
            primary_orders=clinical_orders,
            clinical_alerts=bundle_summary["clinical_alerts"],
            quality_indicators=QualityIndicators(
                completeness_score=success_rate * 0.95,
                clinical_accuracy_confidence=0.95,
                terminology_consistency=1.0,  # Rule-based is deterministic
                missing_critical_information=len(processing_errors) > 0,
                processing_confidence=summary_confidence
            ),
            processing_metadata={
                "tier": "rule_based",
                "rule_coverage": 1.0,  # 100% coverage with fallback
                "processing_method": "comprehensive_deterministic_rules",
                "resources_processed": len(clinical_orders),
                "processing_errors": processing_errors,
                "summary_composition": bundle_summary["composition_details"]
            }
        )
    
    
    
    def _create_comprehensive_bundle_summary(self,
                                            clinical_orders: List[ClinicalOrder],
                                            fhir_bundle: Dict[str, Any],
                                            role: str) -> Dict[str, Any]:
        """Create comprehensive bundle-level summary with clinical context"""

        # Categorize orders by type for intelligent summary composition
        order_categories = {}
        for order in clinical_orders:
            category = self._categorize_clinical_order(order.order_type)
            if category not in order_categories:
                order_categories[category] = []
            order_categories[category].append(order)

        # Extract patient demographic info (non-PHI)
        patient_info = self._extract_patient_demographics(fhir_bundle)

        # Build comprehensive clinical context
        clinical_context_parts = []

        if patient_info:
            clinical_context_parts.append(f"Patient: {patient_info}")

        # Medication summary
        if "medication" in order_categories:
            med_count = len(order_categories["medication"])
            clinical_context_parts.append(f"{med_count} medication{'s' if med_count != 1 else ''} prescribed")

        # Diagnostic summary
        if "diagnostic" in order_categories:
            diag_count = len(order_categories["diagnostic"])
            clinical_context_parts.append(f"{diag_count} diagnostic test{'s' if diag_count != 1 else ''} ordered")

        # Procedure summary
        if "procedure" in order_categories:
            proc_count = len(order_categories["procedure"])
            clinical_context_parts.append(f"{proc_count} procedure{'s' if proc_count != 1 else ''} scheduled")

        # Condition summary
        if "condition" in order_categories:
            cond_count = len(order_categories["condition"])
            clinical_context_parts.append(f"{cond_count} condition{'s' if cond_count != 1 else ''} documented")

        # Other clinical items
        other_categories = set(order_categories.keys()) - {"medication", "diagnostic", "procedure", "condition"}
        if other_categories:
            other_count = sum(len(order_categories[cat]) for cat in other_categories)
            clinical_context_parts.append(f"{other_count} additional clinical item{'s' if other_count != 1 else ''}")

        patient_context = " | ".join(clinical_context_parts) if clinical_context_parts else "Clinical bundle processed"

        # Generate clinical alerts
        clinical_alerts = []

        # Check for safety concerns
        high_risk_orders = [order for order in clinical_orders if order.safety_alerts]
        if high_risk_orders:
            clinical_alerts.append(f"Safety review required for {len(high_risk_orders)} item(s)")

        # Check for low confidence orders
        low_confidence_orders = [order for order in clinical_orders if order.confidence_score < 0.7]
        if low_confidence_orders:
            clinical_alerts.append(f"Manual review recommended for {len(low_confidence_orders)} item(s)")

        # Composition details for metadata
        composition_details = {
            "total_orders": len(clinical_orders),
            "order_categories": {cat: len(orders) for cat, orders in order_categories.items()},
            "patient_info_available": bool(patient_info),
            "clinical_alerts_generated": len(clinical_alerts),
            "role_based_context": role
        }

        return {
            "patient_context": patient_context,
            "clinical_alerts": clinical_alerts,
            "composition_details": composition_details
        }

    def _categorize_clinical_order(self, order_type: str) -> str:
        """Categorize clinical orders for intelligent summary composition"""
        order_type_lower = order_type.lower()

        if any(med_type in order_type_lower for med_type in ['medication', 'drug', 'prescription']):
            return "medication"
        elif any(diag_type in order_type_lower for diag_type in ['observation', 'diagnostic', 'lab', 'test']):
            return "diagnostic"
        elif any(proc_type in order_type_lower for proc_type in ['procedure', 'surgery', 'operation']):
            return "procedure"
        elif any(cond_type in order_type_lower for cond_type in ['condition', 'diagnosis', 'problem']):
            return "condition"
        else:
            return "other"

    def _extract_patient_demographics(self, fhir_bundle: Dict[str, Any]) -> Optional[str]:
        """Extract non-PHI patient demographic information"""
        entries = fhir_bundle.get("entry", [])

        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                # Extract age range and gender only (non-PHI)
                gender = resource.get("gender", "unknown gender")
                birth_date = resource.get("birthDate")

                if birth_date:
                    try:
                        from datetime import datetime
                        birth_year = int(birth_date.split("-")[0])
                        current_year = datetime.now().year
                        age = current_year - birth_year

                        # Age range for privacy
                        if age < 18:
                            age_range = "pediatric"
                        elif age < 30:
                            age_range = "young adult"
                        elif age < 50:
                            age_range = "adult"
                        elif age < 70:
                            age_range = "middle-aged adult"
                        else:
                            age_range = "senior adult"

                        return f"{age_range}, {gender}"
                    except:
                        return gender
                else:
                    return gender

        return None

    def _determine_summary_type(self, clinical_orders: List[ClinicalOrder]) -> str:
        """Determine appropriate summary type based on order composition"""
        order_count = len(clinical_orders)

        if order_count == 0:
            return "minimal"
        elif order_count == 1:
            return "minimal"
        elif order_count <= 3:
            return "comprehensive"
        elif order_count <= 8:
            return "comprehensive"
        else:
            return "complex"

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
        """Create minimal summary for critical error conditions"""
        entries = fhir_bundle.get("entry", [])

        return ClinicalSummary(
            summary_type="emergency",
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.1,
            patient_context="Critical processing error occurred - bundle analysis failed",
            primary_orders=[
                ClinicalOrder(
                    order_type="system_error",
                    description="Bundle processing failed due to system error - manual review required",
                    processing_tier=ProcessingTier.RULE_BASED,
                    confidence_score=0.1,
                    safety_alerts=[f"Critical processing error: {error_message}"]
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
            fallback_information=f"Critical error processing bundle: {error_message}"
        )