#!/usr/bin/env python3
"""
NL-FHIR Performance Baseline Measurement Script
Version: 1.0.0
Date: September 25, 2025
Purpose: Establish performance baselines before refactoring

This script measures current system performance to establish baselines
that will be used to validate the refactoring doesn't degrade performance.
"""

import json
import time
import statistics
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import psutil
import numpy as np
from dataclasses import dataclass, asdict
import argparse
import sys

# Test data templates for different resource types
TEST_DATA = {
    "patient": {
        "text": "Patient John Doe, DOB 01/15/1980, MRN 12345678",
        "resource_type": "Patient"
    },
    "medication": {
        "text": "Prescribe Metformin 500mg twice daily for diabetes",
        "resource_type": "MedicationRequest"
    },
    "observation": {
        "text": "Blood pressure 120/80, pulse 72, temperature 98.6F",
        "resource_type": "Observation"
    },
    "complex_bundle": {
        "text": """
        Patient Jane Smith, DOB 03/22/1975, MRN 87654321.
        Diagnose: Type 2 Diabetes Mellitus (E11.9).
        Prescribe: Insulin glargine 20 units subcutaneous daily.
        Lab results: HbA1c 7.2%, Glucose 145 mg/dL.
        Follow up in 3 months.
        """,
        "resource_type": "Bundle"
    },
    "infusion_workflow": {
        "text": """
        Start IV infusion of Normal Saline 1000mL at 125mL/hr.
        Add Potassium Chloride 20mEq to bag.
        Monitor vital signs every hour.
        Use 20 gauge peripheral IV catheter.
        """,
        "resource_type": "Bundle"
    }
}

@dataclass
class PerformanceMetrics:
    """Container for performance measurement results"""
    endpoint: str
    resource_type: str
    sample_size: int

    # Latency metrics (milliseconds)
    latency_mean: float
    latency_median: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    latency_min: float
    latency_max: float
    latency_stdev: float

    # Throughput metrics
    requests_per_second: float
    successful_requests: int
    failed_requests: int
    error_rate: float

    # Resource metrics
    avg_memory_mb: float
    peak_memory_mb: float
    avg_cpu_percent: float

    # Response size metrics
    avg_response_size_kb: float

    # Timestamp
    measured_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


