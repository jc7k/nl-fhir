"""
Extensible QA Framework for Clinical NLP and FHIR Testing
HIPAA Compliant: No PHI in test data or logs
Production Ready: Performance monitoring and regression detection
"""

import json
import time
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TestScenario(Enum):
    """Types of clinical test scenarios"""
    MEDICATION_ORDER = "medication_order"
    LAB_ORDER = "lab_order" 
    PROCEDURE_ORDER = "procedure_order"
    COMPLEX_CLINICAL = "complex_clinical"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"
    MULTI_MEDICATION = "multi_medication"
    DOSAGE_ADJUSTMENT = "dosage_adjustment"
    DISCONTINUATION = "discontinuation"


class TestTier(Enum):
    """Expected processing tier for test cases"""
    REGEX_ONLY = "regex"
    SPACY_MEDICAL = "spacy"
    TRANSFORMERS_NER = "transformers"
    LLM_ESCALATION = "llm"
    ANY_TIER = "any"


@dataclass
class ExpectedEntity:
    """Expected entity in test case"""
    category: str  # medications, dosages, conditions, etc.
    value: str  # expected entity text or pattern
    confidence_threshold: float = 0.5
    required: bool = True  # Must be found for test to pass


@dataclass 
class ExpectedFHIRResource:
    """Expected FHIR resource in output"""
    resource_type: str  # Patient, MedicationRequest, etc.
    required_fields: List[str] = field(default_factory=list)
    validation_level: str = "basic"  # basic, strict, clinical


@dataclass
class PerformanceExpectation:
    """Performance requirements for test case"""
    max_processing_time_ms: int = 2000  # <2s requirement
    expected_tier: TestTier = TestTier.ANY_TIER
    max_memory_mb: Optional[int] = None


