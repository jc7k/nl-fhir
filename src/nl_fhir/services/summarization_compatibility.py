"""
Compatibility layer for transitioning from old SummarizationService to new FHIRBundleSummarizer
REFACTOR-008: Temporary compatibility wrapper
"""

import asyncio
from typing import Dict, Any, Optional
from .summarization import FHIRBundleSummarizer


class LegacySummarizationWrapper:
    """
    Compatibility wrapper to maintain API compatibility during refactoring.
    Wraps the new async FHIRBundleSummarizer to provide the old synchronous interface.
    """

    def __init__(self):
        self.modern_summarizer = FHIRBundleSummarizer()

    def summarize(self, bundle: Dict[str, Any], role: str = "clinician", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Legacy synchronous interface that wraps the new async implementation.
        Converts the modern ClinicalSummary response back to the old dictionary format.
        """
        try:
            # Run the async method in sync context
            if asyncio.get_event_loop().is_running():
                # If we're already in an async context, we need to handle this differently
                # For now, return a basic summary to avoid blocking
                return self._create_fallback_summary(bundle, role, context)
            else:
                # We can safely create a new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    modern_result = loop.run_until_complete(
                        self.modern_summarizer.summarize_bundle(bundle, role, context=context)
                    )
                    return self._convert_modern_to_legacy_format(modern_result)
                finally:
                    loop.close()
        except Exception as e:
            # Fallback to basic summary on any error
            return self._create_fallback_summary(bundle, role, context)

    def _convert_modern_to_legacy_format(self, modern_result) -> Dict[str, Any]:
        """Convert new ClinicalSummary object to old dictionary format"""
        try:
            return {
                "human_readable_summary": modern_result.human_readable_summary,
                "bundle_summary": {
                    "total_entries": getattr(modern_result.bundle_analysis, 'total_entries', 0),
                    "resource_counts": getattr(modern_result.bundle_analysis, 'resource_counts', {}),
                    "recognized_types": list(getattr(modern_result.bundle_analysis, 'resource_counts', {}).keys()),
                },
                "confidence_indicators": {
                    "method": modern_result.processing_tier.value if hasattr(modern_result.processing_tier, 'value') else str(modern_result.processing_tier),
                    "deterministic": True,
                    "role": modern_result.target_audience,
                    "quality": {
                        "coverage_score": getattr(modern_result.quality_indicators, 'coverage_score', 1.0),
                        "coherence_score": getattr(modern_result.quality_indicators, 'coherence_score', 0.9),
                    },
                },
            }
        except Exception:
            # If conversion fails, return the object as-is and let the caller handle it
            return {
                "human_readable_summary": str(modern_result),
                "bundle_summary": {"total_entries": 0, "resource_counts": {}, "recognized_types": []},
                "confidence_indicators": {"method": "fallback", "deterministic": True, "role": "clinician"},
            }

    def _create_fallback_summary(self, bundle: Dict[str, Any], role: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a basic fallback summary when modern service fails"""
        entries = bundle.get("entry", []) or []
        resource_types = [e.get("resource", {}).get("resourceType") for e in entries if isinstance(e, dict)]
        resource_counts = {}
        for rt in resource_types:
            if rt:
                resource_counts[rt] = resource_counts.get(rt, 0) + 1

        return {
            "human_readable_summary": f"FHIR Bundle with {len(entries)} entries. Resource types: {', '.join(resource_counts.keys()) or 'None'}.",
            "bundle_summary": {
                "total_entries": len(entries),
                "resource_counts": resource_counts,
                "recognized_types": list(resource_counts.keys()),
            },
            "confidence_indicators": {
                "method": "fallback",
                "deterministic": True,
                "role": role,
                "quality": {
                    "coverage_score": 0.8,
                    "coherence_score": 0.7,
                },
            },
        }


# Alias for backward compatibility
SummarizationService = LegacySummarizationWrapper