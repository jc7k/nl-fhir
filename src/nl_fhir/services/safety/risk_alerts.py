"""
Alert generation helpers for safety risk scoring.
"""

from typing import Any, Dict, List

from .risk_models import SafetyRiskScore, SafetyAlert, AlertSeverity, RiskLevel


def build_safety_alerts(
    risk_score: SafetyRiskScore,
    interaction_results: Dict[str, Any],
    contraindication_results: Dict[str, Any],
    dosage_results: Dict[str, Any],
) -> List[SafetyAlert]:
    """Generate prioritized safety alerts based on risk assessment."""

    alerts: List[SafetyAlert] = []
    alert_counter = 1

    if interaction_results.get("has_interactions"):
        contraindicated = [
            i
            for i in interaction_results.get("interactions", [])
            if i.get("severity") == "contraindicated"
        ]
        major = [
            i
            for i in interaction_results.get("interactions", [])
            if i.get("severity") == "major"
        ]

        if contraindicated:
            alerts.append(
                SafetyAlert(
                    alert_id=f"ALERT-{alert_counter:03d}",
                    severity=AlertSeverity.URGENT,
                    category="Drug Interactions",
                    title="Contraindicated Drug Combination Detected",
                    description=(
                        f"Found {len(contraindicated)} contraindicated drug interaction(s) "
                        "requiring immediate attention"
                    ),
                    affected_medications=[i["drug_a"] for i in contraindicated]
                    + [i["drug_b"] for i in contraindicated],
                    required_actions=[
                        "Stop contraindicated medications immediately",
                        "Consult prescriber for alternative therapy",
                        "Monitor patient for adverse effects",
                    ],
                    timeline="Immediate (within 1 hour)",
                    escalation_criteria=[
                        "Patient shows signs of adverse reaction",
                        "Unable to contact prescriber within 2 hours",
                    ],
                )
            )
            alert_counter += 1

        if major:
            alerts.append(
                SafetyAlert(
                    alert_id=f"ALERT-{alert_counter:03d}",
                    severity=AlertSeverity.ALERT,
                    category="Drug Interactions",
                    title="Major Drug Interactions Require Monitoring",
                    description=(
                        f"Found {len(major)} major drug interaction(s) requiring close monitoring"
                    ),
                    affected_medications=[i["drug_a"] for i in major]
                    + [i["drug_b"] for i in major],
                    required_actions=[
                        "Implement enhanced monitoring protocols",
                        "Consider dose adjustments",
                        "Educate patient about signs/symptoms to watch",
                    ],
                    timeline="Within 24 hours",
                    escalation_criteria=[
                        "Patient develops symptoms",
                        "Lab values show adverse trends",
                    ],
                )
            )
            alert_counter += 1

    if contraindication_results.get("has_contraindications"):
        absolute = [
            c
            for c in contraindication_results.get("contraindications", [])
            if c.get("severity") == "absolute"
        ]

        if absolute:
            alerts.append(
                SafetyAlert(
                    alert_id=f"ALERT-{alert_counter:03d}",
                    severity=AlertSeverity.URGENT,
                    category="Contraindications",
                    title="Absolute Contraindications Detected",
                    description=(
                        f"Found {len(absolute)} absolute contraindication(s) requiring "
                        "medication discontinuation"
                    ),
                    affected_medications=[c["medication"] for c in absolute],
                    required_actions=[
                        "Discontinue contraindicated medications",
                        "Assess for alternative therapies",
                        "Monitor for withdrawal effects if applicable",
                    ],
                    timeline="Immediate (within 1 hour)",
                    escalation_criteria=[
                        "Patient at immediate risk",
                        "No safe alternatives available",
                    ],
                )
            )
            alert_counter += 1

    if dosage_results.get("has_dosage_violations"):
        critical = [
            v
            for v in dosage_results.get("violations", [])
            if v.get("severity") == "critical"
        ]

        if critical:
            alerts.append(
                SafetyAlert(
                    alert_id=f"ALERT-{alert_counter:03d}",
                    severity=AlertSeverity.URGENT,
                    category="Dosage Safety",
                    title="Critical Dosage Violations Detected",
                    description=(
                        f"Found {len(critical)} critical dosage violation(s) with potential for serious harm"
                    ),
                    affected_medications=[v["medication"] for v in critical],
                    required_actions=[
                        "Verify and correct dosing immediately",
                        "Assess patient for signs of overdose/underdose",
                        "Consider antidote if overdose suspected",
                    ],
                    timeline="Immediate (within 30 minutes)",
                    escalation_criteria=[
                        "Signs of toxicity present",
                        "Dosing error confirmed",
                    ],
                )
            )
            alert_counter += 1

    if risk_score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        alerts.append(
            SafetyAlert(
                alert_id=f"ALERT-{alert_counter:03d}",
                severity=AlertSeverity.ALERT
                if risk_score.risk_level == RiskLevel.HIGH
                else AlertSeverity.URGENT,
                category="Overall Risk",
                title=f"{risk_score.risk_level.value.title()} Safety Risk Profile",
                description=(
                    f"Patient has {risk_score.risk_level.value} overall safety risk "
                    f"(score: {risk_score.overall_score:.1f}/100)"
                ),
                affected_medications=[],
                required_actions=risk_score.recommendations[:3],
                timeline="Within 24 hours"
                if risk_score.risk_level == RiskLevel.HIGH
                else "Within 4 hours",
                escalation_criteria=risk_score.escalation_triggers,
            )
        )

    return alerts