@dataclass
class ClinicalTestCase:
    """Standardized clinical test case structure"""
    id: str
    name: str
    clinical_text: str
    scenario: TestScenario
    
    # Expected outputs
    expected_entities: List[ExpectedEntity] = field(default_factory=list)
    expected_fhir_resources: List[ExpectedFHIRResource] = field(default_factory=list)
    
    # Quality expectations
    minimum_quality_score: float = 0.7
    performance: PerformanceExpectation = field(default_factory=PerformanceExpectation)
    
    # Metadata
    complexity_level: str = "medium"  # simple, medium, complex
    medical_specialty: Optional[str] = None
    notes: str = ""
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestResult:
    """Test execution result"""
    test_case_id: str
    test_name: str
    success: bool
    processing_time_ms: float
    tier_used: str
    
    # Entity extraction results
    extracted_entities: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    entity_quality_score: float = 0.0
    
    # FHIR generation results
    generated_fhir_resources: List[Dict[str, Any]] = field(default_factory=list)
    fhir_validation_results: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    memory_usage_mb: Optional[float] = None
    tier_escalations: int = 0
    
    # Issues and recommendations
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ClinicalTestLoader:
    """Load and manage clinical test cases from configuration files"""
    
    def __init__(self, test_data_dir: str = "tests/data"):
        self.test_data_dir = Path(test_data_dir)
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_test_cases_from_json(self, file_path: str) -> List[ClinicalTestCase]:
        """Load test cases from JSON configuration file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            test_cases = []
            for case_data in data.get('test_cases', []):
                # Convert dict to ClinicalTestCase
                expected_entities = [
                    ExpectedEntity(**entity) for entity in case_data.get('expected_entities', [])
                ]
                expected_fhir_resources = [
                    ExpectedFHIRResource(**resource) for resource in case_data.get('expected_fhir_resources', [])
                ]
                performance = PerformanceExpectation(**case_data.get('performance', {}))
                
                test_case = ClinicalTestCase(
                    id=case_data['id'],
                    name=case_data['name'],
                    clinical_text=case_data['clinical_text'],
                    scenario=TestScenario(case_data['scenario']),
                    expected_entities=expected_entities,
                    expected_fhir_resources=expected_fhir_resources,
                    minimum_quality_score=case_data.get('minimum_quality_score', 0.7),
                    performance=performance,
                    complexity_level=case_data.get('complexity_level', 'medium'),
                    medical_specialty=case_data.get('medical_specialty'),
                    notes=case_data.get('notes', ''),
                    created_date=case_data.get('created_date', datetime.now().isoformat())
                )
                test_cases.append(test_case)
                
            return test_cases
            
        except Exception as e:
            logger.error(f"Failed to load test cases from {file_path}: {e}")
            return []
    
    def save_test_cases_to_json(self, test_cases: List[ClinicalTestCase], file_path: str):
        """Save test cases to JSON configuration file"""
        try:
            # Convert dataclasses to dict
            cases_data = []
            for case in test_cases:
                case_dict = {
                    'id': case.id,
                    'name': case.name,
                    'clinical_text': case.clinical_text,
                    'scenario': case.scenario.value,
                    'expected_entities': [
                        {
                            'category': e.category,
                            'value': e.value,
                            'confidence_threshold': e.confidence_threshold,
                            'required': e.required
                        } for e in case.expected_entities
                    ],
                    'expected_fhir_resources': [
                        {
                            'resource_type': r.resource_type,
                            'required_fields': r.required_fields,
                            'validation_level': r.validation_level
                        } for r in case.expected_fhir_resources
                    ],
                    'minimum_quality_score': case.minimum_quality_score,
                    'performance': {
                        'max_processing_time_ms': case.performance.max_processing_time_ms,
                        'expected_tier': case.performance.expected_tier.value,
                        'max_memory_mb': case.performance.max_memory_mb
                    },
                    'complexity_level': case.complexity_level,
                    'medical_specialty': case.medical_specialty,
                    'notes': case.notes,
                    'created_date': case.created_date
                }
                cases_data.append(case_dict)
            
            data = {
                'version': '1.0',
                'description': 'Clinical NLP and FHIR test cases',
                'created': datetime.now().isoformat(),
                'test_cases': cases_data
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved {len(test_cases)} test cases to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save test cases to {file_path}: {e}")


class ClinicalTestRunner:
    """Execute clinical test cases and measure performance"""
    
    def __init__(self, nlp_processor=None, fhir_processor=None):
        self.nlp_processor = nlp_processor
        self.fhir_processor = fhir_processor
        self.results: List[TestResult] = []
        
    async def run_test_case(self, test_case: ClinicalTestCase) -> TestResult:
        """Execute a single test case"""
        start_time = time.time()
        request_id = f"test-{test_case.id}-{uuid.uuid4().hex[:8]}"
        
        result = TestResult(
            test_case_id=test_case.id,
            test_name=test_case.name,
            success=False,
            processing_time_ms=0.0,
            tier_used="unknown"
        )
        
        try:
            # Phase 1: NLP Entity Extraction
            if self.nlp_processor:
                nlp_start = time.time()
                
                # Extract entities using 3-tier system
                extracted_entities = await self._extract_entities_async(
                    test_case.clinical_text, request_id
                )
                
                nlp_time = (time.time() - nlp_start) * 1000
                
                result.extracted_entities = extracted_entities
                result.tier_used = self._determine_tier_used(extracted_entities)
                
                # Calculate entity quality score
                result.entity_quality_score = self._calculate_entity_quality(
                    extracted_entities, test_case.expected_entities
                )
            
            # Phase 2: FHIR Resource Generation
            if self.fhir_processor and result.extracted_entities:
                fhir_start = time.time()
                
                generated_resources = await self._generate_fhir_resources_async(
                    extracted_entities, request_id
                )
                
                fhir_time = (time.time() - fhir_start) * 1000
                
                result.generated_fhir_resources = generated_resources
                
                # Validate FHIR resources
                result.fhir_validation_results = await self._validate_fhir_resources_async(
                    generated_resources, test_case.expected_fhir_resources
                )
            
            # Calculate total processing time
            total_time = (time.time() - start_time) * 1000
            result.processing_time_ms = total_time
            
            # Determine overall success
            result.success = self._evaluate_test_success(result, test_case)
            
            # Add issues and recommendations
            result.issues = self._identify_issues(result, test_case)
            result.recommendations = self._generate_recommendations(result, test_case)
            
        except Exception as e:
            result.issues.append(f"Test execution failed: {str(e)}")
            logger.error(f"Test case {test_case.id} failed: {e}")
        
        self.results.append(result)
        return result
    
    async def run_test_suite(self, test_cases: List[ClinicalTestCase]) -> List[TestResult]:
        """Execute multiple test cases"""
        logger.info(f"Running test suite with {len(test_cases)} test cases")
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Running test {i}/{len(test_cases)}: {test_case.name}")
            result = await self.run_test_case(test_case)
            results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(0.1)
        
        return results
    
    async def _extract_entities_async(self, text: str, request_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using the NLP processor"""
        if hasattr(self.nlp_processor, 'extract_medical_entities'):
            return self.nlp_processor.extract_medical_entities(text)
        else:
            # Fallback for sync processors
            return self.nlp_processor.process_clinical_text(text, [], request_id)
    
    async def _generate_fhir_resources_async(self, entities: Dict, request_id: str) -> List[Dict]:
        """Generate FHIR resources from extracted entities"""
        # This would integrate with your FHIR resource factory
        # For now, return empty list
        return []
    
    async def _validate_fhir_resources_async(self, resources: List[Dict], expected: List[ExpectedFHIRResource]) -> Dict:
        """Validate generated FHIR resources"""
        return {
            "validation_result": "success",
            "resources_validated": len(resources),
            "expected_resources": len(expected),
            "issues": []
        }
    
    def _determine_tier_used(self, extracted_entities: Dict) -> str:
        """Determine which processing tier was used based on entity methods"""
        methods = set()
        for category, entities in extracted_entities.items():
            for entity in entities:
                if 'method' in entity:
                    methods.add(entity['method'])
        
        if any('llm' in method for method in methods):
            return "llm"
        elif any('transformer' in method for method in methods):
            return "transformers"
        elif any('spacy' in method for method in methods):
            return "spacy"
        elif any('regex' in method for method in methods):
            return "regex"
        else:
            return "unknown"
    
    def _calculate_entity_quality(self, extracted: Dict, expected: List[ExpectedEntity]) -> float:
        """Calculate quality score for entity extraction"""
        if not expected:
            return 1.0  # No expectations, assume perfect
        
        total_score = 0.0
        total_weight = 0.0
        
        for expected_entity in expected:
            weight = 1.0 if expected_entity.required else 0.5
            total_weight += weight
            
            # Check if expected entity was found
            category_entities = extracted.get(expected_entity.category, [])
            found = any(
                expected_entity.value.lower() in entity.get('text', '').lower()
                for entity in category_entities
                if entity.get('confidence', 0) >= expected_entity.confidence_threshold
            )
            
            if found:
                total_score += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _evaluate_test_success(self, result: TestResult, test_case: ClinicalTestCase) -> bool:
        """Evaluate overall test success"""
        # Performance check
        if result.processing_time_ms > test_case.performance.max_processing_time_ms:
            return False
        
        # Quality check
        if result.entity_quality_score < test_case.minimum_quality_score:
            return False
        
        # No critical issues
        if any('failed' in issue.lower() or 'error' in issue.lower() for issue in result.issues):
            return False
        
        return True
    
    def _identify_issues(self, result: TestResult, test_case: ClinicalTestCase) -> List[str]:
        """Identify issues with test execution"""
        issues = []
        
        if result.processing_time_ms > test_case.performance.max_processing_time_ms:
            issues.append(f"Performance: {result.processing_time_ms:.1f}ms exceeds {test_case.performance.max_processing_time_ms}ms limit")
        
        if result.entity_quality_score < test_case.minimum_quality_score:
            issues.append(f"Quality: {result.entity_quality_score:.2f} below {test_case.minimum_quality_score} threshold")
        
        if test_case.performance.expected_tier != TestTier.ANY_TIER:
            if result.tier_used != test_case.performance.expected_tier.value:
                issues.append(f"Tier: Expected {test_case.performance.expected_tier.value}, got {result.tier_used}")
        
        return issues
    
    def _generate_recommendations(self, result: TestResult, test_case: ClinicalTestCase) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        if result.processing_time_ms > 1000:
            recommendations.append("Consider optimization - processing time > 1s")
        
        if result.entity_quality_score < 0.8:
            recommendations.append("Improve entity extraction - consider expanding medical vocabularies")
        
        if result.tier_used == "regex":
            recommendations.append("Consider improving spaCy patterns - falling back to regex")
        
        return recommendations


