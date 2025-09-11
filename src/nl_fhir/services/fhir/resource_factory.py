"""
FHIR Resource Factory for Epic 3
Creates FHIR R4 resources from NLP structured data
HIPAA Compliant: Secure resource creation with validation
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from uuid import uuid4

try:
    from fhir.resources.patient import Patient
    from fhir.resources.practitioner import Practitioner
    from fhir.resources.medicationrequest import MedicationRequest
    from fhir.resources.servicerequest import ServiceRequest
    from fhir.resources.condition import Condition
    from fhir.resources.encounter import Encounter
    from fhir.resources.observation import Observation
    from fhir.resources.codeableconcept import CodeableConcept
    from fhir.resources.coding import Coding
    from fhir.resources.reference import Reference
    from fhir.resources.identifier import Identifier
    from fhir.resources.dosage import Dosage
    from fhir.resources.timing import Timing
    from fhir.resources.quantity import Quantity
    FHIR_AVAILABLE = True
except ImportError:
    FHIR_AVAILABLE = False
    # Define minimal stubs for fallback mode
    class CodeableConcept:
        pass
    class Coding:
        pass
    class Reference:
        pass
    class Identifier:
        pass
    class Dosage:
        pass
    class Timing:
        pass
    class Quantity:
        pass

logger = logging.getLogger(__name__)


class FHIRResourceFactory:
    """Factory for creating FHIR R4 resources from structured medical data"""
    
    def __init__(self):
        self.initialized = False
        self._resource_id_counter = 0
        
    def initialize(self) -> bool:
        """Initialize FHIR resource factory"""
        if not FHIR_AVAILABLE:
            logger.warning("FHIR resources library not available - using fallback implementation")
            self.initialized = True
            return True
            
        try:
            logger.info("FHIR resource factory initialized with fhir.resources library")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize FHIR resource factory: {e}")
            return False
    
    def create_patient_resource(self, patient_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR Patient resource from patient data"""
        
        if not FHIR_AVAILABLE:
            return self._create_fallback_patient(patient_data, request_id)
            
        try:
            # Extract patient information from NLP data
            patient_ref = patient_data.get("patient_ref", f"PT-{self._generate_id()}")
            
            # Create FHIR Patient resource
            patient = Patient(
                id=self._generate_resource_id("Patient"),
                identifier=[
                    Identifier(
                        system="http://hospital.local/patient-id",
                        value=patient_ref
                    )
                ],
                active=True,
                meta={
                    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
                }
            )
            
            # Add name if available (usually not from clinical orders)
            if patient_data.get("name"):
                from fhir.resources.humanname import HumanName
                patient.name = [HumanName(text=patient_data["name"])]
            
            return patient.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create Patient resource: {e}")
            return self._create_fallback_patient(patient_data, request_id)
    
    def create_medication_request(self, medication_data: Dict[str, Any], patient_ref: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR MedicationRequest resource from medication data"""
        
        if not FHIR_AVAILABLE:
            return self._create_fallback_medication_request(medication_data, patient_ref, request_id)
            
        try:
            # Create medication CodeableConcept
            medication_concept = self._create_medication_concept(medication_data)
            
            # Create dosage instruction
            dosage_instruction = self._create_dosage_instruction(medication_data)
            
            # Create MedicationRequest
            med_request = MedicationRequest(
                id=self._generate_resource_id("MedicationRequest"),
                status="active",
                intent="order",
                medicationCodeableConcept=medication_concept,
                subject=Reference(reference=f"Patient/{patient_ref}"),
                authoredOn=datetime.now(timezone.utc).isoformat(),
                dosageInstruction=[dosage_instruction] if dosage_instruction else [],
                meta={
                    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest"]
                }
            )
            
            return med_request.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create MedicationRequest resource: {e}")
            return self._create_fallback_medication_request(medication_data, patient_ref, request_id)
    
    def create_service_request(self, service_data: Dict[str, Any], patient_ref: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR ServiceRequest resource from lab/procedure data"""
        
        if not FHIR_AVAILABLE:
            return self._create_fallback_service_request(service_data, patient_ref, request_id)
            
        try:
            # Create service CodeableConcept
            service_concept = self._create_service_concept(service_data)
            
            # Create ServiceRequest
            service_request = ServiceRequest(
                id=self._generate_resource_id("ServiceRequest"),
                status="active",
                intent="order",
                code=service_concept,
                subject=Reference(reference=f"Patient/{patient_ref}"),
                authoredOn=datetime.now(timezone.utc).isoformat(),
                priority=service_data.get("urgency", "routine"),
                meta={
                    "profile": ["http://hl7.org/fhir/ServiceRequest"]
                }
            )
            
            # Add category for lab tests
            if service_data.get("type") == "laboratory":
                service_request.category = [
                    CodeableConcept(
                        coding=[
                            Coding(
                                system="http://snomed.info/sct",
                                code="108252007",
                                display="Laboratory procedure"
                            )
                        ]
                    )
                ]
            
            return service_request.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create ServiceRequest resource: {e}")
            return self._create_fallback_service_request(service_data, patient_ref, request_id)
    
    def create_condition_resource(self, condition_data: Dict[str, Any], patient_ref: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR Condition resource from condition data"""
        
        if not FHIR_AVAILABLE:
            return self._create_fallback_condition(condition_data, patient_ref, request_id)
            
        try:
            # Create condition CodeableConcept
            condition_concept = self._create_condition_concept(condition_data)
            
            # Create Condition
            condition = Condition(
                id=self._generate_resource_id("Condition"),
                clinicalStatus=CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                            code="active",
                            display="Active"
                        )
                    ]
                ),
                verificationStatus=CodeableConcept(
                    coding=[
                        Coding(
                            system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
                            code="confirmed",
                            display="Confirmed"
                        )
                    ]
                ),
                code=condition_concept,
                subject=Reference(reference=f"Patient/{patient_ref}"),
                recordedDate=datetime.now(timezone.utc).isoformat(),
                meta={
                    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"]
                }
            )
            
            return condition.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create Condition resource: {e}")
            return self._create_fallback_condition(condition_data, patient_ref, request_id)
    
    def create_encounter_resource(self, encounter_data: Dict[str, Any], patient_ref: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR Encounter resource for the clinical visit"""
        
        if not FHIR_AVAILABLE:
            return self._create_fallback_encounter(encounter_data, patient_ref, request_id)
            
        try:
            # Create Encounter
            encounter = Encounter(
                id=self._generate_resource_id("Encounter"),
                status="finished",
                class_=Coding(
                    system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    code="AMB",
                    display="ambulatory"
                ),
                subject=Reference(reference=f"Patient/{patient_ref}"),
                period={
                    "start": datetime.now(timezone.utc).isoformat(),
                    "end": datetime.now(timezone.utc).isoformat()
                },
                meta={
                    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter"]
                }
            )
            
            return encounter.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create Encounter resource: {e}")
            return self._create_fallback_encounter(encounter_data, patient_ref, request_id)
    
    def _create_medication_concept(self, medication_data: Dict[str, Any]) -> CodeableConcept:
        """Create medication CodeableConcept with RxNorm codes"""
        
        codings = []
        medication_name = medication_data.get("name", "")
        
        # Add RxNorm code if available
        medical_codes = medication_data.get("medical_codes", [])
        for code_info in medical_codes:
            if code_info.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm":
                codings.append(Coding(
                    system=code_info["system"],
                    code=code_info["code"],
                    display=code_info.get("display", medication_name)
                ))
        
        # Add text description
        if not codings:
            codings.append(Coding(
                system="http://www.nlm.nih.gov/research/umls/rxnorm",
                display=medication_name
            ))
        
        return CodeableConcept(
            coding=codings,
            text=medication_name
        )
    
    def _create_service_concept(self, service_data: Dict[str, Any]) -> CodeableConcept:
        """Create service CodeableConcept with LOINC codes"""
        
        codings = []
        service_name = service_data.get("name", "")
        
        # Add LOINC code if available
        medical_codes = service_data.get("medical_codes", [])
        for code_info in medical_codes:
            if code_info.get("system") == "http://loinc.org":
                codings.append(Coding(
                    system=code_info["system"],
                    code=code_info["code"],
                    display=code_info.get("display", service_name)
                ))
        
        # Add text description
        if not codings:
            codings.append(Coding(
                display=service_name
            ))
        
        return CodeableConcept(
            coding=codings,
            text=service_name
        )
    
    def _create_condition_concept(self, condition_data: Dict[str, Any]) -> CodeableConcept:
        """Create condition CodeableConcept with ICD-10 codes"""
        
        codings = []
        condition_name = condition_data.get("name", condition_data.get("text", ""))
        
        # Add ICD-10 code if available
        medical_codes = condition_data.get("medical_codes", [])
        for code_info in medical_codes:
            if code_info.get("system") == "http://hl7.org/fhir/sid/icd-10-cm":
                codings.append(Coding(
                    system=code_info["system"],
                    code=code_info["code"],
                    display=code_info.get("display", condition_name)
                ))
        
        # Add text description
        if not codings:
            codings.append(Coding(
                display=condition_name
            ))
        
        return CodeableConcept(
            coding=codings,
            text=condition_name
        )
    
    def _create_dosage_instruction(self, medication_data: Dict[str, Any]) -> Optional[Dosage]:
        """Create FHIR Dosage instruction from medication data"""
        
        if not FHIR_AVAILABLE:
            return None
            
        try:
            dosage_text = []
            
            # Build dosage text
            if medication_data.get("dosage"):
                dosage_text.append(medication_data["dosage"])
            if medication_data.get("frequency"):
                dosage_text.append(medication_data["frequency"])
            if medication_data.get("route"):
                dosage_text.append(f"via {medication_data['route']}")
            
            if not dosage_text:
                return None
                
            dosage = Dosage(
                text=" ".join(dosage_text),
                timing=self._create_timing(medication_data.get("frequency")),
                route=self._create_route_concept(medication_data.get("route")),
                doseAndRate=[
                    {
                        "doseQuantity": self._create_dose_quantity(medication_data.get("dosage"))
                    }
                ] if medication_data.get("dosage") else []
            )
            
            return dosage
            
        except Exception as e:
            logger.warning(f"Failed to create dosage instruction: {e}")
            return None
    
    def _create_timing(self, frequency: Optional[str]) -> Optional[Timing]:
        """Create FHIR Timing from frequency text"""
        if not frequency or not FHIR_AVAILABLE:
            return None
            
        # Simple frequency mapping
        frequency_lower = frequency.lower()
        
        if "once daily" in frequency_lower or "daily" in frequency_lower:
            return Timing(repeat={"frequency": 1, "period": 1, "periodUnit": "d"})
        elif "twice daily" in frequency_lower or "bid" in frequency_lower:
            return Timing(repeat={"frequency": 2, "period": 1, "periodUnit": "d"})
        elif "three times daily" in frequency_lower or "tid" in frequency_lower:
            return Timing(repeat={"frequency": 3, "period": 1, "periodUnit": "d"})
            
        return None
    
    def _create_route_concept(self, route: Optional[str]) -> Optional[CodeableConcept]:
        """Create route CodeableConcept"""
        if not route or not FHIR_AVAILABLE:
            return None
            
        return CodeableConcept(
            coding=[Coding(display=route)],
            text=route
        )
    
    def _create_dose_quantity(self, dosage: Optional[str]) -> Optional[Quantity]:
        """Create dose Quantity from dosage text"""
        if not dosage or not FHIR_AVAILABLE:
            return None
            
        # Simple dosage parsing (e.g., "500mg")
        import re
        match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)', dosage)
        if match:
            value, unit = match.groups()
            return Quantity(
                value=float(value),
                unit=unit,
                system="http://unitsofmeasure.org"
            )
            
        return None
    
    def _generate_resource_id(self, resource_type: str) -> str:
        """Generate unique resource ID"""
        self._resource_id_counter += 1
        return f"{resource_type}-{self._resource_id_counter}-{str(uuid4())[:8]}"
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return str(uuid4())[:8]
    
    # Fallback methods for when FHIR library is not available
    
    def _create_fallback_patient(self, patient_data: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback Patient resource"""
        return {
            "resourceType": "Patient",
            "id": self._generate_resource_id("Patient"),
            "identifier": [
                {
                    "system": "http://hospital.local/patient-id",
                    "value": patient_data.get("patient_ref", f"PT-{self._generate_id()}")
                }
            ],
            "active": True
        }
    
    def _create_fallback_medication_request(self, medication_data: Dict[str, Any], patient_ref: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback MedicationRequest resource"""
        return {
            "resourceType": "MedicationRequest",
            "id": self._generate_resource_id("MedicationRequest"),
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": medication_data.get("name", "")
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            },
            "authoredOn": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_fallback_service_request(self, service_data: Dict[str, Any], patient_ref: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback ServiceRequest resource"""
        return {
            "resourceType": "ServiceRequest",
            "id": self._generate_resource_id("ServiceRequest"),
            "status": "active",
            "intent": "order",
            "code": {
                "text": service_data.get("name", "")
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            },
            "authoredOn": datetime.now(timezone.utc).isoformat()
        }
    
    def _create_fallback_condition(self, condition_data: Dict[str, Any], patient_ref: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback Condition resource"""
        return {
            "resourceType": "Condition",
            "id": self._generate_resource_id("Condition"),
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active"
                    }
                ]
            },
            "code": {
                "text": condition_data.get("name", condition_data.get("text", ""))
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            }
        }
    
    def _create_fallback_encounter(self, encounter_data: Dict[str, Any], patient_ref: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback Encounter resource"""
        return {
            "resourceType": "Encounter",
            "id": self._generate_resource_id("Encounter"),
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB"
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            }
        }


# Global FHIR resource factory instance
_fhir_resource_factory = None

async def get_fhir_resource_factory() -> FHIRResourceFactory:
    """Get initialized FHIR resource factory instance"""
    global _fhir_resource_factory
    
    if _fhir_resource_factory is None:
        _fhir_resource_factory = FHIRResourceFactory()
        _fhir_resource_factory.initialize()
    
    return _fhir_resource_factory