"""
FHIR Validator for Epic 3
Comprehensive FHIR R4 resource and bundle validation
HIPAA Compliant: Secure validation with detailed reporting
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from enum import Enum

try:
    from fhir.resources.bundle import Bundle
    from fhir.resources.patient import Patient
    from fhir.resources.medicationrequest import MedicationRequest
    from fhir.resources.servicerequest import ServiceRequest
    from fhir.resources.condition import Condition
    from fhir.resources.encounter import Encounter
    from pydantic import ValidationError
    FHIR_AVAILABLE = True
except ImportError:
    FHIR_AVAILABLE = False

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """FHIR validation severity levels"""
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class ValidationType(Enum):
    """Types of FHIR validation"""
    STRUCTURE = "structure"
    BUSINESS_RULES = "business_rules"
    TERMINOLOGY = "terminology"
    CARDINALITY = "cardinality"
    REFERENCES = "references"


class ValidationIssue:
    """FHIR validation issue"""
    
    def __init__(self, severity: ValidationSeverity, type_: ValidationType, 
                 location: str, message: str, code: Optional[str] = None):
        self.severity = severity
        self.type = type_
        self.location = location
        self.message = message
        self.code = code
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "severity": self.severity.value,
            "type": self.type.value,
            "location": self.location,
            "message": self.message,
            "code": self.code,
            "timestamp": self.timestamp
        }


class FHIRValidator:
    """Comprehensive FHIR R4 validator"""
    
    def __init__(self):
        self.initialized = False
        self.validation_rules = {}
        
    def initialize(self) -> bool:
        """Initialize FHIR validator"""
        
        try:
            self._load_validation_rules()
            
            if FHIR_AVAILABLE:
                logger.info("FHIR validator initialized with fhir.resources library")
            else:
                logger.warning("FHIR resources library not available - using fallback validation")
                
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize FHIR validator: {e}")
            return False
    
    def _load_validation_rules(self):
        """Load validation rules and constraints"""
        
        # Required fields by resource type
        self.validation_rules = {
            "Patient": {
                "required_fields": ["resourceType", "id"],
                "business_rules": [
                    {"field": "birthDate", "rule": "valid_date", "severity": "warning"},
                    {"field": "gender", "rule": "valid_gender", "severity": "warning"}
                ]
            },
            "MedicationRequest": {
                "required_fields": ["resourceType", "id", "status", "intent", "medicationCodeableConcept", "subject"],
                "business_rules": [
                    {"field": "status", "rule": "valid_medication_status", "severity": "error"},
                    {"field": "intent", "rule": "valid_medication_intent", "severity": "error"},
                    {"field": "dosageInstruction", "rule": "valid_dosage", "severity": "warning"}
                ]
            },
            "ServiceRequest": {
                "required_fields": ["resourceType", "id", "status", "intent", "code", "subject"],
                "business_rules": [
                    {"field": "status", "rule": "valid_service_status", "severity": "error"},
                    {"field": "intent", "rule": "valid_service_intent", "severity": "error"}
                ]
            },
            "Condition": {
                "required_fields": ["resourceType", "id", "subject"],
                "business_rules": [
                    {"field": "clinicalStatus", "rule": "valid_clinical_status", "severity": "warning"},
                    {"field": "verificationStatus", "rule": "valid_verification_status", "severity": "warning"}
                ]
            },
            "Encounter": {
                "required_fields": ["resourceType", "id", "status", "class", "subject"],
                "business_rules": [
                    {"field": "status", "rule": "valid_encounter_status", "severity": "error"}
                ]
            },
            "Bundle": {
                "required_fields": ["resourceType", "id", "type"],
                "business_rules": [
                    {"field": "type", "rule": "valid_bundle_type", "severity": "error"},
                    {"field": "entry", "rule": "valid_bundle_entries", "severity": "error"}
                ]
            }
        }
    
    def validate_resource(self, resource: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate a single FHIR resource"""
        
        if not self.initialized:
            self.initialize()
        
        try:
            resource_type = resource.get("resourceType")
            if not resource_type:
                return {
                    "is_valid": False,
                    "issues": [{
                        "severity": "error",
                        "type": "structure",
                        "location": "root",
                        "message": "Resource missing resourceType",
                        "timestamp": datetime.utcnow().isoformat()
                    }],
                    "validation_source": "nl_fhir_validator"
                }
            
            issues = []
            
            # Structural validation with fhir.resources if available
            if FHIR_AVAILABLE:
                fhir_issues = self._validate_with_fhir_resources(resource, resource_type)
                issues.extend(fhir_issues)
            
            # Custom business rule validation
            custom_issues = self._validate_business_rules(resource, resource_type)
            issues.extend(custom_issues)
            
            # Reference validation
            reference_issues = self._validate_references(resource)
            issues.extend(reference_issues)
            
            # Terminology validation
            terminology_issues = self._validate_terminology(resource, resource_type)
            issues.extend(terminology_issues)
            
            # Determine overall validity
            errors = [issue for issue in issues if issue.get("severity") in ["error", "fatal"]]
            is_valid = len(errors) == 0
            
            result = {
                "is_valid": is_valid,
                "issues": issues,
                "resource_type": resource_type,
                "validation_source": "nl_fhir_validator"
            }
            
            logger.info(f"[{request_id}] Resource validation completed - {resource_type} valid: {is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"[{request_id}] Resource validation failed: {e}")
            return {
                "is_valid": False,
                "issues": [{
                    "severity": "error",
                    "type": "structure",
                    "location": "root",
                    "message": f"Validation error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }],
                "validation_source": "nl_fhir_validator"
            }
    
    def validate_bundle(self, bundle: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate FHIR bundle and all contained resources"""
        
        if not self.initialized:
            self.initialize()
        
        try:
            issues = []
            
            # Validate bundle structure
            bundle_validation = self.validate_resource(bundle, request_id)
            issues.extend(bundle_validation.get("issues", []))
            
            # Validate each entry
            entries = bundle.get("entry", [])
            resource_validations = []
            
            for i, entry in enumerate(entries):
                # Handle both dict and BundleEntry object entries
                if hasattr(entry, 'resource'):
                    # BundleEntry object
                    resource = entry.resource
                    if hasattr(resource, 'dict'):
                        resource = resource.dict()
                elif isinstance(entry, dict):
                    # Dict entry
                    resource = entry.get("resource")
                else:
                    resource = None

                if resource:
                    resource_result = self.validate_resource(resource, request_id)
                    resource_validations.append(resource_result)

                    # Add location context to issues
                    for issue in resource_result.get("issues", []):
                        issue["location"] = f"entry[{i}].resource.{issue.get('location', '')}"

                    issues.extend(resource_result.get("issues", []))
                else:
                    issues.append({
                        "severity": "error",
                        "type": "structure",
                        "location": f"entry[{i}]",
                        "message": "Bundle entry missing resource",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Bundle-specific validations
            bundle_issues = self._validate_bundle_integrity(bundle, request_id)
            issues.extend(bundle_issues)
            
            # Transaction-specific validations for transaction bundles
            if bundle.get("type") == "transaction":
                transaction_issues = self._validate_transaction_bundle(bundle, request_id)
                issues.extend(transaction_issues)
            
            # Determine overall validity
            errors = [issue for issue in issues if issue.get("severity") in ["error", "fatal"]]
            warnings = [issue for issue in issues if issue.get("severity") == "warning"]
            
            result = {
                "is_valid": len(errors) == 0,
                "total_issues": len(issues),
                "errors": errors,
                "warnings": warnings,
                "issues": issues,
                "resource_validations": resource_validations,
                "bundle_type": bundle.get("type"),
                "entry_count": len(entries),
                "validation_source": "nl_fhir_validator"
            }
            
            logger.info(f"[{request_id}] Bundle validation completed - valid: {result['is_valid']}")
            return result
            
        except Exception as e:
            logger.error(f"[{request_id}] Bundle validation failed: {e}")
            return {
                "is_valid": False,
                "issues": [{
                    "severity": "error",
                    "type": "structure",
                    "location": "root",
                    "message": f"Bundle validation error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }],
                "validation_source": "nl_fhir_validator"
            }
    
    def _validate_with_fhir_resources(self, resource: Dict[str, Any], resource_type: str) -> List[Dict[str, Any]]:
        """Validate using fhir.resources library"""
        
        issues = []
        
        try:
            # Map resource types to fhir.resources classes
            resource_classes = {
                "Patient": Patient,
                "MedicationRequest": MedicationRequest,
                "ServiceRequest": ServiceRequest,
                "Condition": Condition,
                "Encounter": Encounter,
                "Bundle": Bundle
            }
            
            resource_class = resource_classes.get(resource_type)
            if resource_class:
                # Attempt to parse with fhir.resources
                try:
                    parsed_resource = resource_class.parse_obj(resource)
                    # If successful, the resource is structurally valid
                    
                except ValidationError as ve:
                    for error in ve.errors():
                        location = ".".join(str(loc) for loc in error["loc"])
                        issues.append({
                            "severity": "error",
                            "type": "structure",
                            "location": location,
                            "message": error["msg"],
                            "code": error["type"],
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
        except Exception as e:
            issues.append({
                "severity": "warning",
                "type": "structure",
                "location": "root",
                "message": f"fhir.resources validation error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return issues
    
    def _validate_business_rules(self, resource: Dict[str, Any], resource_type: str) -> List[Dict[str, Any]]:
        """Validate business rules for resource"""
        
        issues = []
        rules = self.validation_rules.get(resource_type, {})
        
        # Check required fields
        required_fields = rules.get("required_fields", [])
        for field in required_fields:
            if field not in resource:
                issues.append({
                    "severity": "error",
                    "type": "cardinality",
                    "location": field,
                    "message": f"Required field '{field}' is missing",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check business rules
        business_rules = rules.get("business_rules", [])
        for rule in business_rules:
            field = rule["field"]
            rule_name = rule["rule"]
            severity = rule["severity"]
            
            if field in resource:
                validation_result = self._apply_business_rule(resource[field], rule_name, field)
                if not validation_result["valid"]:
                    issues.append({
                        "severity": severity,
                        "type": "business_rules",
                        "location": field,
                        "message": validation_result["message"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        return issues
    
    def _apply_business_rule(self, value: Any, rule_name: str, field_name: str) -> Dict[str, Any]:
        """Apply specific business rule validation"""
        
        try:
            if rule_name == "valid_date":
                # Validate date format
                if isinstance(value, str):
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                return {"valid": True, "message": ""}
                
            elif rule_name == "valid_gender":
                valid_genders = ["male", "female", "other", "unknown"]
                if value in valid_genders:
                    return {"valid": True, "message": ""}
                return {"valid": False, "message": f"Invalid gender value: {value}"}
                
            elif rule_name == "valid_medication_status":
                valid_statuses = ["active", "on-hold", "cancelled", "completed", "entered-in-error", "stopped", "draft", "unknown"]
                if value in valid_statuses:
                    return {"valid": True, "message": ""}
                return {"valid": False, "message": f"Invalid medication status: {value}"}
                
            elif rule_name == "valid_medication_intent":
                valid_intents = ["proposal", "plan", "order", "original-order", "reflex-order", "filler-order", "instance-order", "option"]
                if value in valid_intents:
                    return {"valid": True, "message": ""}
                return {"valid": False, "message": f"Invalid medication intent: {value}"}
                
            elif rule_name == "valid_service_status":
                valid_statuses = ["draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown"]
                if value in valid_statuses:
                    return {"valid": True, "message": ""}
                return {"valid": False, "message": f"Invalid service status: {value}"}
                
            elif rule_name == "valid_service_intent":
                valid_intents = ["proposal", "plan", "directive", "order", "original-order", "reflex-order", "filler-order", "instance-order", "option"]
                if value in valid_intents:
                    return {"valid": True, "message": ""}
                return {"valid": False, "message": f"Invalid service intent: {value}"}
                
            elif rule_name == "valid_bundle_type":
                valid_types = ["document", "message", "transaction", "transaction-response", "batch", "batch-response", "history", "searchset", "collection"]
                if value in valid_types:
                    return {"valid": True, "message": ""}
                return {"valid": False, "message": f"Invalid bundle type: {value}"}
                
            elif rule_name == "valid_bundle_entries":
                if isinstance(value, list) and len(value) > 0:
                    return {"valid": True, "message": ""}
                return {"valid": False, "message": "Bundle must contain at least one entry"}
                
            else:
                return {"valid": True, "message": f"Unknown rule: {rule_name}"}
                
        except Exception as e:
            return {"valid": False, "message": f"Rule validation error: {str(e)}"}
    
    def _validate_references(self, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate resource references"""
        
        issues = []
        references = self._extract_references(resource)
        
        for ref_path, ref_value in references:
            if ref_value:
                # Check reference format
                if not self._is_valid_reference_format(ref_value):
                    issues.append({
                        "severity": "warning",
                        "type": "references",
                        "location": ref_path,
                        "message": f"Invalid reference format: {ref_value}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        return issues
    
    def _extract_references(self, obj: Any, path: str = "") -> List[Tuple[str, str]]:
        """Extract all references from a resource"""
        
        references = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                if key == "reference" and isinstance(value, str):
                    references.append((current_path, value))
                else:
                    references.extend(self._extract_references(value, current_path))
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                references.extend(self._extract_references(item, current_path))
        
        return references
    
    def _is_valid_reference_format(self, reference: str) -> bool:
        """Check if reference format is valid"""
        
        # Skip contained references and absolute URLs
        if reference.startswith("#") or reference.startswith("http"):
            return True
        
        # Check ResourceType/id format
        pattern = r"^[A-Z][a-zA-Z]*\/[A-Za-z0-9\-\.]{1,64}$"
        return bool(re.match(pattern, reference))
    
    def _validate_terminology(self, resource: Dict[str, Any], resource_type: str) -> List[Dict[str, Any]]:
        """Validate terminology and coding"""
        
        issues = []
        
        # Find all CodeableConcept and Coding elements
        codings = self._extract_codings(resource)
        
        for coding_path, coding in codings:
            if isinstance(coding, dict):
                system = coding.get("system")
                code = coding.get("code")
                
                if system and code:
                    # Basic terminology validation
                    validation_result = self._validate_coding(system, code)
                    if not validation_result["valid"]:
                        issues.append({
                            "severity": "warning",
                            "type": "terminology",
                            "location": coding_path,
                            "message": validation_result["message"],
                            "timestamp": datetime.utcnow().isoformat()
                        })
        
        return issues
    
    def _extract_codings(self, obj: Any, path: str = "") -> List[Tuple[str, Dict[str, Any]]]:
        """Extract all coding elements from a resource"""
        
        codings = []
        
        if isinstance(obj, dict):
            # Check if this is a Coding element
            if "system" in obj and "code" in obj:
                codings.append((path, obj))
            
            # Check if this is a CodeableConcept
            if "coding" in obj and isinstance(obj["coding"], list):
                for i, coding in enumerate(obj["coding"]):
                    coding_path = f"{path}.coding[{i}]" if path else f"coding[{i}]"
                    codings.append((coding_path, coding))
            
            # Recurse into other fields
            for key, value in obj.items():
                if key not in ["coding"]:  # Skip already processed fields
                    current_path = f"{path}.{key}" if path else key
                    codings.extend(self._extract_codings(value, current_path))
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                codings.extend(self._extract_codings(item, current_path))
        
        return codings
    
    def _validate_coding(self, system: str, code: str) -> Dict[str, Any]:
        """Validate a specific coding"""
        
        # Basic validation - check if system looks valid
        known_systems = [
            "http://www.nlm.nih.gov/research/umls/rxnorm",  # RxNorm
            "http://loinc.org",  # LOINC
            "http://hl7.org/fhir/sid/icd-10-cm",  # ICD-10
            "http://snomed.info/sct",  # SNOMED CT
            "http://hl7.org/fhir/administrative-gender",  # Gender
            "http://hl7.org/fhir/request-status",  # Request Status
            "http://hl7.org/fhir/request-intent"  # Request Intent
        ]
        
        if not system.startswith("http"):
            return {"valid": False, "message": f"Invalid coding system format: {system}"}
        
        if not code or not code.strip():
            return {"valid": False, "message": "Coding code cannot be empty"}
        
        return {"valid": True, "message": ""}
    
    def _validate_bundle_integrity(self, bundle: Dict[str, Any], request_id: Optional[str]) -> List[Dict[str, Any]]:
        """Validate bundle referential integrity"""
        
        issues = []
        
        try:
            entries = bundle.get("entry", [])
            
            # Collect all resource IDs in the bundle
            resource_ids = set()
            all_references = []
            
            for entry in entries:
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType")
                resource_id = resource.get("id")
                
                if resource_type and resource_id:
                    resource_ids.add(f"{resource_type}/{resource_id}")
                
                # Extract references from this resource
                refs = self._extract_references(resource)
                all_references.extend(refs)
            
            # Check if all internal references are satisfied
            for ref_path, ref_value in all_references:
                if ref_value and not ref_value.startswith("#") and not ref_value.startswith("http"):
                    if ref_value not in resource_ids:
                        issues.append({
                            "severity": "warning",
                            "type": "references",
                            "location": ref_path,
                            "message": f"Reference to missing resource: {ref_value}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
        
        except Exception as e:
            issues.append({
                "severity": "warning",
                "type": "structure",
                "location": "bundle.entry",
                "message": f"Bundle integrity validation error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return issues
    
    def _validate_transaction_bundle(self, bundle: Dict[str, Any], request_id: Optional[str]) -> List[Dict[str, Any]]:
        """Validate transaction bundle specific requirements"""
        
        issues = []
        
        try:
            entries = bundle.get("entry", [])
            
            for i, entry in enumerate(entries):
                request = entry.get("request")
                if not request:
                    issues.append({
                        "severity": "error",
                        "type": "structure",
                        "location": f"entry[{i}].request",
                        "message": "Transaction bundle entry missing request element",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                method = request.get("method")
                url = request.get("url")
                
                if not method:
                    issues.append({
                        "severity": "error",
                        "type": "structure",
                        "location": f"entry[{i}].request.method",
                        "message": "Transaction entry missing HTTP method",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                if not url:
                    issues.append({
                        "severity": "error",
                        "type": "structure",
                        "location": f"entry[{i}].request.url",
                        "message": "Transaction entry missing URL",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                # Validate HTTP method
                if method and method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    issues.append({
                        "severity": "error",
                        "type": "business_rules",
                        "location": f"entry[{i}].request.method",
                        "message": f"Invalid HTTP method: {method}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        except Exception as e:
            issues.append({
                "severity": "warning",
                "type": "structure",
                "location": "bundle",
                "message": f"Transaction bundle validation error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return issues
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation summary statistics"""
        
        try:
            issues = validation_result.get("issues", [])
            
            # Count issues by severity
            severity_counts = {}
            for issue in issues:
                severity = issue.get("severity", "unknown")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count issues by type
            type_counts = {}
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
            
            return {
                "is_valid": validation_result.get("is_valid", False),
                "total_issues": len(issues),
                "severity_breakdown": severity_counts,
                "type_breakdown": type_counts,
                "has_errors": len([i for i in issues if i.get("severity") in ["error", "fatal"]]) > 0,
                "has_warnings": len([i for i in issues if i.get("severity") == "warning"]) > 0,
                "validation_source": validation_result.get("validation_source", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Failed to generate validation summary: {e}")
            return {
                "is_valid": False,
                "total_issues": 0,
                "error": str(e)
            }


# Global FHIR validator instance
_fhir_validator = None

async def get_fhir_validator() -> FHIRValidator:
    """Get initialized FHIR validator instance"""
    global _fhir_validator
    
    if _fhir_validator is None:
        _fhir_validator = FHIRValidator()
        _fhir_validator.initialize()
    
    return _fhir_validator