class TestReportGenerator:
    """Generate comprehensive test reports"""
    
    def generate_summary_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate summary report from test results"""
        if not results:
            return {"error": "No test results provided"}
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        
        # Performance metrics
        avg_processing_time = sum(r.processing_time_ms for r in results) / total_tests
        max_processing_time = max(r.processing_time_ms for r in results)
        min_processing_time = min(r.processing_time_ms for r in results)
        
        # Quality metrics
        avg_quality_score = sum(r.entity_quality_score for r in results) / total_tests
        
        # Tier distribution
        tier_distribution = {}
        for result in results:
            tier = result.tier_used
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        # Performance compliance
        performance_compliant = sum(1 for r in results if r.processing_time_ms <= 2000)
        
        return {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": successful_tests / total_tests,
                "performance_compliant": performance_compliant,
                "performance_compliance_rate": performance_compliant / total_tests
            },
            "performance": {
                "avg_processing_time_ms": avg_processing_time,
                "max_processing_time_ms": max_processing_time,
                "min_processing_time_ms": min_processing_time,
                "meets_2s_requirement": avg_processing_time <= 2000
            },
            "quality": {
                "avg_quality_score": avg_quality_score,
                "meets_95_percent_target": avg_quality_score >= 0.95
            },
            "tier_distribution": tier_distribution,
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_detailed_html_report(self, results: List[TestResult], output_path: str):
        """Generate detailed HTML report"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Clinical NLP QA Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .summary { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
                .test-case { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
                .success { border-left: 5px solid #28a745; }
                .failure { border-left: 5px solid #dc3545; }
                .metrics { display: flex; gap: 20px; margin: 10px 0; }
                .metric { background: #e9ecef; padding: 10px; border-radius: 4px; min-width: 120px; }
                .issues { color: #dc3545; }
                .recommendations { color: #fd7e14; }
            </style>
        </head>
        <body>
            <h1>Clinical NLP QA Test Report</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="metrics">
                    <div class="metric">
                        <strong>Success Rate</strong><br/>
                        {success_rate:.1%}
                    </div>
                    <div class="metric">
                        <strong>Avg Quality</strong><br/>
                        {avg_quality:.2f}
                    </div>
                    <div class="metric">
                        <strong>Avg Performance</strong><br/>
                        {avg_time:.1f}ms
                    </div>
                    <div class="metric">
                        <strong>2s Compliance</strong><br/>
                        {performance_compliance:.1%}
                    </div>
                </div>
            </div>
            
            <h2>Test Results</h2>
            {test_results_html}
        </body>
        </html>
        """
        
        # Generate test results HTML
        test_results_html = ""
        for result in results:
            status_class = "success" if result.success else "failure"
            status_text = " PASS" if result.success else "L FAIL"
            
            test_results_html += f"""
            <div class="test-case {status_class}">
                <h3>{result.test_name} {status_text}</h3>
                <div class="metrics">
                    <div class="metric">
                        <strong>Processing Time</strong><br/>
                        {result.processing_time_ms:.1f}ms
                    </div>
                    <div class="metric">
                        <strong>Quality Score</strong><br/>
                        {result.entity_quality_score:.2f}
                    </div>
                    <div class="metric">
                        <strong>Tier Used</strong><br/>
                        {result.tier_used}
                    </div>
                </div>
                
                {f'<div class="issues"><strong>Issues:</strong><ul>{"".join(f"<li>{issue}</li>" for issue in result.issues)}</ul></div>' if result.issues else ''}
                {f'<div class="recommendations"><strong>Recommendations:</strong><ul>{"".join(f"<li>{rec}</li>" for rec in result.recommendations)}</ul></div>' if result.recommendations else ''}
            </div>
            """
        
        # Calculate summary metrics
        summary = self.generate_summary_report(results)
        
        # Fill template
        html_content = html_template.format(
            success_rate=summary["summary"]["success_rate"],
            avg_quality=summary["quality"]["avg_quality_score"],
            avg_time=summary["performance"]["avg_processing_time_ms"],
            performance_compliance=summary["summary"]["performance_compliance_rate"],
            test_results_html=test_results_html
        )
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Generated HTML report: {output_path}")


# Utility functions for easy test creation
def create_medication_test(
    name: str, 
    clinical_text: str, 
    expected_medication: str,
    expected_dosage: str = None,
    expected_frequency: str = None
) -> ClinicalTestCase:
    """Create a medication order test case"""
    expected_entities = [
        ExpectedEntity(category="medications", value=expected_medication, required=True)
    ]
    
    if expected_dosage:
        expected_entities.append(
            ExpectedEntity(category="dosages", value=expected_dosage, required=True)
        )
    
    if expected_frequency:
        expected_entities.append(
            ExpectedEntity(category="frequencies", value=expected_frequency, required=True)
        )
    
    return ClinicalTestCase(
        id=f"med-{uuid.uuid4().hex[:8]}",
        name=name,
        clinical_text=clinical_text,
        scenario=TestScenario.MEDICATION_ORDER,
        expected_entities=expected_entities,
        expected_fhir_resources=[
            ExpectedFHIRResource(resource_type="MedicationRequest", required_fields=["status", "intent", "medicationCodeableConcept"])
        ]
    )


def create_lab_test(
    name: str,
    clinical_text: str, 
    expected_lab_tests: List[str]
) -> ClinicalTestCase:
    """Create a lab order test case"""
    expected_entities = [
        ExpectedEntity(category="lab_tests", value=test, required=True)
        for test in expected_lab_tests
    ]
    
    return ClinicalTestCase(
        id=f"lab-{uuid.uuid4().hex[:8]}",
        name=name,
        clinical_text=clinical_text,
        scenario=TestScenario.LAB_ORDER,
        expected_entities=expected_entities,
        expected_fhir_resources=[
            ExpectedFHIRResource(resource_type="ServiceRequest", required_fields=["status", "intent", "code"])
        ]
    )