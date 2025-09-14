#!/usr/bin/env python3
"""
Smart Regex Consolidator - Phase 1 of 3-Tier Architecture Migration

This system replaces the Transformer NER tier (Tier 2) with an intelligent
regex consolidation system that merges extracted transformer patterns with
enhanced regex patterns for optimal performance.

Design Philosophy:
- Preserve valuable patterns from transformer intelligence extraction
- Create hierarchical pattern matching with confidence weighting
- Provide intelligent gap filling for MedSpaCy missed entities
- Maintain high speed with pattern-based approach
"""

import re
import time
import json
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class SmartRegexConsolidator:
    """
    Intelligent Tier 2 replacement: Smart pattern matching with learned insights

    This class consolidates:
    - Extracted transformer intelligence patterns
    - Enhanced regex patterns from current Tier 3
    - Medical abbreviation and terminology patterns
    - Intelligent confidence weighting system
    """

    def __init__(self):
        self.pattern_hierarchy = self._build_pattern_hierarchy()
        self.confidence_weights = self._load_confidence_weights()
        self.gap_fill_patterns = self._build_gap_fill_patterns()
        self.medical_abbreviations = self._build_medical_abbreviations()

        # Performance tracking
        self.pattern_performance = {}

    def _build_pattern_hierarchy(self) -> Dict:
        """Build hierarchical patterns based on transformer intelligence extraction"""

        return {
            # Level 1: High-confidence patterns (from intelligence extraction)
            "high_confidence": {
                "confidence_boost": 0.9,
                "patterns": {
                    # Dosage patterns learned from transformer (successful extractions)
                    "dosage_concentration": [
                        r"(\d+(?:\.\d+)?)\s*mg/(\d+(?:\.\d+)?)\s*ml",  # 250mg/5ml pattern
                        r"(\d+(?:\.\d+)?)\s*mg\s*/\s*(\d+(?:\.\d+)?)\s*ml",  # 100mg / 5ml variation
                        r"(\d+(?:\.\d+)?)\s*mg\s*per\s*(\d+(?:\.\d+)?)\s*ml"  # per format
                    ],
                    "dosage_simple": [
                        r"(\d+(?:\.\d+)?)\s*mg\s+daily",  # 10mg daily (transformer success)
                        r"(\d+(?:\.\d+)?)\s*mg\s+(?:once\s+)?daily",
                        r"(\d+(?:\.\d+)?)\s*mg\s+per\s+day"
                    ],
                    "liquid_medications": [
                        r"(\w+)\s+suspension",  # amoxicillin suspension
                        r"(\w+)\s+drops",
                        r"(\w+)\s+syrup",
                        r"liquid\s+(\w+)"
                    ]
                }
            },

            # Level 2: Medium-confidence patterns (enhanced from existing regex)
            "medium_confidence": {
                "confidence_boost": 0.75,
                "patterns": {
                    "medications_extended": [
                        # Enhanced from current fallback patterns
                        r"(?:start|begin|give|administer|prescribe)\s+(\w+(?:\s+\w+)?)",
                        r"(\w+)\s+(?:\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml))",
                        r"patient\s+(?:on|taking)\s+(\w+)"
                    ],
                    "frequency_clinical": [
                        r"\b((?:q|every)\s*\d+\s*h(?:ours?)?)\b",  # q6h, every 4 hours
                        r"\b(\d+\s*times?\s*(?:per\s+)?(?:day|daily))\b",
                        r"\b(prn|as\s+needed|when\s+needed)\b"
                    ],
                    "route_extraction": [
                        # Enhanced route patterns from Epic 2.5 implementation
                        r"\b(IV\s+push|IV\s+bolus|IM\s+injection)\b",
                        r"\b(PO|by\s+mouth|orally|oral)\b",
                        r"\b(sublingual|SL|under\s+tongue)\b"
                    ]
                }
            },

            # Level 3: Low-confidence patterns (safety net/catch-all)
            "low_confidence": {
                "confidence_boost": 0.5,
                "patterns": {
                    "generic_medical": [
                        r"\b(\w+(?:cillin|mycin|oxin|ide|ine|ol))\b",  # Common medication suffixes
                        r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?))\b",  # Generic dosages
                        r"\b(daily|twice|thrice|weekly|monthly)\b"  # Basic frequencies
                    ],
                    "condition_indicators": [
                        r"\bfor\s+(\w+(?:\s+\w+){0,3})\b",  # "for diabetes", "for chest pain"
                        r"\btreating?\s+(\w+(?:\s+\w+){0,2})\b",
                        r"\bdiagnosed?\s+with\s+(\w+(?:\s+\w+){0,2})\b"
                    ]
                }
            }
        }

    def _load_confidence_weights(self) -> Dict:
        """Load confidence weights from transformer intelligence extraction"""

        # Based on intelligence extraction results
        return {
            "dosages": {
                "avg_confidence": 0.806,  # From transformer analysis: [0.800, 0.859, 0.760]
                "confidence_threshold": 0.76,  # Minimum from successful extractions
                "reliability_factor": 0.9  # High reliability for dosage patterns
            },
            "medications": {
                "avg_confidence": 0.65,  # Conservative estimate
                "confidence_threshold": 0.6,
                "reliability_factor": 0.85
            },
            "frequencies": {
                "avg_confidence": 0.7,
                "confidence_threshold": 0.6,
                "reliability_factor": 0.8
            }
        }

    def _build_gap_fill_patterns(self) -> Dict:
        """Build patterns to fill gaps identified in transformer intelligence extraction"""

        # Based on gap analysis: transformer caught "TID" that MedSpaCy missed
        return {
            "frequency_abbreviations": [
                r"\b(TID|t\.i\.d\.)\b",  # Three times daily (intelligence gap)
                r"\b(BID|b\.i\.d\.)\b",  # Twice daily
                r"\b(QID|q\.i\.d\.)\b",  # Four times daily
                r"\b(QD|q\.d\.)\b",      # Once daily
                r"\b(PRN|p\.r\.n\.)\b"   # As needed
            ],
            "condition_extraction": [
                # Gap: "otitis media" was missed by MedSpaCy
                r"\b(otitis\s+media)\b",
                r"\b(chest\s+pain)\b",
                r"\b(type\s+2\s+diabetes)\b",
                r"\b(diabetes\s+mellitus)\b"
            ]
        }

    def _build_medical_abbreviations(self) -> Dict:
        """Enhanced medical abbreviation patterns"""

        return {
            "routes": [
                ("PO", "oral"),
                ("IV", "intravenous"),
                ("IM", "intramuscular"),
                ("SL", "sublingual"),
                ("SC", "subcutaneous"),
                ("SQ", "subcutaneous")
            ],
            "frequencies": [
                ("BID", "twice daily"),
                ("TID", "three times daily"),
                ("QID", "four times daily"),
                ("QD", "once daily"),
                ("PRN", "as needed")
            ],
            "urgency": [
                ("STAT", "immediately"),
                ("ASAP", "as soon as possible"),
                ("URGENT", "urgent")
            ]
        }

    def extract_with_smart_consolidation(self, text: str, medspacy_results: Dict) -> Dict:
        """
        Main consolidation method: intelligently fill gaps in MedSpaCy results

        Args:
            text: Original clinical text
            medspacy_results: Results from Tier 1 MedSpaCy processing

        Returns:
            Enhanced results with smart regex gap filling
        """

        start_time = time.time()

        # Start with MedSpaCy results as foundation
        consolidated_results = self._deep_copy_results(medspacy_results)

        # Apply hierarchical pattern matching to fill gaps
        gap_analysis = self._analyze_extraction_gaps(text, consolidated_results)

        if gap_analysis["needs_enhancement"]:
            logger.info(f"Smart consolidation: Filling {len(gap_analysis['gaps'])} identified gaps")

            # Apply pattern hierarchy in order of confidence
            for confidence_level in ["high_confidence", "medium_confidence", "low_confidence"]:
                enhanced_results = self._apply_pattern_level(
                    text,
                    consolidated_results,
                    confidence_level,
                    gap_analysis
                )

                # Update consolidated results with non-overlapping extractions
                consolidated_results = self._merge_non_overlapping(
                    consolidated_results,
                    enhanced_results
                )

                # Check if we have sufficient coverage to stop early
                if self._has_sufficient_coverage(consolidated_results, text):
                    logger.info(f"Early stop at {confidence_level} - sufficient coverage achieved")
                    break

        # Apply medical abbreviation expansion
        consolidated_results = self._expand_medical_abbreviations(consolidated_results, text)

        # Calculate final confidence scores
        consolidated_results = self._calculate_consolidation_confidence(consolidated_results)

        processing_time = time.time() - start_time

        # Add consolidation metadata
        self._add_consolidation_metadata(consolidated_results, processing_time, gap_analysis)

        return consolidated_results

    def _analyze_extraction_gaps(self, text: str, medspacy_results: Dict) -> Dict:
        """Analyze what entities might be missing from MedSpaCy extraction"""

        gap_analysis = {
            "needs_enhancement": False,
            "gaps": [],
            "text_complexity": "low",
            "clinical_indicators": []
        }

        text_lower = text.lower()

        # Check for clinical action words that suggest missing entities
        clinical_actions = ["start", "begin", "give", "administer", "prescribe", "order", "continue", "stop"]
        has_clinical_actions = any(action in text_lower for action in clinical_actions)

        # Check for dosage patterns without medication extraction
        dosage_pattern = r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?)"
        has_dosage_patterns = bool(re.search(dosage_pattern, text_lower))

        # Check for frequency patterns without frequency extraction
        frequency_pattern = r"\b(?:daily|twice|bid|tid|qid|prn|q\d+h)\b"
        has_frequency_patterns = bool(re.search(frequency_pattern, text_lower))

        # Analyze current extraction coverage
        total_entities = sum(len(entities) for entities in medspacy_results.values())
        words_in_text = len(text.split())
        entity_density = total_entities / max(words_in_text, 1)

        # Determine if enhancement is needed
        if has_clinical_actions and entity_density < 0.2:
            gap_analysis["gaps"].append("low_entity_density_with_clinical_actions")
            gap_analysis["needs_enhancement"] = True

        if has_dosage_patterns and len(medspacy_results.get("dosages", [])) == 0:
            gap_analysis["gaps"].append("dosage_patterns_without_extraction")
            gap_analysis["needs_enhancement"] = True

        if has_frequency_patterns and len(medspacy_results.get("frequencies", [])) == 0:
            gap_analysis["gaps"].append("frequency_patterns_without_extraction")
            gap_analysis["needs_enhancement"] = True

        # Text complexity assessment
        if len(text.split()) > 15 and entity_density < 0.15:
            gap_analysis["text_complexity"] = "high"
            gap_analysis["needs_enhancement"] = True

        return gap_analysis

    def _apply_pattern_level(self, text: str, current_results: Dict, confidence_level: str, gap_analysis: Dict) -> Dict:
        """Apply patterns from specific confidence level"""

        level_config = self.pattern_hierarchy[confidence_level]
        new_extractions = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": []
        }

        # Apply patterns based on identified gaps
        patterns = level_config["patterns"]
        confidence_boost = level_config["confidence_boost"]

        # Apply dosage patterns if dosage gap identified
        if "dosage_patterns_without_extraction" in gap_analysis["gaps"]:
            if "dosage_concentration" in patterns:
                new_extractions["dosages"].extend(
                    self._extract_with_patterns(text, patterns["dosage_concentration"], "dosage", confidence_boost)
                )
            if "dosage_simple" in patterns:
                new_extractions["dosages"].extend(
                    self._extract_with_patterns(text, patterns["dosage_simple"], "dosage", confidence_boost)
                )

        # Apply frequency patterns if frequency gap identified
        if "frequency_patterns_without_extraction" in gap_analysis["gaps"]:
            if "frequency_clinical" in patterns:
                new_extractions["frequencies"].extend(
                    self._extract_with_patterns(text, patterns["frequency_clinical"], "frequency", confidence_boost)
                )

            # Apply gap fill patterns for specific frequency abbreviations
            new_extractions["frequencies"].extend(
                self._extract_with_patterns(text, self.gap_fill_patterns["frequency_abbreviations"], "frequency", confidence_boost)
            )

        # Apply medication patterns for low entity density
        if "low_entity_density_with_clinical_actions" in gap_analysis["gaps"]:
            if "medications_extended" in patterns:
                new_extractions["medications"].extend(
                    self._extract_with_patterns(text, patterns["medications_extended"], "medication", confidence_boost)
                )
            if "liquid_medications" in patterns:
                new_extractions["medications"].extend(
                    self._extract_with_patterns(text, patterns["liquid_medications"], "medication", confidence_boost)
                )

        return new_extractions

    def _extract_with_patterns(self, text: str, patterns: List[str], entity_type: str, confidence_boost: float) -> List[Dict]:
        """Extract entities using list of regex patterns"""

        extractions = []

        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    # Determine extracted text (use first group if available, else full match)
                    if match.groups():
                        entity_text = match.group(1)
                    else:
                        entity_text = match.group(0)

                    # Skip very short matches (likely noise)
                    if len(entity_text.strip()) < 2:
                        continue

                    # Calculate pattern-specific confidence
                    base_confidence = self.confidence_weights.get(entity_type + "s", {}).get("avg_confidence", 0.7)
                    final_confidence = min(0.95, base_confidence * confidence_boost)

                    extraction = {
                        "text": entity_text.strip(),
                        "confidence": final_confidence,
                        "start": match.start(),
                        "end": match.end(),
                        "method": "smart_regex_consolidation",
                        "pattern": pattern,
                        "confidence_level": confidence_boost
                    }

                    extractions.append(extraction)

            except re.error as e:
                logger.warning(f"Regex pattern error: {pattern} - {e}")
                continue

        return extractions

    def _merge_non_overlapping(self, base_results: Dict, new_results: Dict) -> Dict:
        """Merge new extractions with base results, avoiding duplicates"""

        merged_results = self._deep_copy_results(base_results)

        for category, new_entities in new_results.items():
            base_entities = merged_results.get(category, [])

            for new_entity in new_entities:
                # Check if this entity adds value (not duplicate)
                if not self._is_entity_duplicate(new_entity, base_entities):
                    merged_results[category].append(new_entity)

        return merged_results

    def _is_entity_duplicate(self, new_entity: Dict, existing_entities: List[Dict]) -> bool:
        """Check if new entity is duplicate of existing entities"""

        new_text = new_entity.get("text", "").lower().strip()

        for existing in existing_entities:
            existing_text = existing.get("text", "").lower().strip()

            # Check for exact match or substantial overlap
            if new_text == existing_text:
                return True
            if new_text in existing_text or existing_text in new_text:
                # If there's substantial overlap, keep the higher confidence one
                if new_entity.get("confidence", 0) <= existing.get("confidence", 0):
                    return True

        return False

    def _expand_medical_abbreviations(self, results: Dict, text: str) -> Dict:
        """Expand medical abbreviations in extraction results"""

        expanded_results = self._deep_copy_results(results)

        # Expand abbreviations in each category
        for category, entities in expanded_results.items():
            for entity in entities:
                entity_text = entity.get("text", "")

                # Check for abbreviation expansion
                for abbrev_category, abbreviations in self.medical_abbreviations.items():
                    for abbrev, full_form in abbreviations:
                        if entity_text.upper() == abbrev:
                            entity["expanded_form"] = full_form
                            entity["abbreviation"] = True
                            break

        return expanded_results

    def _calculate_consolidation_confidence(self, results: Dict) -> Dict:
        """Calculate final confidence scores for consolidated results"""

        for category, entities in results.items():
            for entity in entities:
                # Apply category-specific confidence adjustments
                category_weights = self.confidence_weights.get(category, {})
                reliability_factor = category_weights.get("reliability_factor", 0.8)

                # Adjust confidence based on method
                method = entity.get("method", "")
                if method == "smart_regex_consolidation":
                    # Smart regex gets slight confidence boost for successful pattern matching
                    entity["confidence"] = min(0.95, entity.get("confidence", 0.7) * reliability_factor)
                elif "medspacy" in method:
                    # MedSpaCy results maintain their original confidence
                    pass

                # Add consolidation metadata
                entity["consolidation_processed"] = True

        return results

    def _has_sufficient_coverage(self, results: Dict, text: str) -> bool:
        """Check if current extraction provides sufficient coverage"""

        total_entities = sum(len(entities) for entities in results.values())
        words_in_text = len(text.split())
        entity_density = total_entities / max(words_in_text, 1)

        # Sufficient coverage if we have reasonable entity density
        return entity_density >= 0.2 and total_entities >= 2

    def _add_consolidation_metadata(self, results: Dict, processing_time: float, gap_analysis: Dict) -> None:
        """Add metadata about consolidation process"""

        results["_consolidation_metadata"] = {
            "processing_time": processing_time,
            "gaps_identified": gap_analysis["gaps"],
            "enhancement_applied": gap_analysis["needs_enhancement"],
            "text_complexity": gap_analysis["text_complexity"],
            "total_entities": sum(len(entities) for entities in results.values() if isinstance(entities, list)),
            "consolidation_version": "smart_regex_v1.0"
        }

    def _deep_copy_results(self, results: Dict) -> Dict:
        """Create deep copy of results dictionary with proper field initialization"""

        # Initialize all expected fields
        copied_results = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "conditions": [],
            "lab_tests": [],
            "procedures": [],
            "patients": []
        }

        # Copy over existing results
        for category, entities in results.items():
            if isinstance(entities, list):
                copied_results[category] = [entity.copy() if hasattr(entity, 'copy') else entity for entity in entities]
            else:
                copied_results[category] = entities

        return copied_results

