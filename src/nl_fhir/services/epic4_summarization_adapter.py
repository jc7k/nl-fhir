"""
Epic 4 Backward Compatibility Adapter
Provides compatibility between old SummarizationService interface and new Epic 4 architecture
"""

import asyncio
from typing import Dict, Any, Optional

from .summarization import FHIRBundleSummarizer
from datetime import datetime


class Epic4SummarizationAdapter:
    """
    Adapter to maintain backward compatibility with existing SummarizationService interface
    while using the new Epic 4 adaptive architecture under the hood
    """
    
    def __init__(self):
        self.epic4_summarizer = FHIRBundleSummarizer()
    
    async def async_summarize(self, bundle: Dict[str, Any], role: str = "clinician", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Async interface for use within async contexts (like FastAPI)
        """
        # Use Epic 4 adaptive summarization
        clinical_summary = await self.epic4_summarizer.summarize_bundle(
            fhir_bundle=bundle,
            role=role,
            context=context
        )
        
        # Convert Epic 4 ClinicalSummary back to old format for compatibility
        return self._convert_to_legacy_format(clinical_summary, bundle)
    
    def summarize(self, bundle: Dict[str, Any], role: str = "clinician", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Backward-compatible synchronous interface
        Note: This will raise an error if called from within an async context
        """
        try:
            # Check if we're already in an async context
            asyncio.get_running_loop()
            raise RuntimeError("Cannot call synchronous summarize() from async context. Use async_summarize() instead.")
        except RuntimeError as e:
            if "async context" in str(e):
                raise e
            # No event loop is running, we can create one
            return asyncio.run(self.async_summarize(bundle, role, context))
    
    def _convert_to_legacy_format(self, clinical_summary, original_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Epic 4 ClinicalSummary to legacy SummarizationService format"""
        
        # Generate human-readable summary from clinical orders
        summary_lines = []
        
        if clinical_summary.patient_context:
            summary_lines.append(f"Patient Context: {clinical_summary.patient_context}")
        
        for order in clinical_summary.primary_orders:
            summary_lines.append(f"• {order.description}")
            
            if order.clinical_rationale:
                summary_lines.append(f"  Rationale: {order.clinical_rationale}")
            
            if order.safety_alerts:
                for alert in order.safety_alerts:
                    summary_lines.append(f"  ⚠️ Safety Alert: {alert}")
        
        if clinical_summary.supporting_information:
            summary_lines.append(f"Additional Information: {clinical_summary.supporting_information}")
        
        human_readable_summary = "\n".join(summary_lines)
        
        # Generate bundle summary statistics (legacy format)
        entries = original_bundle.get("entry", [])
        resource_types = [e.get("resource", {}).get("resourceType") for e in entries]
        resource_counts = {}
        for rt in resource_types:
            if rt:
                resource_counts[rt] = resource_counts.get(rt, 0) + 1
        
        # Handle processing_tier which might be enum or string
        processing_tier_value = clinical_summary.processing_tier
        if hasattr(processing_tier_value, 'value'):
            processing_tier_value = processing_tier_value.value
        
        bundle_summary = {
            "total_resources": len(entries),
            "resource_types": list(resource_counts.keys()),
            "resource_counts": resource_counts,
            "processing_tier": processing_tier_value,
            "complexity_score": getattr(clinical_summary.processing_metadata, 'bundle_complexity_score', 'unknown'),
        }
        
        # Generate confidence indicators (legacy format)
        confidence_indicators = {
            "overall_confidence": clinical_summary.confidence_score,
            "processing_method": processing_tier_value,  # Use the same value as above
            "quality_score": clinical_summary.quality_indicators.clinical_accuracy_confidence,
            "completeness": clinical_summary.quality_indicators.completeness_score,
            "epic4_enabled": True,
            "adaptive_architecture": True
        }
        
        return {
            "human_readable_summary": human_readable_summary,
            "bundle_summary": bundle_summary,
            "confidence_indicators": confidence_indicators
        }