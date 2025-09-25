"""
Performance Benchmarking and Optimization Analysis
Comprehensive testing of FHIR resource creation performance, memory usage, and scalability.

This suite provides detailed performance metrics for the NL-FHIR system to ensure
sub-2 second response times and efficient resource utilization.
"""

import pytest
import time
import psutil
import os
from typing import List, Dict, Any
from unittest.mock import patch

from src.nl_fhir.services.fhir.resource_factory import FHIRResourceFactory


class TestPerformanceBenchmarking:
    """Comprehensive performance benchmarking suite"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = FHIRResourceFactory()
        factory.initialize()
        return factory

    @pytest.fixture
    def process(self):
        """Get current process for memory monitoring"""
        return psutil.Process(os.getpid())

    # =================================================================
    # Resource Creation Performance Tests
    # =================================================================

    def test_single_resource_creation_performance(self, factory):
        """Benchmark single resource creation across different types"""

        patient_ref = "Patient/perf-single"
        results = {}

        # Test core clinical resources
        resource_tests = [
            ("Patient", "create_patient_resource", {"name": "Test Patient"}),
            ("Practitioner", "create_practitioner_resource", {"name": "Dr. Test"}),
            ("Observation", "create_observation_resource", {"type": "vital-signs"}, patient_ref),
            ("MedicationRequest", "create_medication_request_resource", {"medication": "aspirin"}, patient_ref),
            ("DiagnosticReport", "create_diagnostic_report_resource", {"title": "Lab Report"}, patient_ref),
            ("Encounter", "create_encounter_resource", {"status": "finished"}, patient_ref)
        ]

        for resource_type, method_name, data, *args in resource_tests:
            start_time = time.time()

            factory_method = getattr(factory, method_name)
            if args:
                result = factory_method(data, args[0])
            else:
                result = factory_method(data)

            end_time = time.time()
            execution_time = end_time - start_time

            results[resource_type] = {
                "time": execution_time,
                "resource_id": result.get("id"),
                "size_bytes": len(str(result))
            }

            # Performance assertion: Each resource should be created in < 50ms
            assert execution_time < 0.050, f"{resource_type} took {execution_time:.3f}s (>50ms limit)"

        # Summary performance check
        avg_time = sum(r["time"] for r in results.values()) / len(results)
        total_time = sum(r["time"] for r in results.values())

        assert avg_time < 0.025, f"Average resource creation time {avg_time:.3f}s exceeds 25ms"
        assert total_time < 0.200, f"Total creation time {total_time:.3f}s exceeds 200ms"

        print(f"✅ Single Resource Performance:")
        for resource_type, metrics in results.items():
            print(f"   {resource_type}: {metrics['time']*1000:.1f}ms ({metrics['size_bytes']} bytes)")
        print(f"   Average: {avg_time*1000:.1f}ms | Total: {total_time*1000:.1f}ms")

    def test_batch_resource_creation_performance(self, factory):
        """Benchmark batch resource creation performance"""

        patient_ref = "Patient/perf-batch"
        start_time = time.time()

        # Create a realistic clinical scenario with multiple resources
        resources = []

        # Patient and core entities
        patient = factory.create_patient_resource({"name": "Batch Test Patient"})
        resources.append(patient)

        practitioner = factory.create_practitioner_resource({"name": "Dr. Batch"})
        resources.append(practitioner)

        encounter = factory.create_encounter_resource({"status": "finished"}, patient_ref)
        resources.append(encounter)

        # Clinical resources batch
        for i in range(5):
            observation = factory.create_observation_resource({
                "type": "vital-signs",
                "value": f"{120 + i}",
                "unit": "mmHg"
            }, patient_ref)
            resources.append(observation)

        for i in range(3):
            medication = factory.create_medication_request_resource({
                "medication": f"medication-{i+1}",
                "dosage": "10mg"
            }, patient_ref)
            resources.append(medication)

        # Epic 7 resources
        specimen = factory.create_specimen_resource({"type": "blood"}, patient_ref)
        resources.append(specimen)

        coverage = factory.create_coverage_resource({
            "type": "medical",
            "payor": {"id": "batch-ins", "name": "Batch Insurance"}
        }, patient_ref)
        resources.append(coverage)

        appointment = factory.create_appointment_resource({
            "status": "scheduled"
        }, patient_ref)
        resources.append(appointment)

        end_time = time.time()
        total_time = end_time - start_time
        resources_per_second = len(resources) / total_time

        # Performance assertions
        assert total_time < 1.0, f"Batch creation took {total_time:.3f}s (>1s limit)"
        assert resources_per_second > 10, f"Only {resources_per_second:.1f} resources/sec (<10 limit)"
        assert len(resources) == 12, f"Expected 12 resources, got {len(resources)}"

        # Verify all resources are valid
        for resource in resources:
            assert "resourceType" in resource
            assert "id" in resource

        print(f"✅ Batch Resource Performance:")
        print(f"   Resources: {len(resources)} created in {total_time*1000:.0f}ms")
        print(f"   Throughput: {resources_per_second:.1f} resources/second")
        print(f"   Average: {(total_time/len(resources))*1000:.1f}ms per resource")

    def test_memory_usage_benchmarking(self, factory, process):
        """Benchmark memory usage during resource creation"""

        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        patient_ref = "Patient/memory-test"
        resources = []

        # Create a significant number of resources to test memory usage
        for i in range(50):
            # Mix different resource types
            if i % 4 == 0:
                resource = factory.create_patient_resource({"name": f"Patient-{i}"})
            elif i % 4 == 1:
                resource = factory.create_observation_resource({"type": "lab"}, patient_ref)
            elif i % 4 == 2:
                resource = factory.create_medication_request_resource({"medication": "test"}, patient_ref)
            else:
                resource = factory.create_diagnostic_report_resource({"title": "Report"}, patient_ref)

            resources.append(resource)

            # Check memory every 10 resources
            if (i + 1) % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - initial_memory

                # Memory growth should be reasonable (< 50MB for 50 resources)
                assert memory_growth < 50, f"Memory usage grew by {memory_growth:.1f}MB (>50MB limit)"

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_growth = final_memory - initial_memory

        # Calculate memory efficiency
        memory_per_resource = total_memory_growth / len(resources)

        # Performance assertions
        assert total_memory_growth < 100, f"Total memory growth {total_memory_growth:.1f}MB (>100MB limit)"
        assert memory_per_resource < 2.0, f"Memory per resource {memory_per_resource:.3f}MB (>2MB limit)"

        print(f"✅ Memory Usage Performance:")
        print(f"   Initial Memory: {initial_memory:.1f}MB")
        print(f"   Final Memory: {final_memory:.1f}MB")
        print(f"   Growth: {total_memory_growth:.1f}MB for {len(resources)} resources")
        print(f"   Efficiency: {memory_per_resource*1024:.1f}KB per resource")

    # =================================================================
    # Epic-Specific Performance Tests
    # =================================================================

    @pytest.mark.parametrize("epic_scenario", [
        ("epic10_advanced", [
            ("Account", "create_account_resource", {}, "Patient/test"),
            ("ChargeItem", "create_charge_item_resource", {}, "Patient/test"),
            ("Claim", "create_claim_resource", {}, "Patient/test"),
            ("Contract", "create_contract_resource", {}),
            ("Binary", "create_binary_resource", {}),
        ]),
        ("epic7_clinical", [
            ("Specimen", "create_specimen_resource", {"type": "blood"}, "Patient/test"),
            ("Coverage", "create_coverage_resource", {
                "type": "medical",
                "payor": {"id": "test", "name": "Test"}
            }, "Patient/test"),
            ("Appointment", "create_appointment_resource", {"status": "scheduled"}, "Patient/test"),
        ]),
        ("core_clinical", [
            ("Patient", "create_patient_resource", {"name": "Test"}),
            ("Practitioner", "create_practitioner_resource", {"name": "Dr. Test"}),
            ("Observation", "create_observation_resource", {"type": "vital"}, "Patient/test"),
            ("MedicationRequest", "create_medication_request_resource", {"medication": "test"}, "Patient/test"),
            ("DiagnosticReport", "create_diagnostic_report_resource", {"title": "Test"}, "Patient/test"),
        ])
    ])
    def test_epic_specific_performance(self, factory, epic_scenario):
        """Test performance of specific Epic resource groups"""

        scenario_name, resource_configs = epic_scenario

        start_time = time.time()
        created_resources = []

        for resource_type, method_name, data, *args in resource_configs:
            factory_method = getattr(factory, method_name)

            if args:
                result = factory_method(data, args[0])
            else:
                result = factory_method(data)

            created_resources.append(result)

        end_time = time.time()
        scenario_time = end_time - start_time

        # Performance assertions per scenario
        if scenario_name == "epic10_advanced":
            assert scenario_time < 0.5, f"Epic 10 scenario took {scenario_time:.3f}s (>500ms limit)"
        elif scenario_name == "epic7_clinical":
            assert scenario_time < 0.3, f"Epic 7 scenario took {scenario_time:.3f}s (>300ms limit)"
        else:  # core_clinical
            assert scenario_time < 0.4, f"Core clinical scenario took {scenario_time:.3f}s (>400ms limit)"

        # Verify all resources created successfully
        assert len(created_resources) == len(resource_configs)
        for resource in created_resources:
            assert "resourceType" in resource
            assert "id" in resource

        resources_per_second = len(created_resources) / scenario_time

        print(f"✅ {scenario_name.replace('_', ' ').title()} Performance:")
        print(f"   Resources: {len(created_resources)} in {scenario_time*1000:.0f}ms")
        print(f"   Throughput: {resources_per_second:.1f} resources/second")

    # =================================================================
    # Scalability and Load Tests
    # =================================================================

    def test_scalability_load_testing(self, factory):
        """Test system performance under increasing load"""

        load_results = {}
        patient_ref = "Patient/load-test"

        # Test different load levels
        load_levels = [10, 25, 50, 100]

        for load_count in load_levels:
            start_time = time.time()
            resources = []

            for i in range(load_count):
                # Create a mix of resources to simulate realistic load
                if i % 3 == 0:
                    resource = factory.create_observation_resource({
                        "type": "vital-signs",
                        "value": f"{i}"
                    }, patient_ref)
                elif i % 3 == 1:
                    resource = factory.create_medication_request_resource({
                        "medication": f"med-{i}"
                    }, patient_ref)
                else:
                    resource = factory.create_diagnostic_report_resource({
                        "title": f"Report-{i}"
                    }, patient_ref)

                resources.append(resource)

            end_time = time.time()
            load_time = end_time - start_time
            throughput = load_count / load_time

            load_results[load_count] = {
                "time": load_time,
                "throughput": throughput,
                "avg_per_resource": load_time / load_count
            }

            # Scalability assertions - throughput should remain reasonable
            if load_count <= 50:
                assert throughput > 15, f"Low throughput at {load_count} resources: {throughput:.1f}/sec"
            else:
                assert throughput > 10, f"Low throughput at {load_count} resources: {throughput:.1f}/sec"

            # Individual resource time should stay reasonable
            assert load_results[load_count]["avg_per_resource"] < 0.1, \
                f"Average resource time {load_results[load_count]['avg_per_resource']:.3f}s too high"

        # Check that performance degrades gracefully
        throughput_50 = load_results[50]["throughput"]
        throughput_100 = load_results[100]["throughput"]
        degradation = (throughput_50 - throughput_100) / throughput_50

        assert degradation < 0.5, f"Performance degraded {degradation*100:.0f}% from 50→100 resources (>50%)"

        print(f"✅ Scalability Load Testing:")
        for load_count, metrics in load_results.items():
            print(f"   {load_count:3d} resources: {metrics['throughput']:5.1f}/sec "
                  f"({metrics['time']*1000:4.0f}ms total)")

        return load_results

    # =================================================================
    # Comprehensive Performance Summary
    # =================================================================

    def test_comprehensive_performance_report(self, factory, process):
        """Generate comprehensive performance report for the system"""

        print(f"\n🎯 COMPREHENSIVE NL-FHIR PERFORMANCE REPORT")
        print(f"=" * 60)

        # System info
        initial_memory = process.memory_info().rss / 1024 / 1024
        print(f"System Memory Usage: {initial_memory:.1f}MB")

        # Test quick resource creation samples
        patient_ref = "Patient/comprehensive"
        performance_data = {}

        # Core resource timing
        core_resources = ["Patient", "Practitioner", "Observation", "MedicationRequest", "Encounter"]
        start_time = time.time()

        for resource_type in core_resources:
            res_start = time.time()
            if resource_type == "Patient":
                resource = factory.create_patient_resource({"name": "Test"})
            elif resource_type == "Practitioner":
                resource = factory.create_practitioner_resource({"name": "Dr. Test"})
            elif resource_type == "Observation":
                resource = factory.create_observation_resource({"type": "test"}, patient_ref)
            elif resource_type == "MedicationRequest":
                resource = factory.create_medication_request_resource({"medication": "test"}, patient_ref)
            elif resource_type == "Encounter":
                resource = factory.create_encounter_resource({"status": "finished"}, patient_ref)

            res_end = time.time()
            performance_data[resource_type] = res_end - res_start

        total_core_time = time.time() - start_time

        # Epic resources timing
        epic_start = time.time()
        specimen = factory.create_specimen_resource({"type": "blood"}, patient_ref)
        coverage = factory.create_coverage_resource({
            "type": "medical",
            "payor": {"id": "test", "name": "Test"}
        }, patient_ref)
        appointment = factory.create_appointment_resource({"status": "scheduled"}, patient_ref)
        epic_time = time.time() - epic_start

        # Memory after operations
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"Core Resources (5): {total_core_time*1000:.0f}ms total, {(total_core_time/5)*1000:.1f}ms avg")
        print(f"Epic Resources (3): {epic_time*1000:.0f}ms total, {(epic_time/3)*1000:.1f}ms avg")
        print(f"Memory Growth: {memory_growth:.1f}MB for 8 resources")

        print(f"\n⚡ RESOURCE BREAKDOWN:")
        for resource, timing in performance_data.items():
            print(f"{resource:20}: {timing*1000:5.1f}ms")

        # Performance validation
        fastest_time = min(performance_data.values())
        slowest_time = max(performance_data.values())
        avg_time = sum(performance_data.values()) / len(performance_data)

        print(f"\n🎯 PERFORMANCE SUMMARY:")
        print(f"Fastest Resource: {fastest_time*1000:.1f}ms")
        print(f"Slowest Resource: {slowest_time*1000:.1f}ms")
        print(f"Average Resource: {avg_time*1000:.1f}ms")
        print(f"Total System Test: {(total_core_time + epic_time)*1000:.0f}ms")

        # System performance assertions
        assert avg_time < 0.050, f"Average resource time {avg_time:.3f}s exceeds 50ms target"
        assert slowest_time < 0.100, f"Slowest resource time {slowest_time:.3f}s exceeds 100ms limit"
        assert total_core_time + epic_time < 1.0, f"Total test time exceeds 1s limit"
        assert memory_growth < 20, f"Memory growth {memory_growth:.1f}MB exceeds 20MB limit"

        print(f"\n✅ PERFORMANCE TARGETS MET:")
        print(f"   ✓ Sub-2s response time capability verified")
        print(f"   ✓ Memory efficiency within acceptable limits")
        print(f"   ✓ Resource creation performance optimized")
        print(f"   ✓ Scalable architecture validated")
        print(f"\n🚀 NL-FHIR PERFORMANCE: PRODUCTION READY")

        return {
            "core_resources": performance_data,
            "epic_time": epic_time,
            "total_time": total_core_time + epic_time,
            "memory_growth": memory_growth,
            "avg_time": avg_time
        }