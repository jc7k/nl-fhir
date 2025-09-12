"""
Bundle Analyzer for Epic 4 Tier Selection Logic
Intelligent analysis of FHIR bundles to determine optimal processing tier
"""

import time
from typing import Dict, Any, List, Set, Optional
from datetime import datetime

from .models import BundleAnalysis, ProcessingTier, TierSelectionCriteria, ResourceClassification


class BundleAnalyzer:
    """
    Analyzes FHIR bundles to determine optimal processing tier
    Considers resource complexity, coverage, and cost optimization targets
    """
    
    def __init__(self, criteria: Optional[TierSelectionCriteria] = None):
        self.criteria = criteria or TierSelectionCriteria()
        
        # Known complex resource types that typically require LLM processing
        self.complex_resource_types = {
            'ClinicalImpression',
            'CarePlan', 
            'Communication',
            'DocumentReference',
            'Media',
            'QuestionnaireResponse'
        }
        
        # Emergency/urgent indicators
        self.emergency_indicators = {
            'emergency', 'urgent', 'stat', 'asap', 'immediate',
            'critical', 'life-threatening', 'emergent'
        }
    
    async def analyze_bundle(self, fhir_bundle: Dict[str, Any], resource_registry) -> BundleAnalysis:
        """
        Comprehensive analysis of FHIR bundle for tier selection
        Returns BundleAnalysis with processing recommendations
        """
        start_time = time.time()
        
        # Extract basic bundle information
        entries = fhir_bundle.get("entry", [])
        resources = [entry.get("resource", {}) for entry in entries if entry.get("resource")]
        
        resource_types = [r.get("resourceType") for r in resources if r.get("resourceType")]
        resource_count = len(resources)
        
        if not resources:
            return self._create_empty_bundle_analysis(start_time)
        
        # Analyze resource coverage and complexity
        rule_based_coverage = resource_registry.calculate_rule_coverage(resource_types)
        unsupported_types = resource_registry.get_unsupported_resource_types(resource_types)
        
        # Calculate complexity score
        complexity_score = await self._calculate_complexity_score(resources, resource_types)
        
        # Detect emergency/urgent indicators
        has_emergency_indicators = await self._detect_emergency_indicators(resources)
        
        # Assess rare resources
        has_rare_resources = await self._has_rare_resources(resource_types)
        
        # Determine optimal processing tier
        recommended_tier = await self._select_optimal_tier(
            complexity_score, rule_based_coverage, has_rare_resources, 
            has_emergency_indicators, resource_count, len(set(resource_types))
        )
        
        # Calculate confidence in recommendation
        confidence_score = await self._calculate_recommendation_confidence(
            recommended_tier, complexity_score, rule_based_coverage, resource_count
        )
        
        # Extract clinical context
        specialty_context = await self._extract_specialty_context(resources)
        urgency_level = await self._extract_urgency_level(resources)
        
        analysis_time = (time.time() - start_time) * 1000
        
        return BundleAnalysis(
            resource_types=resource_types,
            resource_count=resource_count,
            primary_resource_type=self._determine_primary_resource_type(resource_types),
            complexity_score=complexity_score,
            has_rare_resources=has_rare_resources,
            has_emergency_indicators=has_emergency_indicators,
            recommended_tier=recommended_tier,
            confidence_score=confidence_score,
            analysis_timestamp=datetime.now(),
            analysis_duration_ms=analysis_time,
            rule_based_coverage=rule_based_coverage,
            supported_resource_types=list(set(resource_types) - set(unsupported_types)),
            unsupported_resource_types=unsupported_types,
            specialty_context=specialty_context,
            urgency_level=urgency_level,
            patient_demographics=None  # Would extract from Patient resource if present
        )
    
    async def _calculate_complexity_score(self, resources: List[Dict], resource_types: List[str]) -> float:
        """
        Calculate bundle complexity score (0.0-10.0 scale)
        Based on resource types, relationships, and content complexity
        """
        score = 0.0
        
        # Base score from resource count
        resource_count = len(resources)
        if resource_count <= 2:
            score += 1.0
        elif resource_count <= 5:
            score += 2.0
        elif resource_count <= 10:
            score += 4.0
        else:
            score += 6.0
        
        # Complexity based on resource type diversity
        unique_types = len(set(resource_types))
        if unique_types >= 5:
            score += 2.0
        elif unique_types >= 3:
            score += 1.0
        
        # Complex resource type bonus
        complex_types = set(resource_types) & self.complex_resource_types
        score += len(complex_types) * 1.5
        
        # Relationship complexity (references between resources)
        reference_count = 0
        for resource in resources:
            reference_count += await self._count_resource_references(resource)
        
        if reference_count >= 10:
            score += 2.0
        elif reference_count >= 5:
            score += 1.0
        
        # Content complexity (deep nested structures, extensions)
        for resource in resources:
            content_complexity = await self._assess_content_complexity(resource)
            score += content_complexity * 0.5
        
        return min(10.0, score)
    
    async def _count_resource_references(self, resource: Dict[str, Any]) -> int:
        """Count references to other resources in this resource"""
        references = 0
        
        def count_references_recursive(obj):
            nonlocal references
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'reference' and isinstance(value, str):
                        references += 1
                    else:
                        count_references_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    count_references_recursive(item)
        
        count_references_recursive(resource)
        return references
    
    async def _assess_content_complexity(self, resource: Dict[str, Any]) -> float:
        """Assess content complexity based on nested structures and extensions"""
        complexity = 0.0
        
        # Count extensions
        extensions = resource.get('extension', [])
        if isinstance(extensions, list):
            complexity += len(extensions) * 0.2
        
        # Count nested objects
        def count_depth(obj, depth=0):
            if depth > 3:  # Very nested structures are complex
                return 0.5
            if isinstance(obj, dict):
                return max((count_depth(v, depth + 1) for v in obj.values()), default=0)
            elif isinstance(obj, list) and obj:
                return max((count_depth(item, depth + 1) for item in obj), default=0)
            return 0
        
        complexity += count_depth(resource)
        
        return min(2.0, complexity)
    
    async def _detect_emergency_indicators(self, resources: List[Dict]) -> bool:
        """Detect emergency or urgent indicators in the bundle"""
        
        for resource in resources:
            # Check priority fields
            priority = resource.get('priority', '').lower()
            if any(indicator in priority for indicator in self.emergency_indicators):
                return True
            
            # Check status fields
            status = resource.get('status', '').lower()
            if any(indicator in status for indicator in self.emergency_indicators):
                return True
            
            # Check text content for emergency keywords
            text = resource.get('text', {}).get('div', '').lower()
            if any(indicator in text for indicator in self.emergency_indicators):
                return True
            
            # Check category fields
            categories = resource.get('category', [])
            if isinstance(categories, list):
                for category in categories:
                    category_text = str(category).lower()
                    if any(indicator in category_text for indicator in self.emergency_indicators):
                        return True
        
        return False
    
    async def _has_rare_resources(self, resource_types: List[str]) -> bool:
        """Determine if bundle contains rare or uncommon resource types"""
        
        # Common resource types in typical clinical bundles
        common_types = {
            'Patient', 'MedicationRequest', 'ServiceRequest', 'Observation', 
            'Condition', 'Procedure', 'DiagnosticReport', 'Encounter'
        }
        
        rare_types = set(resource_types) - common_types
        
        # Consider bundle to have rare resources if >20% are uncommon types
        if resource_types:
            rare_percentage = len(rare_types) / len(resource_types)
            return rare_percentage > 0.2
        
        return False
    
    async def _select_optimal_tier(self, 
                                 complexity_score: float,
                                 rule_based_coverage: float,
                                 has_rare_resources: bool,
                                 has_emergency_indicators: bool,
                                 resource_count: int,
                                 unique_resource_types: int) -> ProcessingTier:
        """
        Select optimal processing tier based on analysis results
        Prioritizes cost optimization while maintaining quality
        """
        
        # Emergency situations may need LLM processing for comprehensive analysis
        if has_emergency_indicators and complexity_score > 6.0:
            return ProcessingTier.LLM_FALLBACK
        
        # Rule-based tier criteria (target: 70-80% of bundles)
        if (complexity_score <= self.criteria.max_complexity_for_rules and 
            rule_based_coverage >= (self.criteria.min_rule_coverage_percent / 100.0) and 
            not has_rare_resources):
            return ProcessingTier.RULE_BASED
        
        # Template tier criteria (target: 15-20% of bundles)  
        if (complexity_score <= self.criteria.max_complexity_for_templates and
            unique_resource_types <= self.criteria.max_resource_types_for_templates and
            rule_based_coverage >= 0.5):  # At least 50% coverage for template processing
            return ProcessingTier.GENERIC_TEMPLATE
        
        # LLM fallback tier (target: 5-10% of bundles)
        return ProcessingTier.LLM_FALLBACK
    
    async def _calculate_recommendation_confidence(self,
                                                 recommended_tier: ProcessingTier,
                                                 complexity_score: float,
                                                 rule_based_coverage: float,
                                                 resource_count: int) -> float:
        """Calculate confidence in tier recommendation (0.0-1.0)"""
        
        confidence = 0.8  # Base confidence
        
        if recommended_tier == ProcessingTier.RULE_BASED:
            # High confidence for well-covered, simple bundles
            if rule_based_coverage >= 0.9 and complexity_score <= 2.0:
                confidence = 0.95
            elif rule_based_coverage >= 0.8:
                confidence = 0.90
            else:
                confidence = 0.75
        
        elif recommended_tier == ProcessingTier.GENERIC_TEMPLATE:
            # Moderate confidence for template processing
            if complexity_score <= 4.0:
                confidence = 0.85
            else:
                confidence = 0.75
        
        elif recommended_tier == ProcessingTier.LLM_FALLBACK:
            # Lower confidence for complex bundles requiring LLM
            if complexity_score >= 8.0:
                confidence = 0.70
            else:
                confidence = 0.80
        
        # Adjust confidence based on resource count
        if resource_count <= 3:
            confidence += 0.05  # Simple bundles are easier to process
        elif resource_count >= 15:
            confidence -= 0.05  # Complex bundles are harder to process
        
        return max(0.0, min(1.0, confidence))
    
    async def _extract_specialty_context(self, resources: List[Dict]) -> Optional[str]:
        """Extract medical specialty context from bundle resources"""
        
        # Look for specialty indicators in resource categories or codes
        specialty_keywords = {
            'cardiology': ['cardiac', 'heart', 'cardio', 'ecg', 'echo'],
            'emergency': ['emergency', 'urgent', 'trauma', 'critical', 'stat'],
            'oncology': ['cancer', 'tumor', 'oncology', 'chemo', 'radiation'],
            'pediatric': ['pediatric', 'child', 'infant', 'newborn'],
            'psychiatry': ['mental', 'psychiatric', 'depression', 'anxiety'],
            'radiology': ['imaging', 'x-ray', 'ct', 'mri', 'ultrasound']
        }
        
        for resource in resources:
            # Check categories
            categories = resource.get('category', [])
            for category in categories:
                category_text = str(category).lower()
                for specialty, keywords in specialty_keywords.items():
                    if any(keyword in category_text for keyword in keywords):
                        return specialty
            
            # Check resource codes
            codes = []
            if 'code' in resource:
                codes.append(resource['code'])
            if 'medicationCodeableConcept' in resource:
                codes.append(resource['medicationCodeableConcept'])
            
            for code in codes:
                code_text = str(code).lower()
                for specialty, keywords in specialty_keywords.items():
                    if any(keyword in code_text for keyword in keywords):
                        return specialty
        
        return None
    
    async def _extract_urgency_level(self, resources: List[Dict]) -> Optional[str]:
        """Extract urgency level from bundle resources"""
        
        urgency_levels = {'stat': 3, 'urgent': 2, 'routine': 1}
        highest_urgency = 0
        highest_level = None
        
        for resource in resources:
            priority = resource.get('priority', '').lower()
            
            for level, score in urgency_levels.items():
                if level in priority and score > highest_urgency:
                    highest_urgency = score
                    highest_level = level
        
        return highest_level
    
    def _determine_primary_resource_type(self, resource_types: List[str]) -> Optional[str]:
        """Determine primary resource type based on frequency and importance"""
        
        if not resource_types:
            return None
        
        # Count resource type frequencies
        type_counts = {}
        for rt in resource_types:
            type_counts[rt] = type_counts.get(rt, 0) + 1
        
        # Priority order for clinical importance
        priority_types = [
            'MedicationRequest', 'ServiceRequest', 'Procedure',
            'Condition', 'Observation', 'DiagnosticReport'
        ]
        
        # Return highest priority type that exists
        for priority_type in priority_types:
            if priority_type in type_counts:
                return priority_type
        
        # Return most frequent type
        return max(type_counts.items(), key=lambda x: x[1])[0]
    
    def _create_empty_bundle_analysis(self, start_time: float) -> BundleAnalysis:
        """Create analysis for empty bundle"""
        
        analysis_time = (time.time() - start_time) * 1000
        
        return BundleAnalysis(
            resource_types=[],
            resource_count=0,
            primary_resource_type=None,
            complexity_score=0.0,
            has_rare_resources=False,
            has_emergency_indicators=False,
            recommended_tier=ProcessingTier.EMERGENCY_FALLBACK,
            confidence_score=0.1,
            analysis_timestamp=datetime.now(),
            analysis_duration_ms=analysis_time,
            rule_based_coverage=0.0,
            supported_resource_types=[],
            unsupported_resource_types=[],
            specialty_context=None,
            urgency_level=None,
            patient_demographics=None
        )