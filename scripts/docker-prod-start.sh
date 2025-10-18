#!/bin/bash
# Start NL-FHIR in production mode locally
set -e

# Parse arguments
MODE="${1:-full}"  # Default to full mode (with HAPI FHIR)

if [ "$MODE" = "minimal" ]; then
    COMPOSE_FILE="docker-compose.prod-minimal.yml"
    echo "🚀 Starting NL-FHIR Production (Minimal Mode - No HAPI FHIR)..."
    echo "=============================================================="
    echo "⚠️  Using local validation only (fhir.resources library)"
else
    COMPOSE_FILE="docker-compose.prod.yml"
    echo "🚀 Starting NL-FHIR Production Stack (Full Mode)..."
    echo "===================================================="
    echo "✅ Using HAPI FHIR validation server (recommended)"
fi

# Navigate to project root
cd "$(dirname "$0")/.."

# Start services
docker-compose -f "$COMPOSE_FILE" up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
echo ""

# Wait for services to be healthy
timeout=60
elapsed=0
interval=5

while [ $elapsed -lt $timeout ]; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
        health_check=$(docker-compose -f docker-compose.prod.yml ps --format json 2>/dev/null | jq -r '.[] | select(.Health != null) | .Health' 2>/dev/null || echo "")

        if echo "$health_check" | grep -q "healthy"; then
            echo "✅ Services are healthy!"
            break
        fi
    fi

    echo "   Still starting... (${elapsed}s elapsed)"
    sleep $interval
    elapsed=$((elapsed + interval))
done

echo ""
echo "================================================"
echo "✅ NL-FHIR Production Stack is running!"
echo "================================================"
echo ""
echo "Access points:"
echo "  📱 Web UI:        http://localhost:8001"
echo "  📚 API Docs:      http://localhost:8001/docs"

if [ "$MODE" = "minimal" ]; then
    echo "  ⚠️  HAPI FHIR:     Disabled (using local validation)"
else
    echo "  🏥 HAPI FHIR:     http://localhost:8081/fhir"
fi

echo ""
echo "Container status:"
docker-compose -f "$COMPOSE_FILE" ps
echo ""
echo "Commands:"
echo "  View logs:        docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services:    ./scripts/docker-prod-stop.sh $MODE"
echo "  Restart:          docker-compose -f $COMPOSE_FILE restart"
