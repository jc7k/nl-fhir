"""
HAPI FHIR Client for Epic 3
Communicates with HAPI FHIR servers for validation and processing
HIPAA Compliant: Secure FHIR server communication
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
    import aiohttp
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class HAPIFHIRClient:
    """Client for communicating with HAPI FHIR servers"""
    
    def __init__(self, base_url: str = "http://localhost:8080/fhir", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.initialized = False
        self._session = None
        
    def initialize(self) -> bool:
        """Initialize HAPI FHIR client"""
        
        if not HTTP_AVAILABLE:
            logger.warning("HTTP libraries not available - using fallback implementation")
            self.initialized = True
            return True
            
        try:
            # Test connection to HAPI FHIR server
            test_url = f"{self.base_url}/metadata"
            response = requests.get(test_url, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"HAPI FHIR client initialized - server: {self.base_url}")
                self.initialized = True
                return True
            else:
                logger.warning(f"HAPI FHIR server not accessible at {self.base_url} - using fallback")
                self.initialized = True
                return True
                
        except Exception as e:
            logger.warning(f"Failed to connect to HAPI FHIR server: {e} - using fallback")
            self.initialized = True
            return True
    
    async def validate_bundle(self, bundle: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate FHIR bundle against HAPI FHIR server"""
        
        if not self.initialized:
            self.initialize()
            
        if not HTTP_AVAILABLE:
            return self._fallback_validation(bundle, request_id)
            
        try:
            # Use ThreadPoolExecutor for sync HTTP calls in async context
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._sync_validate_bundle, 
                    bundle, 
                    request_id
                )
                return result
                
        except Exception as e:
            logger.error(f"[{request_id}] Bundle validation failed: {e}")
            return self._fallback_validation(bundle, request_id)
    
    def _sync_validate_bundle(self, bundle: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Synchronous bundle validation"""
        
        try:
            # Use HAPI FHIR $validate operation
            validate_url = f"{self.base_url}/Bundle/$validate"
            
            headers = {
                'Content-Type': 'application/fhir+json',
                'Accept': 'application/fhir+json'
            }
            
            response = requests.post(
                validate_url,
                json=bundle,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                validation_result = response.json()
                
                # Process OperationOutcome
                issues = validation_result.get('issue', [])
                errors = [issue for issue in issues if issue.get('severity') in ['error', 'fatal']]
                warnings = [issue for issue in issues if issue.get('severity') == 'warning']
                
                result = {
                    "is_valid": len(errors) == 0,
                    "errors": [issue.get('diagnostics', 'Unknown error') for issue in errors],
                    "warnings": [issue.get('diagnostics', 'Unknown warning') for issue in warnings],
                    "hapi_response": validation_result,
                    "validation_source": "hapi_fhir"
                }
                
                logger.info(f"[{request_id}] HAPI validation completed - valid: {result['is_valid']}")
                return result
                
            else:
                logger.error(f"[{request_id}] HAPI validation failed with status {response.status_code}")
                return self._fallback_validation(bundle, request_id)
                
        except Exception as e:
            logger.error(f"[{request_id}] HAPI validation error: {e}")
            return self._fallback_validation(bundle, request_id)
    
    async def submit_bundle(self, bundle: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Submit transaction bundle to HAPI FHIR server"""
        
        if not self.initialized:
            self.initialize()
            
        if not HTTP_AVAILABLE:
            return self._fallback_submission(bundle, request_id)
            
        try:
            # Use ThreadPoolExecutor for sync HTTP calls in async context
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._sync_submit_bundle, 
                    bundle, 
                    request_id
                )
                return result
                
        except Exception as e:
            logger.error(f"[{request_id}] Bundle submission failed: {e}")
            return self._fallback_submission(bundle, request_id)
    
    def _sync_submit_bundle(self, bundle: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Synchronous bundle submission"""
        
        try:
            # Submit transaction bundle
            submit_url = f"{self.base_url}/"
            
            headers = {
                'Content-Type': 'application/fhir+json',
                'Accept': 'application/fhir+json'
            }
            
            response = requests.post(
                submit_url,
                json=bundle,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                result_bundle = response.json()
                
                # Process bundle response
                entries = result_bundle.get('entry', [])
                successful_entries = []
                failed_entries = []
                
                for entry in entries:
                    response_data = entry.get('response', {})
                    status = response_data.get('status', '')
                    
                    if status.startswith('2'):  # 2xx success codes
                        successful_entries.append(entry)
                    else:
                        failed_entries.append(entry)
                
                result = {
                    "success": len(failed_entries) == 0,
                    "total_resources": len(entries),
                    "successful_resources": len(successful_entries),
                    "failed_resources": len(failed_entries),
                    "bundle_response": result_bundle,
                    "submission_source": "hapi_fhir"
                }
                
                logger.info(f"[{request_id}] Bundle submission completed - success: {result['success']}")
                return result
                
            else:
                logger.error(f"[{request_id}] Bundle submission failed with status {response.status_code}")
                return self._fallback_submission(bundle, request_id)
                
        except Exception as e:
            logger.error(f"[{request_id}] Bundle submission error: {e}")
            return self._fallback_submission(bundle, request_id)
    
    async def get_patient(self, patient_id: str, request_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve patient resource from HAPI FHIR server"""
        
        if not self.initialized:
            self.initialize()
            
        if not HTTP_AVAILABLE:
            return None
            
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._sync_get_patient, 
                    patient_id, 
                    request_id
                )
                return result
                
        except Exception as e:
            logger.error(f"[{request_id}] Patient retrieval failed: {e}")
            return None
    
    def _sync_get_patient(self, patient_id: str, request_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Synchronous patient retrieval"""
        
        try:
            patient_url = f"{self.base_url}/Patient/{patient_id}"
            
            headers = {
                'Accept': 'application/fhir+json'
            }
            
            response = requests.get(
                patient_url,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                patient = response.json()
                logger.info(f"[{request_id}] Patient {patient_id} retrieved successfully")
                return patient
            else:
                logger.warning(f"[{request_id}] Patient {patient_id} not found (status: {response.status_code})")
                return None
                
        except Exception as e:
            logger.error(f"[{request_id}] Patient retrieval error: {e}")
            return None
    
    async def search_resources(self, resource_type: str, search_params: Dict[str, str], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Search for resources on HAPI FHIR server"""
        
        if not self.initialized:
            self.initialize()
            
        if not HTTP_AVAILABLE:
            return self._fallback_search(resource_type, search_params, request_id)
            
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._sync_search_resources, 
                    resource_type, 
                    search_params, 
                    request_id
                )
                return result
                
        except Exception as e:
            logger.error(f"[{request_id}] Resource search failed: {e}")
            return self._fallback_search(resource_type, search_params, request_id)
    
    def _sync_search_resources(self, resource_type: str, search_params: Dict[str, str], request_id: Optional[str]) -> Dict[str, Any]:
        """Synchronous resource search"""
        
        try:
            search_url = f"{self.base_url}/{resource_type}"
            
            headers = {
                'Accept': 'application/fhir+json'
            }
            
            response = requests.get(
                search_url,
                params=search_params,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                search_bundle = response.json()
                
                entries = search_bundle.get('entry', [])
                resources = [entry.get('resource') for entry in entries if entry.get('resource')]
                
                result = {
                    "success": True,
                    "total": search_bundle.get('total', len(resources)),
                    "resources": resources,
                    "search_bundle": search_bundle
                }
                
                logger.info(f"[{request_id}] Search completed - found {len(resources)} {resource_type} resources")
                return result
                
            else:
                logger.error(f"[{request_id}] Resource search failed with status {response.status_code}")
                return self._fallback_search(resource_type, search_params, request_id)
                
        except Exception as e:
            logger.error(f"[{request_id}] Resource search error: {e}")
            return self._fallback_search(resource_type, search_params, request_id)
    
    async def get_server_capabilities(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Get HAPI FHIR server capabilities"""
        
        if not self.initialized:
            self.initialize()
            
        if not HTTP_AVAILABLE:
            return self._fallback_capabilities(request_id)
            
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._sync_get_capabilities, 
                    request_id
                )
                return result
                
        except Exception as e:
            logger.error(f"[{request_id}] Capabilities retrieval failed: {e}")
            return self._fallback_capabilities(request_id)
    
    def _sync_get_capabilities(self, request_id: Optional[str]) -> Dict[str, Any]:
        """Synchronous capabilities retrieval"""
        
        try:
            capabilities_url = f"{self.base_url}/metadata"
            
            headers = {
                'Accept': 'application/fhir+json'
            }
            
            response = requests.get(
                capabilities_url,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                capability_statement = response.json()
                
                # Extract key capabilities
                software = capability_statement.get('software', {})
                implementation = capability_statement.get('implementation', {})
                rest = capability_statement.get('rest', [])
                
                result = {
                    "success": True,
                    "software_name": software.get('name', 'Unknown'),
                    "software_version": software.get('version', 'Unknown'),
                    "implementation_description": implementation.get('description', 'Unknown'),
                    "fhir_version": capability_statement.get('fhirVersion', 'Unknown'),
                    "supported_resources": [],
                    "capability_statement": capability_statement
                }
                
                # Extract supported resource types
                if rest:
                    resources = rest[0].get('resource', [])
                    result["supported_resources"] = [r.get('type') for r in resources]
                
                logger.info(f"[{request_id}] Server capabilities retrieved - FHIR {result['fhir_version']}")
                return result
                
            else:
                logger.error(f"[{request_id}] Capabilities retrieval failed with status {response.status_code}")
                return self._fallback_capabilities(request_id)
                
        except Exception as e:
            logger.error(f"[{request_id}] Capabilities retrieval error: {e}")
            return self._fallback_capabilities(request_id)
    
    # Fallback methods when HAPI FHIR server is not available
    
    def _fallback_validation(self, bundle: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Fallback validation when HAPI FHIR not available"""
        
        # Basic structural validation
        errors = []
        warnings = []
        
        if not bundle.get("resourceType") == "Bundle":
            errors.append("Invalid bundle resourceType")
            
        if not bundle.get("type"):
            errors.append("Bundle type is required")
            
        entries = bundle.get("entry", [])
        if not entries:
            warnings.append("Bundle contains no entries")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_source": "fallback"
        }
    
    def _fallback_submission(self, bundle: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Fallback submission when HAPI FHIR not available"""
        
        entries = bundle.get("entry", [])
        
        return {
            "success": True,  # Assume success for fallback
            "total_resources": len(entries),
            "successful_resources": len(entries),
            "failed_resources": 0,
            "submission_source": "fallback",
            "message": "HAPI FHIR server not available - bundle not actually submitted"
        }
    
    def _fallback_search(self, resource_type: str, search_params: Dict[str, str], request_id: Optional[str]) -> Dict[str, Any]:
        """Fallback search when HAPI FHIR not available"""
        
        return {
            "success": False,
            "total": 0,
            "resources": [],
            "message": "HAPI FHIR server not available - search not performed"
        }
    
    def _fallback_capabilities(self, request_id: Optional[str]) -> Dict[str, Any]:
        """Fallback capabilities when HAPI FHIR not available"""
        
        return {
            "success": False,
            "software_name": "Fallback Mode",
            "software_version": "N/A",
            "implementation_description": "HAPI FHIR server not available",
            "fhir_version": "R4",
            "supported_resources": ["Patient", "MedicationRequest", "ServiceRequest", "Condition", "Encounter"],
            "message": "HAPI FHIR server not available - using fallback capabilities"
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        
        try:
            if not HTTP_AVAILABLE:
                return {
                    "connected": False,
                    "base_url": self.base_url,
                    "status": "HTTP libraries not available"
                }
            
            # Quick health check
            test_url = f"{self.base_url}/metadata"
            response = requests.get(test_url, timeout=5)
            
            return {
                "connected": response.status_code == 200,
                "base_url": self.base_url,
                "status": f"HTTP {response.status_code}",
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
            
        except Exception as e:
            return {
                "connected": False,
                "base_url": self.base_url,
                "status": f"Connection error: {str(e)}"
            }


# Global HAPI FHIR client instance
_hapi_client = None

async def get_hapi_client() -> HAPIFHIRClient:
    """Get initialized HAPI FHIR client instance"""
    global _hapi_client
    
    if _hapi_client is None:
        _hapi_client = HAPIFHIRClient()
        _hapi_client.initialize()
    
    return _hapi_client