# Performance Baseline Measurement Guide

## Quick Start

### Prerequisites
```bash
# Install required dependencies
uv add aiohttp psutil numpy
```

### Basic Usage
```bash
# Run with default settings (100 iterations)
uv run python scripts/performance_baseline.py

# Custom configuration
uv run python scripts/performance_baseline.py \
  --url http://localhost:8001 \
  --iterations 200 \
  --stress-duration 120 \
  --output-dir ./performance_baselines
```

### Command Line Options
- `--url`: NL-FHIR API base URL (default: http://localhost:8001)
- `--iterations`: Number of test iterations per resource type (default: 100)
- `--stress-duration`: Duration of stress test in seconds (default: 60)
- `--output-dir`: Directory for output files (default: ./performance_baselines)
- `--skip-stress`: Skip the stress testing phase

## What It Measures

### 1. Resource Creation Performance
Tests each resource type with production-like data:
- **Patient records** - Basic patient information
- **Medication requests** - Prescription orders
- **Observations** - Vital signs and measurements
- **Complex bundles** - Multi-resource clinical scenarios
- **Infusion workflows** - Complete infusion therapy bundles

### 2. Key Metrics Captured
**Latency Metrics:**
- Mean, median, p50, p95, p99 response times
- Min/max latency boundaries
- Standard deviation for consistency

**Throughput Metrics:**
- Requests per second (RPS)
- Success/failure rates
- Error percentages

**Resource Metrics:**
- Average memory usage (MB)
- Peak memory consumption
- CPU utilization percentage

### 3. Stress Testing
Continuous load testing to find:
- Maximum sustainable throughput
- Performance degradation points
- Error rate under load

## Output Files

### 1. JSON Baseline Data
`performance_baselines/baseline_YYYYMMDD_HHMMSS.json`
- Complete metrics for all tests
- Machine-readable format
- Used for automated comparisons

### 2. Human-Readable Report
`performance_baselines/baseline_report_YYYYMMDD_HHMMSS.txt`
- Summary statistics
- Performance analysis
- Recommended thresholds

### 3. Monitoring Thresholds
`performance_baselines/monitoring_thresholds.json`
```json
{
  "latency_p95_warning_ms": 67.5,
  "latency_p95_critical_ms": 90.0,
  "error_rate_warning_percent": 1.0,
  "error_rate_critical_percent": 5.0
}
```

## Integration with Refactoring

### Before Refactoring
```bash
# Establish baseline
uv run python scripts/performance_baseline.py --iterations 500
# Save the baseline files for comparison
```

### During Refactoring
```bash
# After each major change
uv run python scripts/performance_baseline.py --iterations 100
# Compare with baseline to detect degradation
```

### Automated Comparison
```python
# Example comparison script
import json

with open('baseline_original.json') as f:
    baseline = json.load(f)

with open('baseline_current.json') as f:
    current = json.load(f)

# Compare p95 latencies
baseline_p95 = baseline['resource_creation']['patient']['latency_p95']
current_p95 = current['resource_creation']['patient']['latency_p95']

if current_p95 > baseline_p95 * 1.5:
    print(f"⚠️ Performance degradation detected: {current_p95:.2f}ms vs {baseline_p95:.2f}ms")
    # Trigger rollback
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Performance Baseline
on:
  pull_request:
    paths:
      - 'src/nl_fhir/services/fhir/**'

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Start NL-FHIR
        run: |
          uv run uvicorn src.nl_fhir.main:app --port 8001 &
          sleep 10  # Wait for startup

      - name: Run baseline measurement
        run: |
          uv run python scripts/performance_baseline.py \
            --iterations 50 \
            --skip-stress

      - name: Check thresholds
        run: |
          python scripts/check_performance_thresholds.py
```

## Interpreting Results

### Good Performance Indicators
- ✅ P95 latency < 100ms for simple resources
- ✅ P99 latency < 200ms for complex bundles
- ✅ Error rate < 0.1%
- ✅ Consistent latency (low standard deviation)
- ✅ Linear throughput scaling

### Warning Signs
- ⚠️ P95 latency > 150% of baseline
- ⚠️ Memory usage > 2x baseline
- ⚠️ Error rate > 1%
- ⚠️ High latency variance
- ⚠️ Throughput plateau under load

### Critical Issues
- 🔴 P95 latency > 200% of baseline
- 🔴 Memory leak patterns
- 🔴 Error rate > 5%
- 🔴 System crashes under load
- 🔴 Throughput degradation

## Rollback Triggers

Based on measurements, automatic rollback should trigger when:

1. **Latency Breach**: P95 > baseline * 1.5 for 5 consecutive minutes
2. **Error Spike**: Error rate > 5% for any 1-minute window
3. **Memory Leak**: Memory usage grows > 10MB per minute
4. **Throughput Drop**: RPS < 50% of baseline under same load

## Troubleshooting

### Server Not Found
```
❌ Cannot connect to server
```
**Solution:** Ensure NL-FHIR is running:
```bash
uv run uvicorn src.nl_fhir.main:app --host 0.0.0.0 --port 8001
```

### Timeout Errors
```
⚠️ Request timeout after 30s
```
**Solution:** System under heavy load, reduce iterations or increase timeout

### Memory Errors
```
MemoryError: Unable to allocate array
```
**Solution:** Reduce batch size or iterations, check system resources

## Next Steps

After establishing baselines:
1. ✅ Save baseline files to git repository
2. ✅ Configure monitoring dashboards with thresholds
3. ✅ Set up automated performance tests in CI/CD
4. ✅ Create performance regression alerts
5. ✅ Document baseline metrics in project wiki