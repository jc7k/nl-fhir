"""
Shared dosage domain models used across dosage safety components.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class DosageViolationSeverity(Enum):
    """Dosage violation severity levels"""

    CRITICAL = "critical"  # Potentially life-threatening
    HIGH = "high"  # Serious adverse effects likely
    MODERATE = "moderate"  # Monitoring required
    LOW = "low"  # Minor concern


@dataclass
class DosageRange:
    """Safe dosage range model"""

    min_dose: float
    max_dose: float
    unit: str
    frequency: str
    route: str
    age_group: Optional[str] = None
    weight_based: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_dose": self.min_dose,
            "max_dose": self.max_dose,
            "unit": self.unit,
            "frequency": self.frequency,
            "route": self.route,
            "age_group": self.age_group,
            "weight_based": self.weight_based,
        }


@dataclass
class DosageViolation:
    """Dosage safety violation model"""

    medication: str
    prescribed_dose: str
    safe_range: DosageRange
    violation_type: str
    severity: DosageViolationSeverity
    reason: str
    recommendation: str
    monitoring_requirements: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "medication": self.medication,
            "prescribed_dose": self.prescribed_dose,
            "safe_range": self.safe_range.to_dict(),
            "violation_type": self.violation_type,
            "severity": self.severity.value,
            "reason": self.reason,
            "recommendation": self.recommendation,
            "monitoring_requirements": self.monitoring_requirements,
        }
