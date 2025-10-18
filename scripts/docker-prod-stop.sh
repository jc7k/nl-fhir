#!/bin/bash
# Stop NL-FHIR production stack
set -e

# Parse arguments
MODE="${1:-full}"  # Default to full mode

if [ "$MODE" = "minimal" ]; then
    COMPOSE_FILE="docker-compose.prod-minimal.yml"
    echo "🛑 Stopping NL-FHIR Production (Minimal Mode)..."
else
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "🛑 Stopping NL-FHIR Production Stack (Full Mode)..."
fi

# Navigate to project root
cd "$(dirname "$0")/.."

# Stop services
docker-compose -f "$COMPOSE_FILE" down

echo ""
echo "✅ Production stack stopped!"
echo ""

if [ "$MODE" != "minimal" ]; then
    echo "To remove volumes (CAUTION: deletes HAPI FHIR data):"
    echo "  docker-compose -f $COMPOSE_FILE down -v"
fi