class PerformanceBaseline:
    """Performance baseline measurement tool for NL-FHIR"""

    def __init__(self, base_url: str = "http://localhost:8001",
                 output_dir: str = "./performance_baselines"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = None
        self.process = psutil.Process()

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        await self.warmup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def warmup(self, iterations: int = 10):
        """Warmup the system before measurements"""
        print("🔥 Warming up system...")
        warmup_data = TEST_DATA["patient"]

        for i in range(iterations):
            try:
                async with self.session.post(
                    f"{self.base_url}/convert",
                    json=warmup_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    await response.json()
            except:
                pass  # Ignore warmup errors

        print("✅ Warmup complete")
        await asyncio.sleep(2)  # Let system stabilize

    async def measure_endpoint(
        self,
        endpoint: str,
        test_data: Dict[str, Any],
        iterations: int = 100
    ) -> PerformanceMetrics:
        """Measure performance for a specific endpoint"""

        url = f"{self.base_url}{endpoint}"
        latencies = []
        response_sizes = []
        memory_samples = []
        cpu_samples = []
        successful = 0
        failed = 0

        print(f"📏 Measuring {endpoint} with {test_data['resource_type']}...")

        start_time = time.time()

        for i in range(iterations):
            # Memory and CPU sampling
            memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
            cpu_samples.append(self.process.cpu_percent())

            request_start = time.time()

            try:
                async with self.session.post(
                    url,
                    json=test_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_data = await response.read()

                    if response.status == 200:
                        successful += 1
                        latency = (time.time() - request_start) * 1000  # Convert to ms
                        latencies.append(latency)
                        response_sizes.append(len(response_data) / 1024)  # KB
                    else:
                        failed += 1

            except Exception as e:
                failed += 1
                print(f"  ⚠️  Request {i+1} failed: {str(e)[:50]}")

            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"  📊 Progress: {i+1}/{iterations} requests completed")

        total_time = time.time() - start_time

        # Calculate metrics
        if latencies:
            metrics = PerformanceMetrics(
                endpoint=endpoint,
                resource_type=test_data['resource_type'],
                sample_size=iterations,

                # Latency metrics
                latency_mean=statistics.mean(latencies),
                latency_median=statistics.median(latencies),
                latency_p50=np.percentile(latencies, 50),
                latency_p95=np.percentile(latencies, 95),
                latency_p99=np.percentile(latencies, 99),
                latency_min=min(latencies),
                latency_max=max(latencies),
                latency_stdev=statistics.stdev(latencies) if len(latencies) > 1 else 0,

                # Throughput
                requests_per_second=iterations / total_time,
                successful_requests=successful,
                failed_requests=failed,
                error_rate=(failed / iterations) * 100,

                # Resources
                avg_memory_mb=statistics.mean(memory_samples),
                peak_memory_mb=max(memory_samples),
                avg_cpu_percent=statistics.mean(cpu_samples),

                # Response size
                avg_response_size_kb=statistics.mean(response_sizes) if response_sizes else 0,

                # Timestamp
                measured_at=datetime.now().isoformat()
            )
        else:
            # All requests failed
            metrics = PerformanceMetrics(
                endpoint=endpoint,
                resource_type=test_data['resource_type'],
                sample_size=iterations,
                latency_mean=0, latency_median=0, latency_p50=0,
                latency_p95=0, latency_p99=0, latency_min=0,
                latency_max=0, latency_stdev=0,
                requests_per_second=0,
                successful_requests=successful,
                failed_requests=failed,
                error_rate=100,
                avg_memory_mb=statistics.mean(memory_samples),
                peak_memory_mb=max(memory_samples),
                avg_cpu_percent=statistics.mean(cpu_samples),
                avg_response_size_kb=0,
                measured_at=datetime.now().isoformat()
            )

        return metrics

    async def measure_resource_creation(self, iterations: int = 100) -> Dict[str, PerformanceMetrics]:
        """Measure resource creation performance for all resource types"""
        results = {}

        for resource_name, test_data in TEST_DATA.items():
            metrics = await self.measure_endpoint("/convert", test_data, iterations)
            results[resource_name] = metrics

            # Print summary
            print(f"  ✅ {resource_name}: p95={metrics.latency_p95:.2f}ms, "
                  f"RPS={metrics.requests_per_second:.2f}, "
                  f"Error={metrics.error_rate:.2f}%")

        return results

    async def measure_bundle_operations(self, iterations: int = 50) -> PerformanceMetrics:
        """Measure bundle validation and assembly performance"""

        # Create a complex bundle for testing
        bundle_data = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "patient-1"}},
                {"resource": {"resourceType": "MedicationRequest", "id": "med-1"}},
                {"resource": {"resourceType": "Observation", "id": "obs-1"}}
            ]
        }

        metrics = await self.measure_endpoint(
            "/validate",
            bundle_data,
            iterations
        )

        return metrics

    async def stress_test(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Run stress test to find breaking point"""
        print(f"🔥 Running stress test for {duration_seconds} seconds...")

        start_time = time.time()
        end_time = start_time + duration_seconds

        request_count = 0
        error_count = 0
        latencies = []

        # Use simple patient data for stress testing
        test_data = TEST_DATA["patient"]

        while time.time() < end_time:
            request_start = time.time()

            try:
                async with self.session.post(
                    f"{self.base_url}/convert",
                    json=test_data,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    await response.json()

                    if response.status == 200:
                        latency = (time.time() - request_start) * 1000
                        latencies.append(latency)
                    else:
                        error_count += 1

            except:
                error_count += 1

            request_count += 1

            # Progress update every 100 requests
            if request_count % 100 == 0:
                elapsed = time.time() - start_time
                rps = request_count / elapsed
                print(f"  📈 Stress: {request_count} requests, "
                      f"RPS={rps:.2f}, Errors={error_count}")

        total_time = time.time() - start_time

        return {
            "duration_seconds": total_time,
            "total_requests": request_count,
            "successful_requests": request_count - error_count,
            "error_count": error_count,
            "error_rate": (error_count / request_count) * 100 if request_count > 0 else 0,
            "requests_per_second": request_count / total_time,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
            "p95_latency_ms": np.percentile(latencies, 95) if latencies else 0,
            "p99_latency_ms": np.percentile(latencies, 99) if latencies else 0
        }

    def save_results(self, results: Dict[str, Any], filename: str = "baseline"):
        """Save measurement results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{filename}_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"💾 Results saved to: {output_file}")
        return output_file

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable performance report"""
        report = []
        report.append("=" * 80)
        report.append("NL-FHIR PERFORMANCE BASELINE REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Resource creation metrics
        report.append("RESOURCE CREATION PERFORMANCE")
        report.append("-" * 40)

        for resource_name, metrics in results.get("resource_creation", {}).items():
            if isinstance(metrics, PerformanceMetrics):
                report.append(f"\n{resource_name.upper()}:")
                report.append(f"  Mean Latency:     {metrics.latency_mean:.2f} ms")
                report.append(f"  P50 Latency:      {metrics.latency_p50:.2f} ms")
                report.append(f"  P95 Latency:      {metrics.latency_p95:.2f} ms")
                report.append(f"  P99 Latency:      {metrics.latency_p99:.2f} ms")
                report.append(f"  Throughput:       {metrics.requests_per_second:.2f} req/s")
                report.append(f"  Error Rate:       {metrics.error_rate:.2f}%")
                report.append(f"  Avg Memory:       {metrics.avg_memory_mb:.2f} MB")
                report.append(f"  Avg Response:     {metrics.avg_response_size_kb:.2f} KB")

        # Bundle operations
        if "bundle_operations" in results:
            bundle_metrics = results["bundle_operations"]
            if isinstance(bundle_metrics, PerformanceMetrics):
                report.append("\nBUNDLE OPERATIONS:")
                report.append(f"  P95 Latency:      {bundle_metrics.latency_p95:.2f} ms")
                report.append(f"  Throughput:       {bundle_metrics.requests_per_second:.2f} req/s")

        # Stress test results
        if "stress_test" in results:
            stress = results["stress_test"]
            report.append("\nSTRESS TEST RESULTS:")
            report.append(f"  Duration:         {stress['duration_seconds']:.2f} seconds")
            report.append(f"  Total Requests:   {stress['total_requests']}")
            report.append(f"  Throughput:       {stress['requests_per_second']:.2f} req/s")
            report.append(f"  Error Rate:       {stress['error_rate']:.2f}%")
            report.append(f"  P95 Latency:      {stress['p95_latency_ms']:.2f} ms")
            report.append(f"  P99 Latency:      {stress['p99_latency_ms']:.2f} ms")

        # Baseline thresholds for monitoring
        report.append("\n" + "=" * 80)
        report.append("RECOMMENDED MONITORING THRESHOLDS")
        report.append("=" * 80)

        # Calculate thresholds (150% of baseline for warnings)
        if "resource_creation" in results:
            patient_metrics = results["resource_creation"].get("patient")
            if patient_metrics and isinstance(patient_metrics, PerformanceMetrics):
                report.append(f"P95 Latency Warning:    > {patient_metrics.latency_p95 * 1.5:.2f} ms")
                report.append(f"P99 Latency Critical:   > {patient_metrics.latency_p99 * 2.0:.2f} ms")
                report.append(f"Error Rate Warning:     > 1%")
                report.append(f"Error Rate Critical:    > 5%")
                report.append(f"Memory Warning:         > {patient_metrics.avg_memory_mb * 2:.2f} MB")

        report_text = "\n".join(report)

        # Save report
        report_file = self.output_dir / f"baseline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report_text)

        return report_text


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="NL-FHIR Performance Baseline Measurement")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL for NL-FHIR API")
    parser.add_argument("--iterations", type=int, default=100, help="Number of iterations per test")
    parser.add_argument("--stress-duration", type=int, default=60, help="Stress test duration in seconds")
    parser.add_argument("--output-dir", default="./performance_baselines", help="Output directory for results")
    parser.add_argument("--skip-stress", action="store_true", help="Skip stress testing")

    args = parser.parse_args()

    print("🚀 NL-FHIR Performance Baseline Measurement Tool")
    print("=" * 60)
    print(f"Target URL: {args.url}")
    print(f"Iterations: {args.iterations}")
    print(f"Output Dir: {args.output_dir}")
    print("=" * 60)

    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{args.url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    print("❌ Server health check failed!")
                    sys.exit(1)
                print("✅ Server is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please ensure NL-FHIR is running at the specified URL")
        sys.exit(1)

    # Run measurements
    async with PerformanceBaseline(args.url, args.output_dir) as baseline:
        results = {}

        # Measure resource creation
        print("\n📊 Phase 1: Resource Creation Performance")
        print("-" * 40)
        resource_results = await baseline.measure_resource_creation(args.iterations)
        results["resource_creation"] = {k: v.to_dict() for k, v in resource_results.items()}

        # Measure bundle operations
        print("\n📊 Phase 2: Bundle Operations Performance")
        print("-" * 40)
        bundle_metrics = await baseline.measure_bundle_operations(args.iterations // 2)
        results["bundle_operations"] = bundle_metrics.to_dict()

        # Run stress test
        if not args.skip_stress:
            print("\n📊 Phase 3: Stress Testing")
            print("-" * 40)
            stress_results = await baseline.stress_test(args.stress_duration)
            results["stress_test"] = stress_results

        # Generate and display report
        print("\n" + "=" * 60)
        print("PERFORMANCE BASELINE SUMMARY")
        print("=" * 60)

        report = baseline.generate_report(results)
        print(report)

        # Save results
        output_file = baseline.save_results(results)

        print("\n✅ Performance baseline measurement complete!")
        print(f"📁 Results saved to: {output_file}")

        # Generate threshold configuration
        threshold_file = Path(args.output_dir) / "monitoring_thresholds.json"
        thresholds = {
            "latency_p95_warning_ms": resource_results["patient"].latency_p95 * 1.5,
            "latency_p95_critical_ms": resource_results["patient"].latency_p95 * 2.0,
            "latency_p99_warning_ms": resource_results["patient"].latency_p99 * 1.5,
            "latency_p99_critical_ms": resource_results["patient"].latency_p99 * 2.0,
            "error_rate_warning_percent": 1.0,
            "error_rate_critical_percent": 5.0,
            "memory_warning_mb": resource_results["patient"].avg_memory_mb * 2,
            "memory_critical_mb": resource_results["patient"].avg_memory_mb * 3,
            "baseline_measured_at": datetime.now().isoformat()
        }

        with open(threshold_file, 'w') as f:
            json.dump(thresholds, f, indent=2)

        print(f"📊 Monitoring thresholds saved to: {threshold_file}")


if __name__ == "__main__":
    # Run async main function
    asyncio.run(main())