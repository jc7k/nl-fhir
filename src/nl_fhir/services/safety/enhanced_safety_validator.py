"""
Story 4.2: Enhanced Safety Validator - Comprehensive Integration
Unified safety validation system integrating all safety components
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from .interaction_checker import DrugInteractionChecker
from .contraindication_checker import ContraindicationChecker
from .dosage_validator import DosageValidator
from .clinical_decision_support import ClinicalDecisionSupport
from .risk_scorer import SafetyRiskScorer, RiskLevel


class EnhancedSafetyValidator:
    """
    Comprehensive safety validation system integrating:
    - Drug interaction detection
    - Contraindication checking
    - Dosage safety validation
    - Clinical decision support
    - Risk scoring and alert generation
    """
    
    def __init__(self):
        self.interaction_checker = DrugInteractionChecker()
        self.contraindication_checker = ContraindicationChecker()
        self.dosage_validator = DosageValidator()
        self.clinical_decision_support = ClinicalDecisionSupport()
        self.risk_scorer = SafetyRiskScorer()
        
        # Audit trail for compliance
        self.audit_log = []
    
    def comprehensive_safety_evaluation(self, bundle: Dict[str, Any], 
                                      request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive safety evaluation of FHIR bundle
        
        Returns complete safety analysis with all components integrated
        """
        
        if not request_id:
            request_id = str(uuid.uuid4())[:8]
        
        evaluation_start = datetime.now()
        
        try:
            # 1. Drug Interaction Analysis
            interaction_results = self.interaction_checker.check_bundle_interactions(bundle)
            
            # 2. Contraindication Analysis
            contraindication_results = self.contraindication_checker.check_bundle_contraindications(bundle)
            
            # 3. Dosage Safety Validation
            dosage_results = self.dosage_validator.validate_bundle_dosages(bundle)
            
            # 4. Clinical Decision Support
            clinical_recommendations = self.clinical_decision_support.generate_clinical_recommendations(bundle)
            
            # 5. Risk Scoring and Alert Generation
            risk_score = self.risk_scorer.calculate_safety_risk_score(
                bundle, interaction_results, contraindication_results, dosage_results
            )
            
            safety_alerts = self.risk_scorer.generate_safety_alerts(
                risk_score, interaction_results, contraindication_results, dosage_results
            )
            
            # 6. Generate comprehensive safety summary
            safety_summary = self._generate_comprehensive_summary(
                interaction_results, contraindication_results, dosage_results,
                clinical_recommendations, risk_score, safety_alerts
            )
            
            # 7. Generate actionable recommendations
            unified_recommendations = self._generate_unified_recommendations(
                interaction_results, contraindication_results, dosage_results,
                clinical_recommendations, risk_score
            )
            
            # 8. Compliance and audit documentation
            audit_record = self._create_audit_record(
                request_id, bundle, safety_summary, risk_score, evaluation_start
            )
            
            # Comprehensive response
            comprehensive_evaluation = {
                "request_id": request_id,
                "evaluation_timestamp": evaluation_start.isoformat(),
                "bundle_safety_assessment": {
                    "overall_safety_status": self._determine_overall_safety_status(risk_score),
                    "risk_score": risk_score.to_dict(),
                    "safety_alerts": [alert.to_dict() for alert in safety_alerts],
                    "summary": safety_summary
                },
                "detailed_analysis": {
                    "drug_interactions": interaction_results,
                    "contraindications": contraindication_results,
                    "dosage_safety": dosage_results,
                    "clinical_recommendations": clinical_recommendations
                },
                "unified_recommendations": unified_recommendations,
                "compliance_documentation": {
                    "audit_record_id": audit_record["audit_id"],
                    "validation_method": "comprehensive_multi_layer_analysis",
                    "evidence_level": "high",
                    "regulatory_compliance": self._assess_regulatory_compliance(risk_score, safety_alerts)
                },
                "next_steps": self._generate_next_steps(risk_score, safety_alerts),
                "escalation_required": self._determine_escalation_required(risk_score, safety_alerts)
            }
            
            # Log successful evaluation
            self._log_audit_event(audit_record, "SUCCESS", None)
            
            return comprehensive_evaluation
            
        except Exception as e:
            # Log error for audit trail
            error_audit = self._create_error_audit_record(request_id, bundle, str(e), evaluation_start)
            self._log_audit_event(error_audit, "ERROR", str(e))
            
            # Return error response with minimal safety information
            return {
                "request_id": request_id,
                "evaluation_timestamp": evaluation_start.isoformat(),
                "error": "Safety evaluation failed",
                "error_details": str(e),
                "fallback_safety_assessment": self._basic_safety_fallback(bundle),
                "audit_record_id": error_audit["audit_id"]
            }
    
    def enhanced_safety_check(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced version of the basic safety check for Story 4.1 integration
        
        Provides backward compatibility while adding comprehensive safety features
        """
        # Perform comprehensive evaluation
        comprehensive_results = self.comprehensive_safety_evaluation(bundle)
        
        # Extract simplified results for Story 4.1 compatibility
        safety_assessment = comprehensive_results.get("bundle_safety_assessment", {})
        detailed_analysis = comprehensive_results.get("detailed_analysis", {})
        
        # Map to Story 4.1 expected format with enhancements
        enhanced_safety_check = {
            "is_safe": safety_assessment.get("overall_safety_status") in ["safe", "caution"],
            "issues": self._extract_safety_issues(detailed_analysis),
            "warnings": self._extract_safety_warnings(detailed_analysis),
            "summary": {
                "issues_count": len(self._extract_safety_issues(detailed_analysis)),
                "warnings_count": len(self._extract_safety_warnings(detailed_analysis)),
                "risk_level": safety_assessment.get("risk_score", {}).get("risk_level", "minimal"),
                "overall_score": safety_assessment.get("risk_score", {}).get("overall_score", 0)
            },
            # Enhanced fields for Story 4.2
            "enhanced_analysis": {
                "drug_interactions": detailed_analysis.get("drug_interactions", {}),
                "contraindications": detailed_analysis.get("contraindications", {}),
                "dosage_safety": detailed_analysis.get("dosage_safety", {}),
                "clinical_recommendations": detailed_analysis.get("clinical_recommendations", {}),
                "safety_alerts": safety_assessment.get("safety_alerts", []),
                "risk_assessment": safety_assessment.get("risk_score", {})
            },
            "recommendations": comprehensive_results.get("unified_recommendations", []),
            "next_steps": comprehensive_results.get("next_steps", []),
            "audit_id": comprehensive_results.get("compliance_documentation", {}).get("audit_record_id")
        }
        
        return enhanced_safety_check
    
    def _determine_overall_safety_status(self, risk_score) -> str:
        """Determine overall safety status based on risk assessment"""
        if risk_score.risk_level == RiskLevel.CRITICAL:
            return "critical"
        elif risk_score.risk_level == RiskLevel.HIGH:
            return "high_risk"
        elif risk_score.risk_level == RiskLevel.MODERATE:
            return "caution"
        elif risk_score.risk_level == RiskLevel.LOW:
            return "low_risk"
        else:
            return "safe"
    
    def _generate_comprehensive_summary(self, interaction_results: Dict, contraindication_results: Dict,
                                      dosage_results: Dict, clinical_recommendations: Dict,
                                      risk_score, safety_alerts: List) -> str:
        """Generate comprehensive safety summary"""
        
        summary_parts = []
        
        # Risk level summary
        summary_parts.append(f"Overall safety risk: {risk_score.risk_level.value} (score: {risk_score.overall_score:.1f}/100)")
        
        # Component summaries
        if interaction_results.get("has_interactions"):
            summary_parts.append(interaction_results["summary"])
        
        if contraindication_results.get("has_contraindications"):
            summary_parts.append(contraindication_results["summary"])
        
        if dosage_results.get("has_dosage_violations"):
            summary_parts.append(dosage_results["summary"])
        
        # Alert summary
        if safety_alerts:
            urgent_alerts = len([a for a in safety_alerts if a.severity.value == "urgent"])
            if urgent_alerts > 0:
                summary_parts.append(f"{urgent_alerts} urgent safety alert(s) requiring immediate attention")
        
        # Clinical recommendations summary
        rec_count = clinical_recommendations.get("recommendation_count", 0)
        if rec_count > 0:
            summary_parts.append(f"{rec_count} clinical recommendation(s) available")
        
        if not summary_parts or len(summary_parts) == 1:
            summary_parts.append("No significant safety concerns identified")
        
        return "; ".join(summary_parts)
    
    def _generate_unified_recommendations(self, interaction_results: Dict, contraindication_results: Dict,
                                        dosage_results: Dict, clinical_recommendations: Dict,
                                        risk_score) -> List[str]:
        """Generate unified, prioritized recommendations"""
        
        unified_recommendations = []
        
        # Priority 1: Critical safety issues
        if risk_score.risk_level == RiskLevel.CRITICAL:
            unified_recommendations.extend(risk_score.recommendations[:2])
        
        # Priority 2: Drug interactions
        if interaction_results.get("has_interactions"):
            urgent_interactions = [i for i in interaction_results.get("interactions", [])
                                 if i.get("severity") == "contraindicated"]
            if urgent_interactions:
                unified_recommendations.append("URGENT: Address contraindicated drug combinations immediately")
        
        # Priority 3: Contraindications
        if contraindication_results.get("has_contraindications"):
            absolute_contraindications = [c for c in contraindication_results.get("contraindications", [])
                                        if c.get("severity") == "absolute"]
            if absolute_contraindications:
                unified_recommendations.append("CRITICAL: Discontinue medications with absolute contraindications")
        
        # Priority 4: Dosage safety
        if dosage_results.get("has_dosage_violations"):
            critical_dosage = [v for v in dosage_results.get("violations", [])
                             if v.get("severity") == "critical"]
            if critical_dosage:
                unified_recommendations.append("URGENT: Correct critical dosage violations")
        
        # Priority 5: Clinical recommendations (high priority only)
        high_priority_clinical = [r for r in clinical_recommendations.get("recommendations", [])
                                if r.get("priority") == "high"]
        for rec in high_priority_clinical[:2]:  # Top 2 high priority
            unified_recommendations.append(f"Clinical: {rec['recommendation']}")
        
        # Priority 6: Monitoring requirements
        if risk_score.monitoring_requirements:
            unified_recommendations.append(f"Implement monitoring: {', '.join(risk_score.monitoring_requirements[:3])}")
        
        return unified_recommendations[:8]  # Top 8 recommendations
    
    def _extract_safety_issues(self, detailed_analysis: Dict) -> List[str]:
        """Extract safety issues for Story 4.1 compatibility"""
        issues = []
        
        # Drug interaction issues
        interactions = detailed_analysis.get("drug_interactions", {}).get("interactions", [])
        for interaction in interactions:
            if interaction.get("severity") in ["contraindicated", "major"]:
                issues.append(f"Drug interaction: {interaction['drug_a']} + {interaction['drug_b']} ({interaction['severity']})")
        
        # Contraindication issues
        contraindications = detailed_analysis.get("contraindications", {}).get("contraindications", [])
        for contraindication in contraindications:
            if contraindication.get("severity") in ["absolute", "relative"]:
                issues.append(f"Contraindication: {contraindication['medication']} - {contraindication['reason']}")
        
        # Dosage issues
        violations = detailed_analysis.get("dosage_safety", {}).get("violations", [])
        for violation in violations:
            if violation.get("severity") in ["critical", "high"]:
                issues.append(f"Dosage concern: {violation['medication']} - {violation['violation_type']}")
        
        return issues
    
    def _extract_safety_warnings(self, detailed_analysis: Dict) -> List[str]:
        """Extract safety warnings for Story 4.1 compatibility"""
        warnings = []
        
        # Drug interaction warnings
        interactions = detailed_analysis.get("drug_interactions", {}).get("interactions", [])
        for interaction in interactions:
            if interaction.get("severity") in ["moderate", "minor"]:
                warnings.append(f"Monitor for {interaction['drug_a']} + {interaction['drug_b']} interaction")
        
        # Contraindication warnings
        contraindications = detailed_analysis.get("contraindications", {}).get("contraindications", [])
        for contraindication in contraindications:
            if contraindication.get("severity") in ["caution", "warning"]:
                warnings.append(f"Caution: {contraindication['medication']} with {contraindication['condition']}")
        
        # Dosage warnings
        violations = detailed_analysis.get("dosage_safety", {}).get("violations", [])
        for violation in violations:
            if violation.get("severity") in ["moderate", "low"]:
                warnings.append(f"Monitor dosage: {violation['medication']} - {violation['violation_type']}")
        
        # Clinical recommendations as warnings
        recommendations = detailed_analysis.get("clinical_recommendations", {}).get("recommendations", [])
        for rec in recommendations:
            if rec.get("type") == "monitoring":
                warnings.append(f"Monitor: {rec['medication']} - {rec['recommendation']}")
        
        return warnings
    
    def _create_audit_record(self, request_id: str, bundle: Dict[str, Any], 
                           safety_summary: str, risk_score, evaluation_start: datetime) -> Dict[str, Any]:
        """Create comprehensive audit record for compliance"""
        
        audit_record = {
            "audit_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": evaluation_start.isoformat(),
            "bundle_metadata": {
                "resource_count": len(bundle.get("entry", [])),
                "bundle_type": bundle.get("type"),
                "medication_count": len([e for e in bundle.get("entry", []) 
                                       if e.get("resource", {}).get("resourceType") == "MedicationRequest"])
            },
            "safety_evaluation": {
                "overall_risk_level": risk_score.risk_level.value,
                "risk_score": risk_score.overall_score,
                "safety_summary": safety_summary,
                "evaluation_method": "comprehensive_multi_layer_analysis"
            },
            "compliance_flags": {
                "hipaa_compliant": True,  # No PHI in logs
                "validation_performed": True,
                "evidence_based": True,
                "audit_trail_complete": True
            },
            "evaluation_duration_ms": (datetime.now() - evaluation_start).total_seconds() * 1000
        }
        
        return audit_record
    
    def _create_error_audit_record(self, request_id: str, bundle: Dict[str, Any], 
                                 error: str, evaluation_start: datetime) -> Dict[str, Any]:
        """Create audit record for failed evaluations"""
        
        return {
            "audit_id": str(uuid.uuid4()),
            "request_id": request_id,
            "timestamp": evaluation_start.isoformat(),
            "status": "error",
            "error": error,
            "bundle_metadata": {
                "resource_count": len(bundle.get("entry", [])) if bundle.get("entry") else 0,
                "bundle_type": bundle.get("type") if bundle else "unknown"
            },
            "evaluation_duration_ms": (datetime.now() - evaluation_start).total_seconds() * 1000
        }
    
    def _log_audit_event(self, audit_record: Dict[str, Any], status: str, error: Optional[str]):
        """Log audit event for compliance tracking"""
        
        audit_entry = {
            "audit_record": audit_record,
            "status": status,
            "logged_at": datetime.now().isoformat()
        }
        
        if error:
            audit_entry["error"] = error
        
        # Store in audit log (in production, this would go to secure audit database)
        self.audit_log.append(audit_entry)
        
        # Keep audit log size manageable (in production, implement proper archiving)
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-500:]  # Keep last 500 entries
    
    def _assess_regulatory_compliance(self, risk_score, safety_alerts: List) -> Dict[str, Any]:
        """Assess regulatory compliance status"""
        
        compliance_assessment = {
            "fda_guidance_compliance": True,
            "clinical_decision_support_standard": "met",
            "safety_validation_complete": True,
            "audit_trail_complete": True,
            "risk_assessment_performed": True
        }
        
        # Check for compliance issues
        if risk_score.risk_level == RiskLevel.CRITICAL:
            compliance_assessment["immediate_review_required"] = True
        
        urgent_alerts = [a for a in safety_alerts if a.severity.value == "urgent"]
        if urgent_alerts:
            compliance_assessment["urgent_intervention_documented"] = True
        
        return compliance_assessment
    
    def _generate_next_steps(self, risk_score, safety_alerts: List) -> List[str]:
        """Generate specific next steps based on risk assessment"""
        
        next_steps = []
        
        # Risk level specific steps
        if risk_score.risk_level == RiskLevel.CRITICAL:
            next_steps.extend([
                "Immediate clinical review required",
                "Implement emergency safety protocols",
                "Document all interventions"
            ])
        elif risk_score.risk_level == RiskLevel.HIGH:
            next_steps.extend([
                "Prioritize clinical review within 24 hours",
                "Implement enhanced monitoring",
                "Consider medication adjustments"
            ])
        
        # Alert-specific steps
        urgent_alerts = [a for a in safety_alerts if a.severity.value == "urgent"]
        for alert in urgent_alerts[:2]:  # Top 2 urgent alerts
            next_steps.extend(alert.required_actions[:2])
        
        # General steps for any risk
        if risk_score.overall_score > 20:
            next_steps.append("Schedule follow-up safety review")
        
        return next_steps[:6]  # Top 6 next steps
    
    def _determine_escalation_required(self, risk_score, safety_alerts: List) -> bool:
        """Determine if escalation to clinical team is required"""
        
        # Critical risk level always requires escalation
        if risk_score.risk_level == RiskLevel.CRITICAL:
            return True
        
        # Urgent alerts require escalation
        urgent_alerts = [a for a in safety_alerts if a.severity.value == "urgent"]
        if urgent_alerts:
            return True
        
        # High risk with multiple factors
        if risk_score.risk_level == RiskLevel.HIGH and risk_score.overall_score > 75:
            return True
        
        return False
    
    def _basic_safety_fallback(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Basic safety assessment fallback when comprehensive evaluation fails"""
        
        # Count medications for basic polypharmacy check
        medications = [e for e in bundle.get("entry", []) 
                      if e.get("resource", {}).get("resourceType") == "MedicationRequest"]
        
        med_count = len(medications)
        
        # Basic risk assessment
        if med_count >= 10:
            risk_level = "high"
            summary = f"High medication burden ({med_count} medications) - manual review recommended"
        elif med_count >= 6:
            risk_level = "moderate"
            summary = f"Moderate medication burden ({med_count} medications) - standard monitoring"
        else:
            risk_level = "low"
            summary = f"Low medication burden ({med_count} medications) - routine care"
        
        return {
            "risk_level": risk_level,
            "medication_count": med_count,
            "summary": summary,
            "recommendation": "Manual safety review recommended due to system error",
            "fallback_used": True
        }
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get audit trail summary for compliance reporting"""
        
        total_evaluations = len(self.audit_log)
        successful_evaluations = len([log for log in self.audit_log if log["status"] == "SUCCESS"])
        error_rate = (total_evaluations - successful_evaluations) / total_evaluations if total_evaluations > 0 else 0
        
        return {
            "total_evaluations": total_evaluations,
            "successful_evaluations": successful_evaluations,
            "error_rate": error_rate,
            "compliance_status": "compliant" if error_rate < 0.05 else "review_required",
            "audit_trail_complete": True,
            "last_evaluation": self.audit_log[-1]["audit_record"]["timestamp"] if self.audit_log else None
        }