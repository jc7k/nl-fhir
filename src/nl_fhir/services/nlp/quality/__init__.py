"""
Quality scoring and validation for NLP results
Handles confidence scoring, validation, and quality assessment.
"""

from .quality_scorer import QualityScorer
from .escalation_manager import EscalationManager

__all__ = ["QualityScorer", "EscalationManager"]