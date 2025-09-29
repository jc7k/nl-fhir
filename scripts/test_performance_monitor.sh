#!/bin/bash
# Test Performance Monitoring Script
# Enhanced Test Suite Modernization - Story 6

echo "🚀 NL-FHIR Test Performance Monitor"
echo "=================================="
echo ""

# Performance targets (based on Story 6 requirements)
FACTORY_TARGET_SEC=20
INFUSION_TARGET_SEC=45
INTEGRATION_TARGET_SEC=10

echo "📊 Performance Targets:"
echo "  Factory Tests: <${FACTORY_TARGET_SEC}s"
echo "  Infusion Tests: <${INFUSION_TARGET_SEC}s"
echo "  Integration Tests: <${INTEGRATION_TARGET_SEC}s"
echo ""

# Factory Tests Performance
echo "🏭 Factory Tests Performance:"
FACTORY_START=$(date +%s.%N)
uv run pytest tests/services/fhir/factories/ --tb=no -q > /dev/null 2>&1
FACTORY_END=$(date +%s.%N)
FACTORY_TIME=$(echo "$FACTORY_END - $FACTORY_START" | bc)
FACTORY_TIME_INT=$(echo "$FACTORY_TIME/1" | bc)

echo "  Time: ${FACTORY_TIME}s"
if [ $(echo "$FACTORY_TIME < $FACTORY_TARGET_SEC" | bc) -eq 1 ]; then
    echo "  Status: ✅ EXCELLENT ($(echo "scale=1; $FACTORY_TARGET_SEC / $FACTORY_TIME" | bc)x faster than target)"
else
    echo "  Status: ⚠️ NEEDS OPTIMIZATION"
fi
echo ""

# Infusion Workflow Tests Performance
echo "💉 Infusion Workflow Tests Performance:"
INFUSION_START=$(date +%s.%N)
uv run pytest tests/test_infusion_workflow_resources.py --tb=no -q > /dev/null 2>&1
INFUSION_END=$(date +%s.%N)
INFUSION_TIME=$(echo "$INFUSION_END - $INFUSION_START" | bc)
INFUSION_TIME_INT=$(echo "$INFUSION_TIME/1" | bc)

echo "  Time: ${INFUSION_TIME}s"
if [ $(echo "$INFUSION_TIME < $INFUSION_TARGET_SEC" | bc) -eq 1 ]; then
    echo "  Status: ✅ EXCELLENT ($(echo "scale=1; $INFUSION_TARGET_SEC / $INFUSION_TIME" | bc)x faster than target)"
else
    echo "  Status: ⚠️ NEEDS OPTIMIZATION"
fi
echo ""

# Integration Tests Performance
echo "🔗 Integration Tests Performance:"
INTEGRATION_START=$(date +%s.%N)
uv run pytest tests/epic/test_epic_3_manual.py tests/test_story_3_3_hapi.py --tb=no -q > /dev/null 2>&1
INTEGRATION_END=$(date +%s.%N)
INTEGRATION_TIME=$(echo "$INTEGRATION_END - $INTEGRATION_START" | bc)
INTEGRATION_TIME_INT=$(echo "$INTEGRATION_TIME/1" | bc)

echo "  Time: ${INTEGRATION_TIME}s"
if [ $(echo "$INTEGRATION_TIME < $INTEGRATION_TARGET_SEC" | bc) -eq 1 ]; then
    echo "  Status: ✅ EXCELLENT ($(echo "scale=1; $INTEGRATION_TARGET_SEC / $INTEGRATION_TIME" | bc)x faster than target)"
else
    echo "  Status: ⚠️ NEEDS OPTIMIZATION"
fi
echo ""

# Overall Summary
TOTAL_TIME=$(echo "$FACTORY_TIME + $INFUSION_TIME + $INTEGRATION_TIME" | bc)
echo "📈 Performance Summary:"
echo "  Total Test Time: ${TOTAL_TIME}s"
echo "  Factory Tests: ${FACTORY_TIME}s ($(echo "scale=1; $FACTORY_TIME * 100 / $TOTAL_TIME" | bc)%)"
echo "  Infusion Tests: ${INFUSION_TIME}s ($(echo "scale=1; $INFUSION_TIME * 100 / $TOTAL_TIME" | bc)%)"
echo "  Integration Tests: ${INTEGRATION_TIME}s ($(echo "scale=1; $INTEGRATION_TIME * 100 / $TOTAL_TIME" | bc)%)"
echo ""

# Performance Grade
if [ $(echo "$FACTORY_TIME < $FACTORY_TARGET_SEC && $INFUSION_TIME < $INFUSION_TARGET_SEC && $INTEGRATION_TIME < $INTEGRATION_TARGET_SEC" | bc) -eq 1 ]; then
    echo "🏆 Overall Grade: EXCELLENT - All performance targets exceeded!"
else
    echo "📊 Overall Grade: NEEDS ATTENTION - Some targets not met"
fi

echo ""
echo "✅ Performance monitoring complete"