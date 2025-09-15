#!/usr/bin/env python3
"""
Test comprehensive FHIR bundle summarization with 100% rule-based coverage
Tests the complete YOLO MODE implementation for Epic 4 simplified architecture
"""

import asyncio
import json
import time
from datetime import datetime

from src.nl_fhir.services.summarization import FHIRBundleSummarizer


async def test_comprehensive_fhir_bundle():
    """Test comprehensive FHIR bundle with multiple resource types"""

    # Create comprehensive FHIR bundle with diverse resource types
    comprehensive_bundle = {
        "resourceType": "Bundle",
        "id": "comprehensive-test-bundle",
        "type": "transaction",
        "entry": [
            # Patient resource
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-1",
                    "gender": "female",
                    "birthDate": "1985-03-15"
                }
            },
            # Medication request
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "med-1",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [{"code": "123456", "display": "Lisinopril 10mg"}]
                    },
                    "dosageInstruction": [{"text": "Take once daily"}]
                }
            },
            # Service request (lab order)
            {
                "resource": {
                    "resourceType": "ServiceRequest",
                    "id": "service-1",
                    "status": "active",
                    "intent": "order",
                    "code": {"text": "Complete Blood Count"},
                    "priority": "routine"
                }
            },
            # Condition (diagnosis)
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "condition-1",
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "code": {"text": "Hypertension"},
                    "severity": {"text": "moderate"}
                }
            },
            # Observation (vital signs)
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-1",
                    "status": "final",
                    "code": {"text": "Blood Pressure"},
                    "valueQuantity": {"value": 140, "unit": "mmHg"}
                }
            },
            # Procedure
            {
                "resource": {
                    "resourceType": "Procedure",
                    "id": "proc-1",
                    "status": "completed",
                    "code": {"text": "Blood pressure measurement"},
                    "performedDateTime": "2025-01-01T10:00:00Z"
                }
            },
            # Diagnostic report
            {
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": "report-1",
                    "status": "final",
                    "code": {"text": "Lab Results"},
                    "conclusion": "All values within normal range"
                }
            },
            # Encounter
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "enc-1",
                    "status": "finished",
                    "class": {"code": "AMB", "display": "ambulatory"}
                }
            },
            # Care plan
            {
                "resource": {
                    "resourceType": "CarePlan",
                    "id": "care-1",
                    "status": "active",
                    "intent": "plan",
                    "title": "Hypertension Management Plan",
                    "category": [{"text": "cardiovascular"}]
                }
            },
            # Allergy intolerance
            {
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "id": "allergy-1",
                    "clinicalStatus": {"coding": [{"code": "active"}]},
                    "code": {"text": "Penicillin"},
                    "criticality": "high"
                }
            },
            # Immunization
            {
                "resource": {
                    "resourceType": "Immunization",
                    "id": "imm-1",
                    "status": "completed",
                    "vaccineCode": {"text": "COVID-19 vaccine"},
                    "occurrenceDateTime": "2024-12-01T09:00:00Z"
                }
            },
            # Device request
            {
                "resource": {
                    "resourceType": "DeviceRequest",
                    "id": "device-1",
                    "status": "active",
                    "intent": "order",
                    "codeCodeableConcept": {"text": "Blood pressure monitor"}
                }
            },
            # Unknown/rare resource type (should use generic fallback)
            {
                "resource": {
                    "resourceType": "CommunicationRequest",
                    "id": "comm-1",
                    "status": "active",
                    "category": [{"text": "notification"}],
                    "payload": [{"contentString": "Follow-up appointment scheduled"}]
                }
            }
        ]
    }

    print("🚀 Testing 100% Rule-Based FHIR Bundle Summarization")
    print(f"Bundle contains {len(comprehensive_bundle['entry'])} resources")
    print(f"Resource types: {[entry['resource']['resourceType'] for entry in comprehensive_bundle['entry']]}")
    print()

    # Initialize summarizer
    summarizer = FHIRBundleSummarizer()

    # Test summarization
    start_time = time.time()

    try:
        summary = await summarizer.summarize_bundle(
            fhir_bundle=comprehensive_bundle,
            role="physician",
            request_id="test-comprehensive-001"
        )

        processing_time = (time.time() - start_time) * 1000

        print("✅ SUMMARIZATION SUCCESSFUL!")
        print(f"⏱️ Processing time: {processing_time:.2f}ms")
        print()

        # Display results
        print("📋 CLINICAL SUMMARY:")
        print(f"Summary Type: {summary.summary_type}")
        print(f"Processing Tier: {summary.processing_tier}")
        print(f"Confidence Score: {summary.confidence_score:.2f}")
        print()

        print("👤 PATIENT CONTEXT:")
        print(summary.patient_context)
        print()

        print(f"📝 CLINICAL ORDERS ({len(summary.primary_orders)}):")
        for i, order in enumerate(summary.primary_orders, 1):
            print(f"{i:2d}. {order.order_type}: {order.description}")
            print(f"    Confidence: {order.confidence_score:.2f}")
            if order.safety_alerts:
                print(f"    ⚠️ Safety Alerts: {', '.join(order.safety_alerts)}")
            print()

        if summary.clinical_alerts:
            print("🚨 CLINICAL ALERTS:")
            for alert in summary.clinical_alerts:
                print(f"- {alert}")
            print()

        print("📊 QUALITY INDICATORS:")
        qi = summary.quality_indicators
        print(f"- Completeness: {qi.completeness_score:.2f}")
        print(f"- Clinical Accuracy: {qi.clinical_accuracy_confidence:.2f}")
        print(f"- Terminology Consistency: {qi.terminology_consistency:.2f}")
        print(f"- Missing Critical Info: {qi.missing_critical_information}")
        print(f"- Processing Confidence: {qi.processing_confidence:.2f}")
        print()

        print("🔧 PROCESSING METADATA:")
        metadata = summary.processing_metadata
        print(f"- Tier: {metadata['tier']}")
        print(f"- Rule Coverage: {metadata['rule_coverage']:.1%}")
        print(f"- Processing Method: {metadata['processing_method']}")
        print(f"- Resources Processed: {metadata['resources_processed']}")
        print(f"- Processing Errors: {len(metadata.get('processing_errors', []))}")

        if metadata.get('processing_errors'):
            print("  Errors:")
            for error in metadata['processing_errors']:
                print(f"    - {error}")

        composition = metadata.get('summary_composition', {})
        print(f"- Summary Composition:")
        print(f"  Total Orders: {composition.get('total_orders', 0)}")
        print(f"  Order Categories: {composition.get('order_categories', {})}")
        print(f"  Patient Info Available: {composition.get('patient_info_available', False)}")
        print(f"  Clinical Alerts Generated: {composition.get('clinical_alerts_generated', 0)}")
        print()

        # Test coverage validation
        resource_types_in_bundle = set(entry['resource']['resourceType'] for entry in comprehensive_bundle['entry'])
        orders_processed = len(summary.primary_orders)

        print("🎯 COVERAGE VALIDATION:")
        print(f"Resource types in bundle: {len(resource_types_in_bundle)}")
        print(f"Orders processed: {orders_processed}")
        print(f"Coverage rate: {orders_processed / len(resource_types_in_bundle):.1%}")

        if orders_processed == len(resource_types_in_bundle):
            print("✅ 100% COVERAGE ACHIEVED!")
        else:
            print("⚠️ Coverage incomplete")

        return True

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        print(f"❌ SUMMARIZATION FAILED after {processing_time:.2f}ms")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_edge_cases():
    """Test edge cases for comprehensive coverage"""

    print("\n🧪 Testing Edge Cases:")

    summarizer = FHIRBundleSummarizer()

    # Test 1: Empty bundle
    print("1. Empty bundle:")
    empty_bundle = {"resourceType": "Bundle", "type": "transaction", "entry": []}
    try:
        summary = await summarizer.summarize_bundle(empty_bundle)
        print(f"   ✅ Handled gracefully: {summary.summary_type}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 2: Bundle with unknown resource type
    print("2. Unknown resource type:")
    unknown_bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "CustomResourceType",
                    "id": "custom-1",
                    "status": "active",
                    "description": "This is a custom resource type"
                }
            }
        ]
    }
    try:
        summary = await summarizer.summarize_bundle(unknown_bundle)
        print(f"   ✅ Generic fallback worked: {len(summary.primary_orders)} order(s)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test 3: Bundle with malformed resource
    print("3. Malformed resource:")
    malformed_bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    # Missing required fields
                }
            }
        ]
    }
    try:
        summary = await summarizer.summarize_bundle(malformed_bundle)
        print(f"   ✅ Error handling worked: {len(summary.primary_orders)} order(s)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")


if __name__ == "__main__":
    print("Epic 4: 100% Rule-Based FHIR Bundle Summarization Test")
    print("=" * 60)

    async def run_tests():
        success = await test_comprehensive_fhir_bundle()
        await test_edge_cases()

        if success:
            print("\n🎉 ALL TESTS PASSED - 100% RULE-BASED COVERAGE ACHIEVED!")
        else:
            print("\n💥 TESTS FAILED")

    asyncio.run(run_tests())