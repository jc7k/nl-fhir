"""
Story 4.3: LLM-Enhanced Summarization
Optional LLM enhancement with validation and fallback
"""

from typing import Any, Dict, List, Optional
import json
import asyncio
from datetime import datetime


class LLMEnhancer:
    """LLM enhancement service for medical summaries"""

    def __init__(self):
        # Simulated LLM client - in production would use actual LLM service
        self.llm_available = True
        self.enhancement_timeout = 5.0

    async def enhance_summary(self, 
                            template_summary: str,
                            bundle_data: Dict[str, Any],
                            enhancement_level: str = "contextual") -> Dict[str, Any]:
        """
        Enhance template-based summary with LLM processing
        
        Args:
            template_summary: Original template-based summary
            bundle_data: Original FHIR bundle for context
            enhancement_level: contextual|educational|comprehensive
            
        Returns:
            Enhancement result with validation status
        """
        try:
            # Simulate LLM processing with timeout
            enhanced_text = await asyncio.wait_for(
                self._simulate_llm_enhancement(template_summary, enhancement_level),
                timeout=self.enhancement_timeout
            )
            
            # Validate enhancement
            validation_result = self._validate_enhancement(
                template_summary, enhanced_text, bundle_data
            )
            
            if validation_result["is_valid"]:
                return {
                    "enhanced_summary": enhanced_text,
                    "enhancement_level": enhancement_level,
                    "validation_passed": True,
                    "enhancement_applied": True,
                    "validation_details": validation_result,
                    "fallback_used": False,
                    "processing_time_ms": 1200  # Simulated
                }
            else:
                # Validation failed - return original
                return {
                    "enhanced_summary": template_summary,
                    "enhancement_level": "none",
                    "validation_passed": False,
                    "enhancement_applied": False,
                    "validation_details": validation_result,
                    "fallback_used": True,
                    "processing_time_ms": 800
                }
                
        except asyncio.TimeoutError:
            return self._timeout_fallback(template_summary)
        except Exception as e:
            return self._error_fallback(template_summary, str(e))

    async def _simulate_llm_enhancement(self, template_summary: str, level: str) -> str:
        """Simulate LLM enhancement - replace with actual LLM in production"""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        if level == "contextual":
            return self._add_contextual_enhancement(template_summary)
        elif level == "educational":
            return self._add_educational_enhancement(template_summary)
        elif level == "comprehensive":
            return self._add_comprehensive_enhancement(template_summary)
        else:
            return template_summary

    def _add_contextual_enhancement(self, summary: str) -> str:
        """Add clinical context to summary"""
        enhanced_lines = []
        
        for line in summary.split('\n'):
            enhanced_lines.append(line)
            
            # Add context for medications
            if "Medication order:" in line and "Metformin" in line:
                enhanced_lines.append("  • This medication helps control blood sugar by improving insulin sensitivity and reducing glucose production.")
            elif "Medication order:" in line and "Warfarin" in line:
                enhanced_lines.append("  • Blood thinner requiring regular monitoring of clotting times (INR).")
            elif "Medication order:" in line and "Insulin" in line:
                enhanced_lines.append("  • Hormone replacement for diabetes management - monitor blood glucose closely.")
                
            # Add context for observations
            elif "Observation:" in line and "High" in line:
                enhanced_lines.append("  • Abnormal result requiring clinical attention and possible intervention.")
            elif "Observation:" in line and "blood pressure" in line.lower():
                enhanced_lines.append("  • Important cardiovascular indicator for monitoring heart health.")
                
        return '\n'.join(enhanced_lines)

    def _add_educational_enhancement(self, summary: str) -> str:
        """Add patient education information"""
        enhanced = self._add_contextual_enhancement(summary)
        
        # Add educational footer
        enhanced += "\n\n--- Patient Education Notes ---\n"
        enhanced += "• Take medications as prescribed and at consistent times\n"
        enhanced += "• Contact your healthcare provider if you experience any unusual symptoms\n"
        enhanced += "• Keep a record of your medications and bring it to all appointments\n"
        enhanced += "• Follow up as scheduled for monitoring and adjustments"
        
        return enhanced

    def _add_comprehensive_enhancement(self, summary: str) -> str:
        """Add comprehensive enhancement with full context"""
        enhanced = self._add_educational_enhancement(summary)
        
        # Add comprehensive analysis
        enhanced += "\n\n--- Clinical Overview ---\n"
        enhanced += "This clinical order represents a comprehensive treatment plan addressing "
        enhanced += "the patient's current health conditions. The prescribed medications and "
        enhanced += "monitoring requirements are designed to optimize therapeutic outcomes while "
        enhanced += "minimizing potential adverse effects. Regular follow-up and adherence to "
        enhanced += "the treatment plan are essential for achieving the best clinical results."
        
        return enhanced

    def _validate_enhancement(self, original: str, enhanced: str, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Validate LLM enhancement for medical accuracy"""
        validation_issues = []
        
        # Check for preservation of core medical facts
        if not self._preserve_medication_names(original, enhanced):
            validation_issues.append("Medication names not preserved")
            
        if not self._preserve_dosage_info(original, enhanced):
            validation_issues.append("Dosage information not preserved")
            
        if not self._check_no_contraindications(enhanced):
            validation_issues.append("Potential medical contraindications added")
            
        # Check for appropriate length (shouldn't be too verbose)
        if len(enhanced) > len(original) * 3:
            validation_issues.append("Enhancement too verbose")
            
        return {
            "is_valid": len(validation_issues) == 0,
            "issues": validation_issues,
            "preservation_score": self._calculate_preservation_score(original, enhanced),
            "enhancement_quality": self._calculate_enhancement_quality(original, enhanced)
        }

    def _preserve_medication_names(self, original: str, enhanced: str) -> bool:
        """Check that all medication names are preserved"""
        # Extract medication names from original
        med_keywords = ["Metformin", "Warfarin", "Insulin", "Lisinopril", "Aspirin"]
        
        for med in med_keywords:
            if med in original and med not in enhanced:
                return False
        return True

    def _preserve_dosage_info(self, original: str, enhanced: str) -> bool:
        """Check that dosage information is preserved"""
        # Look for dosage patterns like "500mg", "twice daily", etc.
        import re
        dosage_patterns = re.findall(r'\d+\s*mg|\d+\s*times?\s+daily|twice\s+daily|once\s+daily', original, re.IGNORECASE)
        
        for pattern in dosage_patterns:
            if pattern.lower() not in enhanced.lower():
                return False
        return True

    def _check_no_contraindications(self, enhanced: str) -> bool:
        """Check that no dangerous medical advice was added"""
        dangerous_phrases = [
            "stop taking",
            "discontinue medication",
            "double the dose",
            "skip doses",
            "medical emergency"
        ]
        
        enhanced_lower = enhanced.lower()
        for phrase in dangerous_phrases:
            if phrase in enhanced_lower:
                return False
        return True

    def _calculate_preservation_score(self, original: str, enhanced: str) -> float:
        """Calculate how well original content is preserved (0-1)"""
        original_words = set(original.lower().split())
        enhanced_words = set(enhanced.lower().split())
        
        if not original_words:
            return 1.0
            
        preserved = len(original_words.intersection(enhanced_words))
        return preserved / len(original_words)

    def _calculate_enhancement_quality(self, original: str, enhanced: str) -> float:
        """Calculate quality of enhancement (0-1)"""
        # Simple quality metrics
        length_ratio = len(enhanced) / max(len(original), 1)
        
        # Good enhancement should be 1.5-2.5x original length
        if 1.5 <= length_ratio <= 2.5:
            quality = 0.8
        elif 1.0 <= length_ratio < 1.5:
            quality = 0.6
        else:
            quality = 0.4
            
        return quality

    def _timeout_fallback(self, original: str) -> Dict[str, Any]:
        """Return fallback result for timeout"""
        return {
            "enhanced_summary": original,
            "enhancement_level": "none",
            "validation_passed": False,
            "enhancement_applied": False,
            "validation_details": {"is_valid": False, "issues": ["Processing timeout"]},
            "fallback_used": True,
            "processing_time_ms": 5000,
            "error": "Enhancement processing timed out"
        }

    def _error_fallback(self, original: str, error: str) -> Dict[str, Any]:
        """Return fallback result for errors"""
        return {
            "enhanced_summary": original,
            "enhancement_level": "none", 
            "validation_passed": False,
            "enhancement_applied": False,
            "validation_details": {"is_valid": False, "issues": [f"Processing error: {error}"]},
            "fallback_used": True,
            "processing_time_ms": 0,
            "error": error
        }

    def get_enhancement_options(self) -> Dict[str, Any]:
        """Get available enhancement options"""
        return {
            "available_levels": [
                {
                    "level": "contextual",
                    "description": "Add clinical context and reasoning",
                    "estimated_time_ms": 1000
                },
                {
                    "level": "educational", 
                    "description": "Add patient education information",
                    "estimated_time_ms": 1500
                },
                {
                    "level": "comprehensive",
                    "description": "Full enhancement with context and education",
                    "estimated_time_ms": 2000
                }
            ],
            "llm_available": self.llm_available,
            "default_timeout_ms": int(self.enhancement_timeout * 1000)
        }