"""
Shared models and enums for safety risk scoring.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class RiskLevel(Enum):
    """Overall risk level classification."""

    MINIMAL = "minimal"  # 0-20: Routine care
    LOW = "low"  # 21-40: Standard monitoring
    MODERATE = "moderate"  # 41-60: Enhanced monitoring
    HIGH = "high"  # 61-80: Close monitoring required
    CRITICAL = "critical"  # 81-100: Immediate intervention


class AlertSeverity(Enum):
    """Safety alert severity levels."""

    INFO = "info"  # Informational only
    WARNING = "warning"  # Attention required
    ALERT = "alert"  # Action recommended
    URGENT = "urgent"  # Immediate action required


@dataclass
class SafetyAlert:
    """Safety alert model."""

    alert_id: str
    severity: AlertSeverity
    category: str
    title: str
    description: str
    affected_medications: List[str]
    required_actions: List[str]
    timeline: str
    escalation_criteria: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "affected_medications": self.affected_medications,
            "required_actions": self.required_actions,
            "timeline": self.timeline,
            "escalation_criteria": self.escalation_criteria,
        }


@dataclass
class SafetyRiskScore:
    """Comprehensive safety risk score."""

    overall_score: float
    risk_level: RiskLevel
    contributing_factors: Dict[str, float]
    risk_components: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    monitoring_requirements: List[str]
    escalation_triggers: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "risk_level": self.risk_level.value,
            "contributing_factors": self.contributing_factors,
            "risk_components": self.risk_components,
            "recommendations": self.recommendations,
            "monitoring_requirements": self.monitoring_requirements,
            "escalation_triggers": self.escalation_triggers,
        }
