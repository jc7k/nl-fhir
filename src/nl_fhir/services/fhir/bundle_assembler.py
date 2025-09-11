"""
FHIR Bundle Assembler for Epic 3
Assembles FHIR resources into transaction bundles
HIPAA Compliant: Secure bundle creation and validation
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

try:
    from fhir.resources.bundle import Bundle, BundleEntry, BundleEntryRequest
    from fhir.resources.meta import Meta
    FHIR_AVAILABLE = True
except ImportError:
    FHIR_AVAILABLE = False

logger = logging.getLogger(__name__)


class FHIRBundleAssembler:
    """Assembles FHIR resources into transaction bundles"""
    
    def __init__(self):
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize FHIR bundle assembler"""
        if not FHIR_AVAILABLE:
            logger.warning("FHIR resources library not available - using fallback implementation")
            self.initialized = True
            return True
            
        try:
            logger.info("FHIR bundle assembler initialized with fhir.resources library")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize FHIR bundle assembler: {e}")
            return False
    
    def create_transaction_bundle(self, resources: List[Dict[str, Any]], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR transaction bundle from list of resources"""
        
        if not self.initialized:
            self.initialize()
            
        if not FHIR_AVAILABLE:
            return self._create_fallback_bundle(resources, request_id)
            
        try:
            # Create bundle entries from resources
            entries = []
            
            for resource in resources:
                entry = self._create_bundle_entry(resource)
                if entry:
                    entries.append(entry)
            
            # Create the transaction bundle
            bundle = Bundle(
                id=f"bundle-{str(uuid4())}",
                type="transaction",
                timestamp=datetime.now(timezone.utc).isoformat(),
                entry=entries,
                meta=Meta(
                    profile=["http://hl7.org/fhir/StructureDefinition/Bundle"]
                )
            )
            
            logger.info(f"[{request_id}] Created transaction bundle with {len(entries)} resources")
            return bundle.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create transaction bundle: {e}")
            return self._create_fallback_bundle(resources, request_id)
    
    def create_collection_bundle(self, resources: List[Dict[str, Any]], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR collection bundle (for search results)"""
        
        if not self.initialized:
            self.initialize()
            
        if not FHIR_AVAILABLE:
            return self._create_fallback_collection_bundle(resources, request_id)
            
        try:
            # Create bundle entries from resources (without request methods)
            entries = []
            
            for resource in resources:
                entry = BundleEntry(
                    resource=resource,
                    fullUrl=f"urn:uuid:{resource.get('id', str(uuid4()))}"
                )
                entries.append(entry)
            
            # Create the collection bundle
            bundle = Bundle(
                id=f"bundle-{str(uuid4())}",
                type="collection",
                timestamp=datetime.now(timezone.utc).isoformat(),
                total=len(entries),
                entry=entries
            )
            
            logger.info(f"[{request_id}] Created collection bundle with {len(entries)} resources")
            return bundle.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create collection bundle: {e}")
            return self._create_fallback_collection_bundle(resources, request_id)
    
    def validate_bundle_integrity(self, bundle: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate bundle referential integrity and structure"""
        
        try:
            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "resource_count": 0,
                "reference_validation": {}
            }
            
            # Check bundle structure
            if not bundle.get("resourceType") == "Bundle":
                validation_results["errors"].append("Invalid bundle resourceType")
                validation_results["is_valid"] = False
                
            if not bundle.get("type") in ["transaction", "collection", "batch"]:
                validation_results["errors"].append("Invalid bundle type")
                validation_results["is_valid"] = False
            
            # Validate entries
            entries = bundle.get("entry", [])
            validation_results["resource_count"] = len(entries)
            
            if not entries:
                validation_results["warnings"].append("Bundle contains no entries")
            
            # Collect resource IDs for reference validation
            resource_ids = set()
            resource_refs = []
            
            for entry in entries:
                resource = entry.get("resource", {})
                resource_id = resource.get("id")
                resource_type = resource.get("resourceType")
                
                if resource_id and resource_type:
                    resource_ids.add(f"{resource_type}/{resource_id}")
                
                # Find references in the resource
                refs = self._extract_references(resource)
                resource_refs.extend(refs)
            
            # Validate references
            validation_results["reference_validation"] = self._validate_references(resource_ids, resource_refs)
            
            if validation_results["reference_validation"]["broken_references"]:
                validation_results["warnings"].append(
                    f"Found {len(validation_results['reference_validation']['broken_references'])} broken references"
                )
            
            logger.info(f"[{request_id}] Bundle validation completed - valid: {validation_results['is_valid']}")
            return validation_results
            
        except Exception as e:
            logger.error(f"[{request_id}] Bundle validation failed: {e}")
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "resource_count": 0,
                "reference_validation": {}
            }
    
    def optimize_bundle(self, bundle: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Optimize bundle for HAPI FHIR processing"""
        
        try:
            optimized_bundle = bundle.copy()
            
            # Sort entries by dependency order (Patient first, then others)
            entries = optimized_bundle.get("entry", [])
            
            # Separate resources by type for optimal ordering
            patients = []
            practitioners = []
            encounters = []
            conditions = []
            others = []
            
            for entry in entries:
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType")
                
                if resource_type == "Patient":
                    patients.append(entry)
                elif resource_type == "Practitioner":
                    practitioners.append(entry)
                elif resource_type == "Encounter":
                    encounters.append(entry)
                elif resource_type == "Condition":
                    conditions.append(entry)
                else:
                    others.append(entry)
            
            # Reorder entries for optimal processing
            optimized_entries = patients + practitioners + encounters + conditions + others
            optimized_bundle["entry"] = optimized_entries
            
            # Update metadata
            if "meta" not in optimized_bundle:
                optimized_bundle["meta"] = {}
            optimized_bundle["meta"]["lastUpdated"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"[{request_id}] Bundle optimized - reordered {len(entries)} entries")
            return optimized_bundle
            
        except Exception as e:
            logger.error(f"[{request_id}] Bundle optimization failed: {e}")
            return bundle
    
    def _create_bundle_entry(self, resource: Dict[str, Any]) -> Optional[BundleEntry]:
        """Create bundle entry with appropriate request method"""
        
        if not FHIR_AVAILABLE:
            return None
            
        try:
            resource_type = resource.get("resourceType")
            resource_id = resource.get("id")
            
            if not resource_type or not resource_id:
                logger.warning(f"Resource missing type or id: {resource}")
                return None
            
            # Create bundle entry with POST request (for creation)
            entry = BundleEntry(
                resource=resource,
                fullUrl=f"urn:uuid:{resource_id}",
                request=BundleEntryRequest(
                    method="POST",
                    url=resource_type
                )
            )
            
            return entry
            
        except Exception as e:
            logger.error(f"Failed to create bundle entry: {e}")
            return None
    
    def _extract_references(self, resource: Dict[str, Any]) -> List[str]:
        """Extract all references from a FHIR resource"""
        
        references = []
        
        def extract_refs(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "reference" and isinstance(value, str):
                        references.append(value)
                    else:
                        extract_refs(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_refs(item, f"{path}[{i}]" if path else f"[{i}]")
        
        extract_refs(resource)
        return references
    
    def _validate_references(self, resource_ids: set, references: List[str]) -> Dict[str, Any]:
        """Validate that all references point to existing resources"""
        
        valid_references = []
        broken_references = []
        external_references = []
        
        for ref in references:
            # Skip contained references and absolute URLs
            if ref.startswith("#") or ref.startswith("http"):
                external_references.append(ref)
                continue
                
            if ref in resource_ids:
                valid_references.append(ref)
            else:
                broken_references.append(ref)
        
        return {
            "valid_references": valid_references,
            "broken_references": broken_references,
            "external_references": external_references,
            "total_references": len(references)
        }
    
    def get_bundle_summary(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for a bundle"""
        
        try:
            entries = bundle.get("entry", [])
            
            # Count resources by type
            resource_counts = {}
            total_size = 0
            
            for entry in entries:
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType", "Unknown")
                
                resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
                
                # Estimate size (rough JSON string length)
                total_size += len(str(resource))
            
            return {
                "bundle_id": bundle.get("id"),
                "bundle_type": bundle.get("type"),
                "total_entries": len(entries),
                "resource_counts": resource_counts,
                "estimated_size_bytes": total_size,
                "timestamp": bundle.get("timestamp"),
                "has_meta": "meta" in bundle
            }
            
        except Exception as e:
            logger.error(f"Failed to generate bundle summary: {e}")
            return {
                "bundle_id": None,
                "bundle_type": None,
                "total_entries": 0,
                "resource_counts": {},
                "estimated_size_bytes": 0,
                "error": str(e)
            }
    
    # Fallback methods for when FHIR library is not available
    
    def _create_fallback_bundle(self, resources: List[Dict[str, Any]], request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback transaction bundle"""
        
        entries = []
        for resource in resources:
            entry = {
                "resource": resource,
                "request": {
                    "method": "POST",
                    "url": resource.get("resourceType", "Resource")
                }
            }
            entries.append(entry)
        
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{str(uuid4())}",
            "type": "transaction",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry": entries
        }
    
    def _create_fallback_collection_bundle(self, resources: List[Dict[str, Any]], request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback collection bundle"""
        
        entries = []
        for resource in resources:
            entry = {
                "resource": resource
            }
            entries.append(entry)
        
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{str(uuid4())}",
            "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(entries),
            "entry": entries
        }


# Global bundle assembler instance
_bundle_assembler = None

async def get_bundle_assembler() -> FHIRBundleAssembler:
    """Get initialized bundle assembler instance"""
    global _bundle_assembler
    
    if _bundle_assembler is None:
        _bundle_assembler = FHIRBundleAssembler()
        _bundle_assembler.initialize()
    
    return _bundle_assembler