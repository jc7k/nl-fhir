"""
Story 4.3 & 4.4: Hybrid Summarization Service
Combines template-based summaries with optional LLM enhancement and safety integration
"""

from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime

from .summarization import SummarizationService
from .llm_enhancer import LLMEnhancer


class HybridSummarizer:
    """Unified summarization service with template-based + optional LLM enhancement + safety integration"""
    
    def __init__(self):
        self.template_summarizer = SummarizationService()
        self.llm_enhancer = LLMEnhancer()
        # Import SafetyValidator using simple import
        from .safety_validator import SafetyValidator
        self.safety_validator = SafetyValidator()
        
    async def create_comprehensive_summary(self, 
                                         bundle: Dict[str, Any],
                                         options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create comprehensive summary with template + optional LLM + safety validation
        
        Args:
            bundle: FHIR bundle to summarize
            options: Enhancement options including llm_enhancement, enhancement_level, etc.
        """
        options = options or {}
        start_time = datetime.now()
        
        # Step 1: Template-based summary (always fast and reliable)
        template_result = self.template_summarizer.summarize(
            bundle, 
            role=options.get("role", "clinician"),
            context=options.get("context")
        )
        
        # Step 2: Safety validation (always performed)
        safety_result = self.safety_validator.evaluate(bundle)
        
        # Step 3: Optional LLM enhancement
        llm_result = None
        if options.get("llm_enhancement", False):
            try:
                llm_result = await self.llm_enhancer.enhance_summary(
                    template_result["human_readable_summary"],
                    bundle,
                    options.get("enhancement_level", "contextual")
                )
            except Exception as e:
                # LLM enhancement failed - continue with template
                llm_result = {
                    "enhanced_summary": template_result["human_readable_summary"],
                    "enhancement_applied": False,
                    "fallback_used": True,
                    "error": str(e)
                }
        
        # Step 4: Integrate results
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return self._create_unified_response(
            template_result, safety_result, llm_result, processing_time, options
        )
    
    def _create_unified_response(self, 
                               template_result: Dict[str, Any],
                               safety_result: Dict[str, Any], 
                               llm_result: Optional[Dict[str, Any]],
                               processing_time: float,
                               options: Dict[str, Any]) -> Dict[str, Any]:
        """Create unified response combining all components"""
        
        # Determine final summary text
        if llm_result and llm_result.get("enhancement_applied", False):
            final_summary = llm_result["enhanced_summary"]
            summary_type = "llm_enhanced"
        else:
            final_summary = template_result["human_readable_summary"]
            summary_type = "template_based"
            
        # Integrate safety alerts into summary
        enhanced_summary_with_safety = self._integrate_safety_alerts(
            final_summary, safety_result
        )
        
        # Create comprehensive response
        response = {
            "summary": enhanced_summary_with_safety,
            "summary_type": summary_type,
            "bundle_stats": template_result.get("bundle_summary", {}),
            "confidence": template_result.get("confidence_indicators", {}).get("quality", {}).get("coverage_score", 0.95),
            
            # Safety information
            "safety": {
                "is_safe": safety_result.get("is_safe", True),
                "issues": safety_result.get("issues", []),
                "warnings": safety_result.get("warnings", []),
                "risk_score": safety_result.get("risk_score", {}),
                "recommendations": safety_result.get("recommendations", [])
            },
            
            # Processing details
            "processing": {
                "total_time_ms": processing_time,
                "template_generated": True,
                "safety_validated": True,
                "llm_enhancement_requested": options.get("llm_enhancement", False),
                "llm_enhancement_applied": llm_result.get("enhancement_applied", False) if llm_result else False,
                "fallback_used": llm_result.get("fallback_used", False) if llm_result else False
            },
            
            # Component results for debugging/monitoring
            "component_results": {
                "template": template_result,
                "safety": safety_result,
                "llm_enhancement": llm_result
            }
        }
        
        # Add enhancement details if LLM was used
        if llm_result:
            response["enhancement_details"] = {
                "level": llm_result.get("enhancement_level", "none"),
                "validation_passed": llm_result.get("validation_passed", False),
                "validation_details": llm_result.get("validation_details", {}),
                "processing_time_ms": llm_result.get("processing_time_ms", 0)
            }
            
        return response
    
    def _integrate_safety_alerts(self, summary: str, safety_result: Dict[str, Any]) -> str:
        """Integrate safety alerts prominently into summary"""
        
        # Start with original summary
        enhanced_summary = summary
        
        # Add critical safety issues at the top
        issues = safety_result.get("issues", [])
        if issues:
            safety_header = "\n🚨 CRITICAL SAFETY ALERTS 🚨\n"
            for issue in issues:
                safety_header += f"• {issue}\n"
            enhanced_summary = safety_header + "\n" + enhanced_summary
            
        # Add warnings section
        warnings = safety_result.get("warnings", [])
        if warnings:
            warnings_section = "\n⚠️  Safety Considerations:\n"
            for warning in warnings:
                warnings_section += f"• {warning}\n"
            enhanced_summary += warnings_section
            
        # Add risk score if significant
        risk_score = safety_result.get("risk_score", {})
        if risk_score and risk_score.get("total_score", 0) > 40:
            risk_level = risk_score.get("risk_level", "UNKNOWN")
            enhanced_summary += f"\n📊 Overall Safety Risk: {risk_level} (Score: {risk_score.get('total_score', 0)}/100)\n"
            
        # Add recommendations
        recommendations = safety_result.get("recommendations", [])
        if recommendations:
            rec_section = "\n💡 Clinical Recommendations:\n"
            for rec in recommendations[:3]:  # Limit to top 3
                if isinstance(rec, dict):
                    rec_section += f"• {rec.get('recommendation', rec)}\n"
                else:
                    rec_section += f"• {rec}\n"
            enhanced_summary += rec_section
            
        return enhanced_summary
    
    def get_summarization_options(self) -> Dict[str, Any]:
        """Get available summarization options"""
        return {
            "template_based": {
                "description": "Fast, reliable template-based summaries",
                "response_time_ms": "< 500",
                "always_available": True
            },
            "llm_enhancement": {
                "description": "Optional LLM enhancement for richer summaries", 
                "options": self.llm_enhancer.get_enhancement_options(),
                "fallback_available": True
            },
            "safety_validation": {
                "description": "Comprehensive safety analysis",
                "always_performed": True,
                "components": [
                    "Drug interaction checking",
                    "Contraindication detection", 
                    "Dosage validation",
                    "Clinical decision support",
                    "Risk scoring"
                ]
            },
            "supported_roles": [
                "clinician",
                "patient", 
                "nurse",
                "pharmacist",
                "administrator"
            ]
        }
    
    # Synchronous version for backward compatibility
    def summarize_sync(self, bundle: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Synchronous version (no LLM enhancement)"""
        options = options or {}
        
        # Template summary
        template_result = self.template_summarizer.summarize(
            bundle,
            role=options.get("role", "clinician"), 
            context=options.get("context")
        )
        
        # Safety validation
        safety_result = self.safety_validator.evaluate(bundle)
        
        # Create response without LLM enhancement
        return self._create_unified_response(
            template_result, safety_result, None, 0, options
        )