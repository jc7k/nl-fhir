#!/bin/bash
# Phase 1 Test Validation Script
# Validates all newly implemented tests

set -e  # Exit on error

echo "=================================================="
echo "Phase 1 Test Validation"
echo "Safety Modules + Middleware Tests"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to check file exists
check_file() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $1"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} File missing: $1"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check syntax
check_syntax() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if uv run python -m py_compile "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Syntax valid: $1"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} Syntax error: $1"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo "Step 1: Checking test files exist..."
echo "------------------------------------"
check_file "tests/services/safety/__init__.py"
check_file "tests/services/safety/test_dosage_validator.py"
check_file "tests/services/safety/test_interaction_checker.py"
check_file "tests/services/safety/test_contraindication_checker.py"
check_file "tests/services/safety/test_risk_scorer.py"
check_file "tests/services/safety/test_clinical_decision_support.py"
check_file "tests/api/middleware/__init__.py"
check_file "tests/api/middleware/test_timing_middleware.py"
check_file "tests/api/middleware/test_rate_limit_middleware.py"
echo ""

echo "Step 2: Checking Python syntax..."
echo "------------------------------------"
check_syntax "tests/services/safety/test_dosage_validator.py"
check_syntax "tests/services/safety/test_interaction_checker.py"
check_syntax "tests/services/safety/test_contraindication_checker.py"
check_syntax "tests/services/safety/test_risk_scorer.py"
check_syntax "tests/services/safety/test_clinical_decision_support.py"
check_syntax "tests/api/middleware/test_timing_middleware.py"
check_syntax "tests/api/middleware/test_rate_limit_middleware.py"
echo ""

echo "Step 3: Counting test cases..."
echo "------------------------------------"
DOSAGE_TESTS=$(grep -c "def test_" tests/services/safety/test_dosage_validator.py || echo "0")
INTERACTION_TESTS=$(grep -c "def test_" tests/services/safety/test_interaction_checker.py || echo "0")
CONTRAINDICATION_TESTS=$(grep -c "def test_" tests/services/safety/test_contraindication_checker.py || echo "0")
RISK_TESTS=$(grep -c "def test_" tests/services/safety/test_risk_scorer.py || echo "0")
CDS_TESTS=$(grep -c "def test_" tests/services/safety/test_clinical_decision_support.py || echo "0")
TIMING_TESTS=$(grep -c "def test_" tests/api/middleware/test_timing_middleware.py || echo "0")
RATELIMIT_TESTS=$(grep -c "def test_" tests/api/middleware/test_rate_limit_middleware.py || echo "0")

TOTAL_TEST_CASES=$((DOSAGE_TESTS + INTERACTION_TESTS + CONTRAINDICATION_TESTS + RISK_TESTS + CDS_TESTS + TIMING_TESTS + RATELIMIT_TESTS))

echo "  Dosage Validator:        ${DOSAGE_TESTS} tests"
echo "  Interaction Checker:     ${INTERACTION_TESTS} tests"
echo "  Contraindication Checker: ${CONTRAINDICATION_TESTS} tests"
echo "  Risk Scorer:             ${RISK_TESTS} tests"
echo "  Clinical Decision Support: ${CDS_TESTS} tests"
echo "  Timing Middleware:       ${TIMING_TESTS} tests"
echo "  Rate Limit Middleware:   ${RATELIMIT_TESTS} tests"
echo "  ${GREEN}TOTAL: ${TOTAL_TEST_CASES} test cases${NC}"
echo ""

echo "Step 4: Checking source modules exist..."
echo "------------------------------------"
check_file "src/nl_fhir/services/safety/dosage_validator.py"
check_file "src/nl_fhir/services/safety/interaction_checker.py"
check_file "src/nl_fhir/services/safety/contraindication_checker.py"
check_file "src/nl_fhir/services/safety/risk_scorer.py"
check_file "src/nl_fhir/services/safety/clinical_decision_support.py"
check_file "src/nl_fhir/api/middleware/timing.py"
check_file "src/nl_fhir/api/middleware/rate_limit.py"
echo ""

echo "Step 5: Quick import validation..."
echo "------------------------------------"
IMPORT_ERRORS=0

echo -n "  Checking dosage_validator imports... "
if uv run python -c "from src.nl_fhir.services.safety.dosage_validator import DosageValidator" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    IMPORT_ERRORS=$((IMPORT_ERRORS + 1))
fi

echo -n "  Checking interaction_checker imports... "
if uv run python -c "from src.nl_fhir.services.safety.interaction_checker import DrugInteractionChecker" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    IMPORT_ERRORS=$((IMPORT_ERRORS + 1))
fi

echo -n "  Checking contraindication_checker imports... "
if uv run python -c "from src.nl_fhir.services.safety.contraindication_checker import ContraindicationChecker" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    IMPORT_ERRORS=$((IMPORT_ERRORS + 1))
fi

echo -n "  Checking risk_scorer imports... "
if uv run python -c "from src.nl_fhir.services.safety.risk_scorer import SafetyRiskScorer" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    IMPORT_ERRORS=$((IMPORT_ERRORS + 1))
fi

echo -n "  Checking timing middleware imports... "
if uv run python -c "from src.nl_fhir.api.middleware.timing import request_timing_and_validation" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    IMPORT_ERRORS=$((IMPORT_ERRORS + 1))
fi

echo -n "  Checking rate_limit middleware imports... "
if uv run python -c "from src.nl_fhir.api.middleware.rate_limit import rate_limit_middleware" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    IMPORT_ERRORS=$((IMPORT_ERRORS + 1))
fi

echo ""

echo "=================================================="
echo "Validation Summary"
echo "=================================================="
echo ""
echo "File Checks:       ${PASSED_CHECKS}/${TOTAL_CHECKS} passed"
echo "Test Cases Found:  ${TOTAL_TEST_CASES}"
echo "Import Errors:     ${IMPORT_ERRORS}"
echo ""

if [ $FAILED_CHECKS -eq 0 ] && [ $IMPORT_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All validation checks passed!${NC}"
    echo ""
    echo "Next step: Run the tests"
    echo "  uv run pytest tests/services/safety/ -v"
    echo "  uv run pytest tests/api/middleware/ -v"
    exit 0
else
    echo -e "${RED}✗ Validation failed${NC}"
    echo ""
    echo "Issues found:"
    [ $FAILED_CHECKS -gt 0 ] && echo "  - ${FAILED_CHECKS} file check(s) failed"
    [ $IMPORT_ERRORS -gt 0 ] && echo "  - ${IMPORT_ERRORS} import error(s)"
    echo ""
    echo "Please review errors above and fix before running tests."
    exit 1
fi
