#!/usr/bin/env python3
"""
Test script to debug ServiceRequest creation specifically
"""

import asyncio
from src.nl_fhir.services.fhir.resource_factory import get_fhir_resource_factory

async def test_service_request_creation():
    """Test ServiceRequest creation with different data formats"""
    
    print("Testing ServiceRequest creation...")
    
    # Get factory
    factory = await get_fhir_resource_factory()
    
    # Test data that mirrors what conversion.py creates
    test_service_data = {
        "code": "cbc",  # This is what conversion.py uses
        "name": "should not be used",
        "category": "laboratory"
    }
    
    print(f"Input service_data: {test_service_data}")
    
    # Create ServiceRequest
    service_request = factory.create_service_request(
        service_data=test_service_data,
        patient_ref="test-patient", 
        request_id="debug-123"
    )
    
    print(f"\nGenerated ServiceRequest:")
    print(f"  Resource Type: {service_request.get('resourceType')}")
    print(f"  ID: {service_request.get('id')}")
    code_section = service_request.get('code', {})
    print(f"  Full code section: {code_section}")
    
    # Check both possible structures: direct text or concept.text
    code_text = (
        code_section.get('text') or 
        code_section.get('concept', {}).get('text') or
        'MISSING'
    )
    print(f"  Code text: '{code_text}'")
    print(f"  Status: {service_request.get('status')}")
    
    # Debug the service_name extraction
    service_name = (
        test_service_data.get("code") or 
        test_service_data.get("name") or 
        test_service_data.get("text") or 
        "Laboratory/procedure order"
    )
    print(f"  Extracted service_name should be: '{service_name}'")
    
    return service_request

if __name__ == "__main__":
    asyncio.run(test_service_request_creation())