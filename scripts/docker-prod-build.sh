#!/bin/bash
# Build production Docker image for NL-FHIR
set -e

echo "🐳 Building NL-FHIR Production Docker Image..."
echo "================================================"

# Navigate to project root
cd "$(dirname "$0")/.."

# Build the image
docker-compose -f docker-compose.prod.yml build --no-cache

echo ""
echo "✅ Production image built successfully!"
echo ""
echo "Image details:"
docker images nl-fhir:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""
echo "Next steps:"
echo "  - Run with HAPI FHIR (recommended):    ./scripts/docker-prod-start.sh"
echo "  - Run without HAPI FHIR (minimal):     ./scripts/docker-prod-start.sh minimal"
echo "  - Stop:                                ./scripts/docker-prod-stop.sh [minimal]"
echo "  - View logs (full):                    docker-compose -f docker-compose.prod.yml logs -f"
echo "  - View logs (minimal):                 docker-compose -f docker-compose.prod-minimal.yml logs -f"
