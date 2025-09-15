"""
Epic 4: Adaptive FHIR Bundle Summarization
Multi-tier processing architecture for cost-optimized clinical summarization
"""

from .fhir_bundle_summarizer import FHIRBundleSummarizer

# Alias for backward compatibility
SummarizationService = FHIRBundleSummarizer
from .resource_summarizer_registry import ResourceSummarizerRegistry, BaseResourceSummarizer
from .bundle_analyzer import BundleAnalyzer
from .monitoring import ProductionMonitoringMixin

from .models import (
    ClinicalSummary,
    ClinicalOrder,
    QualityIndicators,
    BundleAnalysis,
    ProcessingTier,
    SummarizationEvent,
    TierUsageAnalytics
)

__all__ = [
    # Main components
    "FHIRBundleSummarizer",
    "SummarizationService",  # Backward compatibility alias
    "ResourceSummarizerRegistry",
    "BaseResourceSummarizer",
    "BundleAnalyzer",
    "ProductionMonitoringMixin",
    
    # Data models
    "ClinicalSummary",
    "ClinicalOrder",
    "QualityIndicators", 
    "BundleAnalysis",
    "ProcessingTier",
    "SummarizationEvent",
    "TierUsageAnalytics",
]

# Version information
__version__ = "4.1.0"
__epic__ = "Epic 4: Adaptive FHIR Bundle Summarization"
__story__ = "Story 4.1: Adaptive FHIR Bundle Summarizer Framework"