def main():
    """Test the Smart Regex Consolidator"""

    print("🧠 SMART REGEX CONSOLIDATOR - Testing")
    print("=" * 50)

    consolidator = SmartRegexConsolidator()

    # Test cases
    test_cases = [
        {
            "text": "Start amoxicillin suspension 250mg/5ml, give 5ml TID for otitis media",
            "medspacy_mock": {
                "medications": [{"text": "amoxicillin", "confidence": 0.8, "method": "medspacy"}],
                "dosages": [],
                "frequencies": [],
                "conditions": []
            }
        },
        {
            "text": "Patient on Metformin 500mg BID for diabetes",
            "medspacy_mock": {
                "medications": [{"text": "Metformin", "confidence": 0.9, "method": "medspacy"}],
                "dosages": [{"text": "500mg", "confidence": 0.8, "method": "medspacy"}],
                "frequencies": [],
                "conditions": []
            }
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {case['text']}")
        print("-" * 40)

        start_time = time.time()
        results = consolidator.extract_with_smart_consolidation(
            case["text"],
            case["medspacy_mock"]
        )
        processing_time = time.time() - start_time

        print(f"Processing time: {processing_time*1000:.1f}ms")
        print(f"Total entities: {sum(len(entities) for entities in results.values() if isinstance(entities, list))}")

        for category, entities in results.items():
            if isinstance(entities, list) and entities:
                print(f"{category}: {[e['text'] for e in entities]}")

        if "_consolidation_metadata" in results:
            metadata = results["_consolidation_metadata"]
            print(f"Gaps filled: {metadata['gaps_identified']}")
            print(f"Enhancement: {metadata['enhancement_applied']}")

if __name__ == "__main__":
    main()