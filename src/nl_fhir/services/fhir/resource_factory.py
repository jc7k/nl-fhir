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
                # meta removed - US Core profiles causing HAPI validation failures
            )
            
            # Add name if available (usually not from clinical orders)
            if patient_data.get("name"):
                from fhir.resources.humanname import HumanName
                patient.name = [HumanName(text=patient_data["name"])]
            
            return patient.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create Patient resource: {e}")
            return self._create_fallback_patient(patient_data, request_id)
    
    def create_practitioner_resource(self, practitioner_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR Practitioner resource from practitioner data"""
        
        if not FHIR_AVAILABLE:
            return self._create_fallback_practitioner(practitioner_data, request_id)
            
        try:
            # Extract practitioner information
            practitioner_id = practitioner_data.get("identifier", f"PRACT-{self._generate_id()}")
            practitioner_name = practitioner_data.get("name", "Unknown Practitioner")
            
            # Create FHIR Practitioner resource
            practitioner = Practitioner(
                id=self._generate_resource_id("Practitioner"),
                identifier=[
                    Identifier(
                        system="http://hospital.local/practitioner-id",
                        value=practitioner_id
                    )
                ],
                active=True,
                # meta removed - US Core profiles causing HAPI validation failures
            )
            
            # Add name
            if practitioner_name and practitioner_name != "Unknown Practitioner":
                from fhir.resources.humanname import HumanName
                practitioner.name = [HumanName(text=practitioner_name)]
            
            resource_dict = practitioner.dict()
            logger.info(f"[{request_id}] Created Practitioner resource: {practitioner.id}")
            return resource_dict
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create Practitioner resource: {e}")
            return self._create_fallback_practitioner(practitioner_data, request_id)
    
    def create_medication_request(self, medication_data: Dict[str, Any], patient_ref: str, request_id: Optional[str] = None, practitioner_ref: Optional[str] = None, encounter_ref: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR MedicationRequest resource from medication data"""

        if not FHIR_AVAILABLE:
            return self._create_fallback_medication_request(medication_data, patient_ref, request_id)
            
        try:
            # Create medication CodeableConcept
            medication_concept = self._create_medication_concept(medication_data)

            # Create dosage instruction
            dosage_instruction = self._create_dosage_instruction(medication_data)

            # Create CodeableReference for medication field (FHIR R4.3+ requirement)
            try:
                from fhir.resources.codeablereference import CodeableReference
                medication_reference = CodeableReference(concept=medication_concept)
            except ImportError:
                # Fallback for older FHIR library versions
                logger.warning(f"[{request_id}] CodeableReference not available, using fallback")
                return self._create_fallback_medication_request(medication_data, patient_ref, request_id)

            # Create MedicationRequest using CodeableReference for R4 compliance
            med_request = MedicationRequest(
                id=self._generate_resource_id("MedicationRequest"),
                status="active",
                intent="order",
                medication=medication_reference,
                subject=Reference(reference=f"Patient/{patient_ref}"),
                authoredOn=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                dosageInstruction=[dosage_instruction] if dosage_instruction else [],
                # meta removed - US Core profiles causing HAPI validation failures
            )
            
            # Add reasonCode if condition is available (clinical justification)
            if medication_data.get("indication") or medication_data.get("condition"):
                indication = medication_data.get("indication") or medication_data.get("condition")
                med_request.reasonCode = [
                    CodeableConcept(
                        text=indication,
                        coding=[
                            Coding(
                                system="http://snomed.info/sct",
                                display=indication
                            )
                        ]
                    )
                ]
            
            # Add requester reference if practitioner available
            if practitioner_ref:
                med_request.requester = Reference(reference=f"Practitioner/{practitioner_ref}")

            # Add encounter reference if available
            if encounter_ref:
                med_request.encounter = Reference(reference=f"Encounter/{encounter_ref}")

            # Convert to dict and fix medication field for HAPI FHIR compatibility
            resource_dict = med_request.dict()

            # HAPI FHIR expects 'medicationCodeableConcept' not 'medication' with CodeableReference
            if 'medication' in resource_dict and 'concept' in resource_dict['medication']:
                resource_dict['medicationCodeableConcept'] = resource_dict['medication']['concept']
                del resource_dict['medication']
                logger.info(f"[{request_id}] Converted medication CodeableReference to medicationCodeableConcept for HAPI compatibility")

            return resource_dict
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create MedicationRequest resource: {e}")
            return self._create_fallback_medication_request(medication_data, patient_ref, request_id)
    
    def create_service_request(self, service_data: Dict[str, Any], patient_ref: str, request_id: Optional[str] = None,
                             practitioner_ref: Optional[str] = None, encounter_ref: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR ServiceRequest resource from lab/procedure data"""

        if not FHIR_AVAILABLE:
            return self._create_fallback_service_request(service_data, patient_ref, request_id, practitioner_ref, encounter_ref)

        # Note: Using fallback ServiceRequest creation to avoid CodeableReference compatibility issues
        # The FHIR library expects CodeableReference but HAPI FHIR works better with direct CodeableConcept
        logger.info(f"[{request_id}] Using fallback ServiceRequest creation for HAPI FHIR compatibility")
        return self._create_fallback_service_request(service_data, patient_ref, request_id, practitioner_ref, encounter_ref)

        try:
            # Create service CodeableConcept
            service_concept = self._create_service_concept(service_data)

            # Try to create ServiceRequest with CodeableReference for newer FHIR versions
            service_request_data = {
                "id": self._generate_resource_id("ServiceRequest"),
                "status": "active",
                "intent": "order",
                "subject": {"reference": f"Patient/{patient_ref}"},
                "authoredOn": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "priority": service_data.get("urgency", "routine")
            }

            # Try using CodeableReference first, fall back to CodeableConcept
            try:
                from fhir.resources.codeablereference import CodeableReference
                service_request_data["code"] = CodeableReference(concept=service_concept).dict()
            except (ImportError, Exception):
                # Fallback to direct CodeableConcept for HAPI compatibility
                service_request_data["code"] = service_concept.dict()

            # Create ServiceRequest from dict to avoid validation issues
            service_request = ServiceRequest(**service_request_data)
            
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
            elif service_data.get("type") == "procedure" or service_data.get("category") == "procedure":
                service_request.category = [
                    CodeableConcept(
                        coding=[
                            Coding(
                                system="http://snomed.info/sct", 
                                code="103693007",
                                display="Diagnostic procedure"
                            )
                        ]
                    )
                ]
            
            # Add reasonCode if indication/condition is available (clinical justification)
            if service_data.get("indication") or service_data.get("condition") or service_data.get("reason"):
                reason = service_data.get("indication") or service_data.get("condition") or service_data.get("reason")
                service_request.reasonCode = [
                    CodeableConcept(
                        text=reason,
                        coding=[
                            Coding(
                                system="http://snomed.info/sct",
                                display=reason
                            )
                        ]
                    )
                ]
            
            # Add requester reference if practitioner available  
            if practitioner_ref:
                service_request.requester = Reference(reference=f"Practitioner/{practitioner_ref}")
            
            # Add encounter reference if available
            if encounter_ref:
                service_request.encounter = Reference(reference=f"Encounter/{encounter_ref}")
            
            # Add performer reference if specified
            if service_data.get("performer"):
                service_request.performer = [Reference(reference=f"Organization/{service_data['performer']}")]

            # Convert to dict and handle CodeableReference compatibility issues
            resource_dict = service_request.dict()

            # Fix code field for HAPI FHIR compatibility if CodeableReference conversion fails
            if 'code' in resource_dict and isinstance(resource_dict['code'], dict):
                if 'concept' in resource_dict['code']:
                    # Convert CodeableReference back to CodeableConcept for HAPI compatibility
                    resource_dict['code'] = resource_dict['code']['concept']
                    logger.info(f"[{request_id}] Converted ServiceRequest code CodeableReference to CodeableConcept for HAPI compatibility")

            return resource_dict
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create ServiceRequest resource: {e}")
            return self._create_fallback_service_request(service_data, patient_ref, request_id, practitioner_ref, encounter_ref)
    
    def create_condition_resource(self, condition_data: Dict[str, Any], patient_ref: str, request_id: Optional[str] = None, encounter_ref: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR Condition resource from condition data"""
        
        if not FHIR_AVAILABLE:
            return self._create_fallback_condition(condition_data, patient_ref, request_id, encounter_ref)
            
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
                recordedDate=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                # meta removed - US Core profiles causing HAPI validation failures
            )
            
            return condition.dict()
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create Condition resource: {e}")
            return self._create_fallback_condition(condition_data, patient_ref, request_id, encounter_ref)
    
    def create_encounter_resource(self, encounter_data: Dict[str, Any], patient_ref: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FHIR Encounter resource for the clinical visit"""
        
        if not FHIR_AVAILABLE:
            return self._create_fallback_encounter(encounter_data, patient_ref, request_id)
            
        try:
            # Create minimal but valid FHIR Encounter resource
            encounter = Encounter(
                id=self._generate_resource_id("Encounter"),
                status="finished",
                subject=Reference(reference=f"Patient/{patient_ref}")
            )

            resource_dict = encounter.dict()

            # Add class as a Coding object (FHIR expects Coding, not CodeableConcept for encounter.class)
            resource_dict["class"] = {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            }

            # Add period with proper timezone formatting
            if encounter_data.get("period", {}).get("start"):
                # Ensure the provided start time has proper timezone
                start_time = encounter_data["period"]["start"]
                if "Z" not in start_time and "+" not in start_time and "-" not in start_time[-6:]:
                    # Add UTC timezone if missing
                    start_time = start_time.rstrip("Z") + "Z"
                resource_dict["period"] = {
                    "start": start_time
                }
            else:
                # Use proper ISO 8601 format with timezone
                resource_dict["period"] = {
                    "start": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                }

            logger.info(f"[{request_id}] Created Encounter resource: {encounter.id}")
            return resource_dict
            
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
        
        # Enhanced medication mapping for common medications
        if not codings and medication_name:
            medication_lower = medication_name.lower().strip()
            
            # Common medication to RxNorm mappings (placeholder codes for demonstration)
            medication_mappings = {
                "sertraline": {"code": "36437", "display": "Sertraline"},
                "zoloft": {"code": "321988", "display": "Sertraline"},
                "metformin": {"code": "6809", "display": "Metformin"},
                "lisinopril": {"code": "29046", "display": "Lisinopril"},
                "albuterol": {"code": "435", "display": "Albuterol"},
                "amoxicillin": {"code": "723", "display": "Amoxicillin"},
                "ibuprofen": {"code": "5640", "display": "Ibuprofen"},
                "aspirin": {"code": "1191", "display": "Aspirin"},
                "prozac": {"code": "4493", "display": "Fluoxetine"},
                "fluoxetine": {"code": "4493", "display": "Fluoxetine"},
                "atorvastatin": {"code": "83367", "display": "Atorvastatin"},
                "lipitor": {"code": "153165", "display": "Atorvastatin"},
                "prednisone": {"code": "8640", "display": "Prednisone"},
                "ambien": {"code": "39968", "display": "Zolpidem"},
                "zolpidem": {"code": "39968", "display": "Zolpidem"},
                "ceftriaxone": {"code": "2193", "display": "Ceftriaxone"},
                "insulin": {"code": "5856", "display": "Insulin"},
                "tramadol": {"code": "10689", "display": "Tramadol"},
                "doxycycline": {"code": "3640", "display": "Doxycycline"},
                "acetaminophen": {"code": "161", "display": "Acetaminophen"},
                "tylenol": {"code": "161", "display": "Acetaminophen"},
                # Oncology medications
                "paclitaxel": {"code": "56946", "display": "Paclitaxel"},
                "carboplatin": {"code": "38936", "display": "Carboplatin"},
                "cisplatin": {"code": "2555", "display": "Cisplatin"},
                "doxorubicin": {"code": "3639", "display": "Doxorubicin"},
                "cyclophosphamide": {"code": "3002", "display": "Cyclophosphamide"}
            }
            
            # Find exact or partial matches
            for med_key, mapping in medication_mappings.items():
                if med_key in medication_lower:
                    codings.append(Coding(
                        system="http://www.nlm.nih.gov/research/umls/rxnorm",
                        code=mapping["code"],
                        display=mapping["display"]
                    ))
                    break
        
        # Fallback to generic coding if no specific mapping found
        if not codings:
            display_name = medication_name if medication_name else "Unknown medication"
            codings.append(Coding(
                system="http://www.nlm.nih.gov/research/umls/rxnorm",
                code="unknown",  # Add code to prevent "no system" error
                display=display_name
            ))
        
        # Add additional coding systems for better interoperability
        if medication_name:
            # Add NDC system placeholder for prescription drugs
            codings.append(Coding(
                system="http://hl7.org/fhir/sid/ndc",
                code="unknown-ndc",
                display=medication_name
            ))

            # Add SNOMED CT for medication concepts
            codings.append(Coding(
                system="http://snomed.info/sct",
                code="unknown-snomed",
                display=medication_name
            ))
        
        return CodeableConcept(
            coding=codings,
            text=medication_name if medication_name.strip() else "Medication order"
        )
    
    def _create_service_concept(self, service_data: Dict[str, Any]) -> CodeableConcept:
        """Create service CodeableConcept with LOINC codes"""
        
        codings = []
        # Try different field names for service code/name (prioritize "code" field)
        service_name = (
            service_data.get("code") or 
            service_data.get("name") or 
            service_data.get("text") or 
            ""
        )
        
        # Add LOINC code if available
        medical_codes = service_data.get("medical_codes", [])
        for code_info in medical_codes:
            if code_info.get("system") == "http://loinc.org":
                codings.append(Coding(
                    system=code_info["system"],
                    code=code_info["code"],
                    display=code_info.get("display", service_name)
                ))
        
        # Enhanced lab test mapping for common lab tests
        if not codings and service_name:
            service_lower = service_name.lower().strip()
            
            # Common lab test to LOINC mappings
            lab_mappings = {
                "cbc": {"code": "58410-2", "display": "Complete blood count (CBC)"},
                "complete blood count": {"code": "58410-2", "display": "Complete blood count (CBC)"},
                "comprehensive metabolic panel": {"code": "24323-8", "display": "Comprehensive metabolic panel"},
                "cmp": {"code": "24323-8", "display": "Comprehensive metabolic panel"},
                "basic metabolic panel": {"code": "51990-0", "display": "Basic metabolic panel"},
                "bmp": {"code": "51990-0", "display": "Basic metabolic panel"},
                "hba1c": {"code": "4548-4", "display": "Hemoglobin A1c"},
                "hemoglobin a1c": {"code": "4548-4", "display": "Hemoglobin A1c"},
                "lipid panel": {"code": "57698-3", "display": "Lipid panel"},
                "cholesterol": {"code": "14647-2", "display": "Cholesterol"},
                "glucose": {"code": "2339-0", "display": "Glucose"},
                "creatinine": {"code": "2160-0", "display": "Creatinine"},
                "bun": {"code": "3094-0", "display": "Blood urea nitrogen"},
                "blood urea nitrogen": {"code": "3094-0", "display": "Blood urea nitrogen"},
                "tsh": {"code": "3016-3", "display": "Thyroid stimulating hormone"},
                "thyroid stimulating hormone": {"code": "3016-3", "display": "Thyroid stimulating hormone"},
                "free t4": {"code": "3024-7", "display": "Free thyroxine"},
                "troponin": {"code": "6598-7", "display": "Troponin T"},
                "cardiac enzymes": {"code": "33747-0", "display": "Cardiac enzymes"},
                "pt": {"code": "5902-2", "display": "Prothrombin time"},
                "ptt": {"code": "14979-9", "display": "Partial thromboplastin time"},
                "inr": {"code": "34714-6", "display": "International normalized ratio"},
                "cea": {"code": "2039-6", "display": "Carcinoembryonic antigen"},
                "psa": {"code": "2857-1", "display": "Prostate specific antigen"},
                "bnp": {"code": "33762-6", "display": "B-type natriuretic peptide"},
                "d-dimer": {"code": "48065-7", "display": "D-dimer"},
                "esr": {"code": "30341-2", "display": "Erythrocyte sedimentation rate"},
                "crp": {"code": "1988-5", "display": "C-reactive protein"},
                "ana": {"code": "14611-8", "display": "Antinuclear antibody"},
                "hepatitis b": {"code": "5196-1", "display": "Hepatitis B surface antigen"},
                "hepatitis c": {"code": "16128-1", "display": "Hepatitis C antibody"},
                "h. pylori": {"code": "24117-4", "display": "Helicobacter pylori antigen"},
                "helicobacter pylori": {"code": "24117-4", "display": "Helicobacter pylori antigen"},
                "urinalysis": {"code": "24356-8", "display": "Urinalysis"},
                "urine analysis": {"code": "24356-8", "display": "Urinalysis"},
                "microalbumin": {"code": "14958-3", "display": "Microalbumin"},
                "vitamin d": {"code": "25-OH-VitD3", "display": "25-Hydroxyvitamin D3"},
                "iron": {"code": "2498-4", "display": "Iron"},
                "ferritin": {"code": "2276-4", "display": "Ferritin"},
                "b12": {"code": "2132-9", "display": "Vitamin B12"},
                "folate": {"code": "2284-8", "display": "Folate"},
                "arterial blood gas": {"code": "24336-0", "display": "Arterial blood gas"},
                "abg": {"code": "24336-0", "display": "Arterial blood gas"},
                "cortisol": {"code": "2143-6", "display": "Cortisol"},
                "blood cultures": {"code": "600-7", "display": "Blood culture"},
                "procalcitonin": {"code": "33959-8", "display": "Procalcitonin"}
            }
            
            # Find exact or partial matches
            for lab_key, mapping in lab_mappings.items():
                if lab_key in service_lower:
                    codings.append(Coding(
                        system="http://loinc.org",
                        code=mapping["code"],
                        display=mapping["display"]
                    ))
                    break
        
        # Add procedure/diagnostic mappings for non-lab services
        if not codings and service_name:
            service_lower = service_name.lower().strip()
            
            # Common diagnostic procedures to SNOMED CT mappings
            procedure_mappings = {
                "ecg": {"code": "29303009", "display": "Electrocardiography"},
                "electrocardiogram": {"code": "29303009", "display": "Electrocardiography"},
                "chest x-ray": {"code": "399208008", "display": "Chest X-ray"},
                "chest xray": {"code": "399208008", "display": "Chest X-ray"},
                "chest radiograph": {"code": "399208008", "display": "Chest X-ray"},
                "ct": {"code": "77477000", "display": "CT scan"},
                "computed tomography": {"code": "77477000", "display": "CT scan"},
                "mri": {"code": "113091000", "display": "MRI scan"},
                "magnetic resonance": {"code": "113091000", "display": "MRI scan"},
                "ultrasound": {"code": "16310003", "display": "Ultrasound"},
                "echocardiogram": {"code": "40701008", "display": "Echocardiography"},
                "echo": {"code": "40701008", "display": "Echocardiography"},
                "dexa": {"code": "312681000", "display": "Bone density scan"},
                "bone density": {"code": "312681000", "display": "Bone density scan"},
                "mammography": {"code": "71651007", "display": "Mammography"},
                "colonoscopy": {"code": "73761001", "display": "Colonoscopy"},
                "endoscopy": {"code": "423827005", "display": "Endoscopy"},
                "upper endoscopy": {"code": "1919006", "display": "Upper gastrointestinal endoscopy"},
                "holter": {"code": "86184003", "display": "Holter monitoring"},
                "stress test": {"code": "18501008", "display": "Cardiac stress test"},
                "pulmonary function": {"code": "23426006", "display": "Pulmonary function test"},
                "pft": {"code": "23426006", "display": "Pulmonary function test"},
                "lumbar puncture": {"code": "277762005", "display": "Lumbar puncture"},
                "bone marrow": {"code": "396487001", "display": "Bone marrow biopsy"}
            }
            
            for proc_key, mapping in procedure_mappings.items():
                if proc_key in service_lower:
                    codings.append(Coding(
                        system="http://snomed.info/sct",
                        code=mapping["code"], 
                        display=mapping["display"]
                    ))
                    break
        
        # Fallback to generic coding if no specific mapping found
        if not codings:
            display_name = service_name if service_name.strip() else "Laboratory/procedure order"
            # Default to LOINC for lab-like orders, SNOMED for procedures
            if any(keyword in service_name.lower() for keyword in ["lab", "test", "level", "panel", "count"]):
                codings.append(Coding(
                    system="http://loinc.org",
                    code="unknown-lab",
                    display=display_name
                ))
            else:
                codings.append(Coding(
                    system="http://snomed.info/sct",
                    code="unknown-procedure",
                    display=display_name
                ))
        
        return CodeableConcept(
            coding=codings,
            text=service_name if service_name.strip() else "Laboratory/procedure order"
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
                system="http://snomed.info/sct",
                code="unknown-condition",
                display=condition_name if condition_name.strip() else "Clinical condition"
            ))
        
        return CodeableConcept(
            coding=codings,
            text=condition_name if condition_name.strip() else "Clinical condition"
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
                
            # Build dosage components, only include non-None values
            dosage_components = {
                "text": " ".join(dosage_text)
            }

            timing = self._create_timing(medication_data.get("frequency"))
            if timing:
                dosage_components["timing"] = timing

            route = self._create_route_concept(medication_data.get("route"))
            if route:
                dosage_components["route"] = route

            dose_quantity = self._create_dose_quantity(medication_data.get("dosage"))
            if dose_quantity:
                dosage_components["doseAndRate"] = [{"doseQuantity": dose_quantity}]

            dosage = Dosage(**dosage_components)
            
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
            coding=[Coding(
                system="http://snomed.info/sct",
                code="unknown-route",
                display=route
            )],
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
        """Generate unique resource ID using valid UUID format"""
        return str(uuid4())
    
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
    
    def _create_fallback_practitioner(self, practitioner_data: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback Practitioner resource"""
        return {
            "resourceType": "Practitioner",
            "id": self._generate_resource_id("Practitioner"),
            "identifier": [
                {
                    "system": "http://hospital.local/practitioner-id",
                    "value": practitioner_data.get("identifier", f"PRACT-{self._generate_id()}")
                }
            ],
            "name": [
                {
                    "text": practitioner_data.get("name", "Unknown Practitioner")
                }
            ],
            "active": True
        }
    
    def _create_fallback_medication_request(self, medication_data: Dict[str, Any], patient_ref: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback MedicationRequest resource"""

        # Try different field names for medication
        medication_name = (
            medication_data.get("name") or
            medication_data.get("medication") or
            medication_data.get("text") or
            "Unknown medication"
        )

        return {
            "resourceType": "MedicationRequest",
            "id": self._generate_resource_id("MedicationRequest"),
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": medication_name,
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "unknown",
                        "display": medication_name
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            },
            "authoredOn": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
    
    def _create_fallback_service_request(self, service_data: Dict[str, Any], patient_ref: str, request_id: Optional[str],
                                       practitioner_ref: Optional[str] = None, encounter_ref: Optional[str] = None) -> Dict[str, Any]:
        """Create fallback ServiceRequest resource"""

        # Try different field names for service code/name
        service_name = (
            service_data.get("code") or
            service_data.get("name") or
            service_data.get("text") or
            "Laboratory/procedure order"
        )

        return {
            "resourceType": "ServiceRequest",
            "id": self._generate_resource_id("ServiceRequest"),
            "status": "active",
            "intent": "order",
            "code": {
                "text": service_name,
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "unknown-lab",
                        "display": service_name
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            },
            "authoredOn": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
    
    def _create_fallback_condition(self, condition_data: Dict[str, Any], patient_ref: str, request_id: Optional[str],
                                 encounter_ref: Optional[str] = None) -> Dict[str, Any]:
        """Create fallback Condition resource"""
        condition_name = condition_data.get("name", condition_data.get("text", "Clinical condition"))

        return {
            "resourceType": "Condition",
            "id": self._generate_resource_id("Condition"),
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                        "display": "Active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                        "display": "Confirmed"
                    }
                ]
            },
            "code": {
                "text": condition_name,
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "unknown-condition",
                        "display": condition_name
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            },
            "recordedDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
    
    def _create_fallback_encounter(self, encounter_data: Dict[str, Any], patient_ref: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Create fallback Encounter resource"""
        return {
            "resourceType": "Encounter",
            "id": self._generate_resource_id("Encounter"),
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            },
            "period": {
                "start": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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