"""
FHIR Medication Resource Factory - REFACTOR-004
Specialized factory for medication-related FHIR resources with advanced safety features
"""

from typing import Dict, Any, List, Optional, Union
import logging
import re
import time
import uuid
from datetime import datetime

from .base import BaseResourceFactory

logger = logging.getLogger(__name__)


class MedicationResourceFactory(BaseResourceFactory):
    """
    Factory for medication-related FHIR resources.

    Handles MedicationRequest, MedicationAdministration, Medication,
    MedicationDispense, MedicationStatement resources with advanced features:
    - RxNorm/NDC medication coding
    - Dosage validation and formatting
    - Drug interaction and allergy safety checks
    - Pharmacy workflow support
    - Medication reconciliation
    """

    SUPPORTED_RESOURCES = {
        'MedicationRequest', 'MedicationAdministration', 'Medication',
        'MedicationDispense', 'MedicationStatement'
    }

    def __init__(self, validators=None, coders=None, reference_manager=None):
        """Initialize medication factory with shared components"""
        super().__init__(validators, coders, reference_manager)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._medication_metrics = {}
        self._drug_interaction_cache = {}
        self.logger.info("MedicationResourceFactory initialized with medication safety features")

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _get_required_fields(self, resource_type: str) -> list[str]:
        """
        Get list of required fields for medication resource types.

        Override to use medication-specific field names instead of FHIR field names.

        Args:
            resource_type: FHIR resource type

        Returns:
            List of required field names in input data format
        """
        required_fields_map = {
            'MedicationRequest': ['medication_name'],
            'MedicationAdministration': ['medication_name', 'patient_id'],
            'Medication': ['medication_name'],
            'MedicationDispense': ['medication_name', 'patient_id'],
            'MedicationStatement': ['medication_name', 'patient_id'],
        }

        return required_fields_map.get(resource_type, [])

    def _create_resource(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create medication-related resource based on type"""
        self.logger.debug(f"[{request_id}] Creating {resource_type} resource with MedicationResourceFactory")

        start_time = time.time()

        try:
            if resource_type == 'MedicationRequest':
                resource = self._create_medication_request(data, request_id)
            elif resource_type == 'MedicationAdministration':
                resource = self._create_medication_administration(data, request_id)
            elif resource_type == 'Medication':
                resource = self._create_medication(data, request_id)
            elif resource_type == 'MedicationDispense':
                resource = self._create_medication_dispense(data, request_id)
            elif resource_type == 'MedicationStatement':
                resource = self._create_medication_statement(data, request_id)
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")

            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            self._record_medication_metrics(resource_type, duration_ms, success=True)

            self.logger.info(f"[{request_id}] Created {resource_type} resource in {duration_ms:.2f}ms")
            return resource

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._record_medication_metrics(resource_type, duration_ms, success=False)
            self.logger.error(f"[{request_id}] Failed to create {resource_type}: {e}")
            raise

    def _create_medication_request(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create MedicationRequest resource with safety validation"""
        medication_request = {
            'resourceType': 'MedicationRequest',
            'id': self._generate_medication_id(data, 'request'),
            'status': self._normalize_request_status(data.get('status', 'active')),
            'intent': data.get('intent', 'order')
        }

        # Required patient reference
        if 'patient_ref' in data:
            medication_request['subject'] = {'reference': data['patient_ref']}
        elif 'patient' in data:
            medication_request['subject'] = {'reference': f"Patient/{data['patient']}"}
        elif 'patient_id' in data:
            medication_request['subject'] = {'reference': f"Patient/{data['patient_id']}"}
        else:
            raise ValueError("Patient reference is required for MedicationRequest")

        # Medication coding (required)
        medication_request['medicationCodeableConcept'] = self._create_medication_concept(data)

        # Dosage instructions
        if self._has_dosage_data(data):
            medication_request['dosageInstruction'] = self._process_dosage_instructions(data)

        # Requester (practitioner)
        if 'practitioner_ref' in data:
            medication_request['requester'] = {'reference': data['practitioner_ref']}
        elif 'prescriber' in data:
            medication_request['requester'] = {'reference': f"Practitioner/{data['prescriber']}"}
        elif 'prescriber_id' in data:
            medication_request['requester'] = {'reference': f"Practitioner/{data['prescriber_id']}"}

        # Encounter reference
        if 'encounter_ref' in data:
            medication_request['encounter'] = {'reference': data['encounter_ref']}

        # Authored date
        medication_request['authoredOn'] = data.get('authored_on', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

        # Note/instructions
        if 'note' in data or 'instructions' in data:
            note_text = data.get('note') or data.get('instructions')
            medication_request['note'] = [{
                'text': str(note_text)
            }]

        # Priority
        if 'priority' in data:
            medication_request['priority'] = self._normalize_priority(data['priority'])

        # Substitution preferences
        if 'substitution' in data:
            medication_request['substitution'] = self._process_substitution(data['substitution'])

        # Dispense request
        if self._has_dispense_data(data):
            medication_request['dispenseRequest'] = self._process_dispense_request(data)

        # Safety checks
        if 'patient_allergies' in data:
            safety_result = self._check_medication_allergy_safety(data, data['patient_allergies'])
            if not safety_result.get('is_safe', True):
                # Add safety warnings to note
                if 'note' not in medication_request:
                    medication_request['note'] = []
                for alert in safety_result.get('alerts', []):
                    medication_request['note'].append({
                        'text': f"SAFETY ALERT: {alert['message']}"
                    })

        # Add metadata
        self._add_medication_metadata(medication_request, request_id, 'request')

        return medication_request

    def _create_medication_administration(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create MedicationAdministration resource"""
        med_admin = {
            'resourceType': 'MedicationAdministration',
            'id': self._generate_medication_id(data, 'administration'),
            'status': self._normalize_admin_status(data.get('status', 'completed'))
        }

        # Required patient reference
        if 'patient_id' in data:
            # patient_id should already be in proper FHIR format (Patient/id) from adapter
            patient_ref = data['patient_id']
            if not patient_ref.startswith('Patient/'):
                patient_ref = f"Patient/{patient_ref}"
            med_admin['subject'] = {'reference': patient_ref}
        elif 'patient_ref' in data:
            patient_ref = data['patient_ref']
            if not patient_ref.startswith('Patient/'):
                patient_ref = f"Patient/{patient_ref}"
            med_admin['subject'] = {'reference': patient_ref}
        elif 'patient' in data:
            med_admin['subject'] = {'reference': f"Patient/{data['patient']}"}
        else:
            raise ValueError("Patient reference is required for MedicationAdministration")

        # Medication coding (required)
        med_admin['medicationCodeableConcept'] = self._create_medication_concept(data)

        # Effective time (when administered)
        if 'effective_time' in data:
            med_admin['effectiveDateTime'] = data['effective_time']
        elif 'administered_at' in data:
            med_admin['effectiveDateTime'] = data['administered_at']
        elif 'administration_time' in data:
            med_admin['effectiveDateTime'] = data['administration_time']
        else:
            med_admin['effectiveDateTime'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Performer (who administered)
        if 'performer' in data or 'practitioner_ref' in data or 'performer_id' in data:
            performer_ref = data.get('performer') or data.get('practitioner_ref')
            if not performer_ref and 'performer_id' in data:
                performer_ref = f"Practitioner/{data['performer_id']}"
            if performer_ref:
                med_admin['performer'] = [{
                    'actor': {'reference': performer_ref}
                }]

        # Request reference (MedicationRequest that was administered)
        if 'medication_request_ref' in data:
            med_admin['request'] = {'reference': data['medication_request_ref']}

        # Dosage given
        if self._has_dosage_data(data):
            med_admin['dosage'] = self._process_administration_dosage(data)

        # Device used (if any)
        if 'device' in data:
            med_admin['device'] = [{'reference': f"Device/{data['device']}"}]

        # Note/reason
        if 'note' in data:
            med_admin['note'] = [{'text': str(data['note'])}]

        if 'reason' in data:
            med_admin['reasonCode'] = [self.create_codeable_concept('SNOMED', '182856006', data['reason'])]

        # Add metadata
        self._add_medication_metadata(med_admin, request_id, 'administration')

        return med_admin

    def _create_medication(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create Medication resource for pharmaceutical products"""
        medication = {
            'resourceType': 'Medication',
            'id': self._generate_medication_id(data, 'medication'),
            'status': data.get('status', 'active')
        }

        # Medication coding
        medication['code'] = self._create_medication_concept(data)

        # Form (tablet, capsule, injection, etc.)
        if 'form' in data:
            medication['form'] = self._create_medication_form_concept(data['form'])

        # Amount (strength/concentration)
        if 'amount' in data:
            medication['amount'] = self._process_medication_amount(data['amount'])

        # Ingredients
        if 'ingredients' in data or 'active_ingredient' in data:
            medication['ingredient'] = self._process_medication_ingredients(data)

        # Batch information
        if 'batch' in data:
            medication['batch'] = self._process_medication_batch(data['batch'])

        # Manufacturer
        if 'manufacturer' in data:
            # Create clean ID for manufacturer
            clean_id = re.sub(r'[^a-zA-Z0-9\-\.]', '-', str(data['manufacturer']).lower())
            manufacturer_resource = {'resourceType': 'Organization', 'id': clean_id}
            medication['manufacturer'] = self.create_reference(manufacturer_resource, display=data['manufacturer'])

        # Add metadata
        self._add_medication_metadata(medication, request_id, 'medication')

        return medication

    def _create_medication_dispense(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create MedicationDispense resource for pharmacy operations"""
        dispense = {
            'resourceType': 'MedicationDispense',
            'id': self._generate_medication_id(data, 'dispense'),
            'status': self._normalize_dispense_status(data.get('status', 'completed'))
        }

        # Required patient reference
        if 'patient_ref' in data:
            dispense['subject'] = {'reference': data['patient_ref']}
        elif 'patient' in data:
            dispense['subject'] = {'reference': f"Patient/{data['patient']}"}
        elif 'patient_id' in data:
            dispense['subject'] = {'reference': f"Patient/{data['patient_id']}"}
        else:
            raise ValueError("Patient reference is required for MedicationDispense")

        # Medication coding
        dispense['medicationCodeableConcept'] = self._create_medication_concept(data)

        # Authorizing prescription
        if 'medication_request_ref' in data:
            dispense['authorizingPrescription'] = [{'reference': data['medication_request_ref']}]

        # Quantity dispensed
        if 'quantity' in data:
            dispense['quantity'] = self._process_dispense_quantity(data['quantity'])
        elif 'quantity_dispensed' in data:
            dispense['quantity'] = self._process_dispense_quantity(data['quantity_dispensed'])

        # Days supply
        if 'days_supply' in data:
            dispense['daysSupply'] = {
                'value': float(data['days_supply']),
                'unit': 'day',
                'system': 'http://unitsofmeasure.org',
                'code': 'd'
            }

        # When handed over
        if 'handed_over_at' in data:
            dispense['whenHandedOver'] = data['handed_over_at']
        elif 'dispense_date' in data:
            dispense['whenHandedOver'] = data['dispense_date']

        # Performer (pharmacist)
        if 'performer' in data or 'pharmacist' in data or 'pharmacy_id' in data:
            performer_ref = data.get('performer') or data.get('pharmacist')
            if not performer_ref and 'pharmacy_id' in data:
                performer_ref = f"Organization/{data['pharmacy_id']}"
            if performer_ref:
                dispense['performer'] = [{
                    'actor': {'reference': performer_ref}
                }]

        # Dosage instruction
        if self._has_dosage_data(data):
            dispense['dosageInstruction'] = self._process_dosage_instructions(data)

        # Add metadata
        self._add_medication_metadata(dispense, request_id, 'dispense')

        return dispense

    def _create_medication_statement(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create MedicationStatement resource for medication history"""
        statement = {
            'resourceType': 'MedicationStatement',
            'id': self._generate_medication_id(data, 'statement'),
            'status': self._normalize_statement_status(data.get('status', 'active'))
        }

        # Required patient reference
        if 'patient_ref' in data:
            statement['subject'] = {'reference': data['patient_ref']}
        elif 'patient' in data:
            statement['subject'] = {'reference': f"Patient/{data['patient']}"}
        elif 'patient_id' in data:
            statement['subject'] = {'reference': f"Patient/{data['patient_id']}"}
        else:
            raise ValueError("Patient reference is required for MedicationStatement")

        # Medication coding
        statement['medicationCodeableConcept'] = self._create_medication_concept(data)

        # Effective period
        if 'effective_period' in data:
            statement['effectivePeriod'] = data['effective_period']
        elif 'start_date' in data:
            period = {'start': data['start_date']}
            if 'end_date' in data:
                period['end'] = data['end_date']
            statement['effectivePeriod'] = period
        elif 'effective_period_start' in data:
            period = {'start': data['effective_period_start']}
            if 'effective_period_end' in data:
                period['end'] = data['effective_period_end']
            statement['effectivePeriod'] = period

        # Date asserted
        statement['dateAsserted'] = data.get('date_asserted', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

        # Information source
        if 'informant' in data:
            statement['informationSource'] = {'reference': data['informant']}

        # Derived from (source documents)
        if 'derived_from' in data:
            statement['derivedFrom'] = [{'reference': ref} for ref in data['derived_from']]

        # Dosage
        if self._has_dosage_data(data):
            statement['dosage'] = self._process_dosage_instructions(data)

        # Add metadata
        self._add_medication_metadata(statement, request_id, 'statement')

        return statement

    def _generate_medication_id(self, data: Dict[str, Any], resource_subtype: str) -> str:
        """Generate unique medication resource ID (max 64 chars for FHIR compliance)"""
        if 'id' in data:
            return str(data['id'])

        # Generate short unique ID
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8]

        # Use medication name if available
        if 'medication_name' in data or 'name' in data:
            med_name = data.get('medication_name') or data.get('name')
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', str(med_name).lower())[:10]
            return f"med-{resource_subtype[:3]}-{clean_name}-{short_uuid}"

        return f"med-{resource_subtype[:3]}-{short_uuid}"

    def _normalize_request_status(self, status: str) -> str:
        """Normalize MedicationRequest status"""
        status_map = {
            'active': 'active',
            'on-hold': 'on-hold',
            'cancelled': 'cancelled',
            'completed': 'completed',
            'entered-in-error': 'entered-in-error',
            'stopped': 'stopped',
            'draft': 'draft',
            'unknown': 'unknown'
        }
        return status_map.get(str(status).lower(), 'active')

    def _normalize_admin_status(self, status: str) -> str:
        """Normalize MedicationAdministration status"""
        status_map = {
            'in-progress': 'in-progress',
            'not-done': 'not-done',
            'on-hold': 'on-hold',
            'completed': 'completed',
            'entered-in-error': 'entered-in-error',
            'stopped': 'stopped',
            'unknown': 'unknown'
        }
        return status_map.get(str(status).lower(), 'completed')

    def _normalize_dispense_status(self, status: str) -> str:
        """Normalize MedicationDispense status"""
        status_map = {
            'preparation': 'preparation',
            'in-progress': 'in-progress',
            'cancelled': 'cancelled',
            'on-hold': 'on-hold',
            'completed': 'completed',
            'entered-in-error': 'entered-in-error',
            'stopped': 'stopped',
            'declined': 'declined',
            'unknown': 'unknown'
        }
        return status_map.get(str(status).lower(), 'completed')

    def _normalize_statement_status(self, status: str) -> str:
        """Normalize MedicationStatement status"""
        status_map = {
            'active': 'active',
            'completed': 'completed',
            'entered-in-error': 'entered-in-error',
            'intended': 'intended',
            'stopped': 'stopped',
            'on-hold': 'on-hold',
            'unknown': 'unknown',
            'not-taken': 'not-taken'
        }
        return status_map.get(str(status).lower(), 'active')

    def _normalize_priority(self, priority: str) -> str:
        """Normalize request priority"""
        priority_map = {
            'routine': 'routine',
            'urgent': 'urgent',
            'asap': 'asap',
            'stat': 'stat'
        }
        return priority_map.get(str(priority).lower(), 'routine')

    def _create_medication_concept(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create medication CodeableConcept with RxNorm coding"""
        # Try to extract medication name/code
        medication_name = (
            data.get('medication_name') or
            data.get('name') or
            data.get('medication') or
            'Unknown medication'
        )

        # If we have an RxNorm code, use it
        if 'rxnorm_code' in data:
            return self.create_codeable_concept(
                system='RXNORM',
                code=data['rxnorm_code'],
                display=medication_name
            )

        # If we have an NDC code, use it
        if 'ndc_code' in data:
            return self.create_codeable_concept(
                system='NDC',
                code=data['ndc_code'],
                display=medication_name
            )

        # Otherwise, create a text-only concept
        return {
            'text': str(medication_name)
        }

    def _create_medication_form_concept(self, form: str) -> Dict[str, Any]:
        """Create medication form CodeableConcept"""
        form_codes = {
            'tablet': {'code': '385055001', 'display': 'Tablet'},
            'capsule': {'code': '385049006', 'display': 'Capsule'},
            'injection': {'code': '385219001', 'display': 'Injection'},
            'solution': {'code': '385024007', 'display': 'Solution'},
            'cream': {'code': '385101003', 'display': 'Cream'},
            'ointment': {'code': '385101003', 'display': 'Ointment'},
            'patch': {'code': '34012005', 'display': 'Transdermal patch'},
            'inhaler': {'code': '420317006', 'display': 'Inhaler'}
        }

        form_info = form_codes.get(str(form).lower(), {'code': '421026006', 'display': str(form)})

        return self.create_codeable_concept(
            system='SNOMED',
            code=form_info['code'],
            display=form_info['display']
        )

    def _has_dosage_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains dosage information"""
        return any(key in data for key in ['dosage', 'dose', 'dosing', 'dosageInstruction', 'dose_quantity', 'dose_unit'])

    def _has_dispense_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains dispense request information"""
        return any(key in data for key in ['quantity', 'refills', 'days_supply', 'dispense'])

    def _process_dosage_instructions(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process dosage instructions"""
        dosage_instructions = []

        # Simple dosage text
        if 'dosage' in data and isinstance(data['dosage'], str):
            dosage_instructions.append({
                'text': data['dosage']
            })

        # Structured dosage
        if 'dosing' in data or 'dose' in data:
            dosing_data = data.get('dosing') or data.get('dose')
            if isinstance(dosing_data, dict):
                instruction = {}

                # Text representation
                if 'text' in dosing_data:
                    instruction['text'] = dosing_data['text']

                # Timing
                if 'frequency' in dosing_data or 'timing' in dosing_data:
                    instruction['timing'] = self._process_dosage_timing(dosing_data)

                # Route
                if 'route' in dosing_data:
                    instruction['route'] = self._create_route_concept(dosing_data['route'])

                # Dose quantity
                if 'amount' in dosing_data:
                    instruction['doseAndRate'] = [{
                        'doseQuantity': self._process_dose_quantity(dosing_data['amount'])
                    }]

                dosage_instructions.append(instruction)

        # Legacy dosageInstruction field
        if 'dosageInstruction' in data:
            if isinstance(data['dosageInstruction'], list):
                dosage_instructions.extend(data['dosageInstruction'])
            else:
                dosage_instructions.append(data['dosageInstruction'])

        # Default if none provided
        if not dosage_instructions:
            dosage_instructions.append({
                'text': 'As directed'
            })

        return dosage_instructions

    def _process_administration_dosage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dosage for administration (simpler than instructions)"""
        dosage = {}

        # Text
        if 'dosage' in data and isinstance(data['dosage'], str):
            dosage['text'] = data['dosage']

        # Route
        if 'route' in data:
            dosage['route'] = self._create_route_concept(data['route'])

        # Dose quantity
        if 'dose' in data or 'amount' in data:
            dose_data = data.get('dose') or data.get('amount')
            dosage['dose'] = self._process_dose_quantity(dose_data)
        elif 'dose_quantity' in data:
            # Handle dose_quantity and dose_unit fields
            dose_info = {
                'value': float(data['dose_quantity']),
                'unit': data.get('dose_unit', 'dose'),
                'system': 'http://unitsofmeasure.org',
                'code': data.get('dose_unit', 'dose')
            }
            dosage['dose'] = dose_info

        return dosage

    def _process_dosage_timing(self, dosing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process timing information for dosage"""
        timing = {}

        if 'frequency' in dosing_data:
            freq = dosing_data['frequency']
            if isinstance(freq, str):
                # Parse common frequency patterns
                timing_map = {
                    'once daily': {'frequency': 1, 'period': 1, 'periodUnit': 'd'},
                    'twice daily': {'frequency': 2, 'period': 1, 'periodUnit': 'd'},
                    'three times daily': {'frequency': 3, 'period': 1, 'periodUnit': 'd'},
                    'four times daily': {'frequency': 4, 'period': 1, 'periodUnit': 'd'},
                    'every 4 hours': {'frequency': 1, 'period': 4, 'periodUnit': 'h'},
                    'every 6 hours': {'frequency': 1, 'period': 6, 'periodUnit': 'h'},
                    'every 8 hours': {'frequency': 1, 'period': 8, 'periodUnit': 'h'},
                    'every 12 hours': {'frequency': 1, 'period': 12, 'periodUnit': 'h'}
                }

                timing_info = timing_map.get(freq.lower())
                if timing_info:
                    timing['repeat'] = timing_info

        return timing

    def _create_route_concept(self, route: str) -> Dict[str, Any]:
        """Create route of administration CodeableConcept"""
        route_codes = {
            'oral': {'code': '26643006', 'display': 'Oral'},
            'iv': {'code': '47625008', 'display': 'Intravenous'},
            'im': {'code': '78421000', 'display': 'Intramuscular'},
            'subcutaneous': {'code': '34206005', 'display': 'Subcutaneous'},
            'topical': {'code': '6064005', 'display': 'Topical'},
            'inhalation': {'code': '447694001', 'display': 'Inhalation'},
            'rectal': {'code': '37161004', 'display': 'Rectal'},
            'nasal': {'code': '46713006', 'display': 'Nasal'}
        }

        route_info = route_codes.get(str(route).lower(), {'code': '26643006', 'display': str(route)})

        return self.create_codeable_concept(
            system='SNOMED',
            code=route_info['code'],
            display=route_info['display']
        )

    def _process_dose_quantity(self, dose_data: Any) -> Dict[str, Any]:
        """Process dose quantity"""
        if isinstance(dose_data, str):
            # Parse dose string like "10 mg", "5 ml"
            dose_match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)', dose_data)
            if dose_match:
                value, unit = dose_match.groups()
                return {
                    'value': float(value),
                    'unit': unit,
                    'system': 'http://unitsofmeasure.org',
                    'code': unit
                }

        elif isinstance(dose_data, dict):
            quantity = {}
            if 'value' in dose_data:
                quantity['value'] = float(dose_data['value'])
            if 'unit' in dose_data:
                quantity['unit'] = dose_data['unit']
                quantity['system'] = 'http://unitsofmeasure.org'
                quantity['code'] = dose_data['unit']
            return quantity

        # Default
        return {
            'value': 1,
            'unit': 'dose',
            'system': 'http://unitsofmeasure.org',
            'code': 'dose'
        }

    def _process_medication_amount(self, amount_data: Any) -> Dict[str, Any]:
        """Process medication amount/strength"""
        if isinstance(amount_data, str):
            return {
                'numerator': self._process_dose_quantity(amount_data)
            }

        elif isinstance(amount_data, dict):
            amount = {}
            if 'numerator' in amount_data:
                amount['numerator'] = self._process_dose_quantity(amount_data['numerator'])
            if 'denominator' in amount_data:
                amount['denominator'] = self._process_dose_quantity(amount_data['denominator'])
            return amount

        return {}

    def _process_medication_ingredients(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process medication ingredients"""
        ingredients = []

        # Single active ingredient
        if 'active_ingredient' in data:
            ingredient = {
                'itemCodeableConcept': self.create_codeable_concept('RXNORM', 'unknown', data['active_ingredient']),
                'isActive': True
            }
            if 'strength' in data:
                ingredient['strength'] = self._process_medication_amount(data['strength'])
            ingredients.append(ingredient)

        # Multiple ingredients
        if 'ingredients' in data:
            for ing_data in data['ingredients']:
                if isinstance(ing_data, dict):
                    ingredient = {
                        'itemCodeableConcept': self.create_codeable_concept(
                            'RXNORM', 'unknown', ing_data.get('name', 'Unknown ingredient')
                        ),
                        'isActive': ing_data.get('is_active', True)
                    }
                    if 'strength' in ing_data:
                        ingredient['strength'] = self._process_medication_amount(ing_data['strength'])
                    ingredients.append(ingredient)

        return ingredients

    def _process_medication_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process medication batch information"""
        batch = {}

        if 'lot_number' in batch_data:
            batch['lotNumber'] = str(batch_data['lot_number'])

        if 'expiration_date' in batch_data:
            batch['expirationDate'] = batch_data['expiration_date']

        return batch

    def _process_substitution(self, substitution_data: Any) -> Dict[str, Any]:
        """Process substitution preferences"""
        if isinstance(substitution_data, bool):
            return {
                'allowedBoolean': substitution_data
            }

        elif isinstance(substitution_data, dict):
            substitution = {}
            if 'allowed' in substitution_data:
                substitution['allowedBoolean'] = bool(substitution_data['allowed'])
            if 'reason' in substitution_data:
                substitution['reason'] = self.create_codeable_concept(
                    'http://terminology.hl7.org/CodeSystem/v3-ActReason',
                    'ALTCHOICE',
                    substitution_data['reason']
                )
            return substitution

        return {'allowedBoolean': True}

    def _process_dispense_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dispense request information"""
        dispense_request = {}

        # Quantity
        if 'quantity' in data:
            dispense_request['quantity'] = self._process_dispense_quantity(data['quantity'])

        # Number of repeats allowed
        if 'refills' in data:
            dispense_request['numberOfRepeatsAllowed'] = int(data['refills'])

        # Expected supply duration
        if 'days_supply' in data:
            dispense_request['expectedSupplyDuration'] = {
                'value': float(data['days_supply']),
                'unit': 'day',
                'system': 'http://unitsofmeasure.org',
                'code': 'd'
            }

        # Performer (pharmacy)
        if 'pharmacy' in data:
            dispense_request['performer'] = {'reference': f"Organization/{data['pharmacy']}"}

        return dispense_request

    def _process_dispense_quantity(self, quantity_data: Any) -> Dict[str, Any]:
        """Process dispense quantity"""
        if isinstance(quantity_data, (int, float)):
            return {
                'value': float(quantity_data),
                'unit': 'each',
                'system': 'http://unitsofmeasure.org',
                'code': 'each'
            }

        elif isinstance(quantity_data, str):
            # Parse quantity string
            qty_match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)?', quantity_data)
            if qty_match:
                value, unit = qty_match.groups()
                return {
                    'value': float(value),
                    'unit': unit or 'each',
                    'system': 'http://unitsofmeasure.org',
                    'code': unit or 'each'
                }

        elif isinstance(quantity_data, dict):
            quantity = {}
            if 'value' in quantity_data:
                quantity['value'] = float(quantity_data['value'])
            if 'unit' in quantity_data:
                quantity['unit'] = quantity_data['unit']
                quantity['system'] = 'http://unitsofmeasure.org'
                quantity['code'] = quantity_data['unit']
            return quantity

        return {
            'value': 1,
            'unit': 'each',
            'system': 'http://unitsofmeasure.org',
            'code': 'each'
        }

    def _check_medication_allergy_safety(self, medication_data: Dict[str, Any], patient_allergies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check medication against known patient allergies"""
        safety_result = {
            'is_safe': True,
            'alerts': []
        }

        medication_name = (
            medication_data.get('medication_name') or
            medication_data.get('name') or
            medication_data.get('medication', '')
        ).lower()

        # Check against known allergies
        for allergy in patient_allergies:
            allergen = str(allergy.get('substance', '')).lower()
            criticality = allergy.get('criticality', 'low')

            # Direct match
            if allergen in medication_name or medication_name in allergen:
                safety_result['is_safe'] = False
                safety_result['alerts'].append({
                    'severity': 'high' if criticality == 'high' else 'medium',
                    'message': f"Patient has {criticality} allergy to {allergen}",
                    'allergen': allergen,
                    'medication': medication_name
                })

            # Drug class checks (basic implementation)
            elif self._check_drug_class_allergy(medication_name, allergen):
                safety_result['is_safe'] = False
                safety_result['alerts'].append({
                    'severity': 'high' if criticality == 'high' else 'medium',
                    'message': f"Potential cross-reactivity: {allergen} allergy with {medication_name}",
                    'allergen': allergen,
                    'medication': medication_name
                })

        return safety_result

    def _check_drug_class_allergy(self, medication: str, allergen: str) -> bool:
        """Check for drug class cross-reactivity"""
        # Simple implementation of common drug class allergies
        drug_classes = {
            'penicillin': ['amoxicillin', 'ampicillin', 'penicillin', 'augmentin'],
            'sulfa': ['sulfamethoxazole', 'trimethoprim', 'sulfonamide'],
            'nsaid': ['ibuprofen', 'naproxen', 'aspirin', 'celecoxib'],
            'beta-lactam': ['penicillin', 'amoxicillin', 'cephalexin', 'ceftriaxone']
        }

        for drug_class, medications in drug_classes.items():
            if allergen in drug_class or drug_class in allergen:
                return any(med in medication for med in medications)

        return False

    def _add_medication_metadata(self, resource: Dict[str, Any], request_id: Optional[str], resource_subtype: str):
        """Add metadata to medication resource"""
        if not resource.get('meta'):
            resource['meta'] = {}

        resource['meta']['lastUpdated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        resource['meta']['profile'] = [f"http://hl7.org/fhir/StructureDefinition/{resource['resourceType']}"]

        if request_id:
            if 'tag' not in resource['meta']:
                resource['meta']['tag'] = []
            resource['meta']['tag'].append({
                'system': 'http://hospital.local/request-id',
                'code': request_id
            })
            resource['meta']['tag'].append({
                'system': 'http://hospital.local/medication-subtype',
                'code': resource_subtype
            })

    def _record_medication_metrics(self, resource_type: str, duration_ms: float, success: bool = True):
        """Record medication factory specific metrics"""
        if resource_type not in self._medication_metrics:
            self._medication_metrics[resource_type] = {
                'count': 0,
                'success_count': 0,
                'error_count': 0,
                'total_duration_ms': 0,
                'max_duration_ms': 0,
                'min_duration_ms': float('inf')
            }

        metrics = self._medication_metrics[resource_type]
        metrics['count'] += 1
        metrics['total_duration_ms'] += duration_ms
        metrics['max_duration_ms'] = max(metrics['max_duration_ms'], duration_ms)
        metrics['min_duration_ms'] = min(metrics['min_duration_ms'], duration_ms)

        if success:
            metrics['success_count'] += 1
        else:
            metrics['error_count'] += 1

        # Log performance warning if slow
        if duration_ms > 100:  # >100ms warning threshold (per PRD requirements)
            self.logger.warning(f"Slow {resource_type} creation: {duration_ms:.2f}ms")

    def get_medication_metrics(self) -> Dict[str, Any]:
        """Get medication factory performance metrics"""
        metrics = {}
        for resource_type, data in self._medication_metrics.items():
            if data['count'] > 0:
                metrics[resource_type] = {
                    'count': data['count'],
                    'success_rate': data['success_count'] / data['count'],
                    'error_rate': data['error_count'] / data['count'],
                    'avg_duration_ms': data['total_duration_ms'] / data['count'],
                    'max_duration_ms': data['max_duration_ms'],
                    'min_duration_ms': data['min_duration_ms'] if data['min_duration_ms'] != float('inf') else 0
                }
        return metrics

    def get_health_status(self) -> Dict[str, Any]:
        """Get medication factory health status"""
        total_requests = sum(m['count'] for m in self._medication_metrics.values())
        total_errors = sum(m['error_count'] for m in self._medication_metrics.values())

        if total_requests > 0:
            error_rate = total_errors / total_requests
            avg_duration = sum(m['total_duration_ms'] for m in self._medication_metrics.values()) / total_requests
        else:
            error_rate = 0
            avg_duration = 0

        return {
            'status': 'healthy' if error_rate < 0.05 and avg_duration < 100 else 'degraded',
            'total_requests': total_requests,
            'error_rate': error_rate,
            'avg_duration_ms': avg_duration,
            'supported_resources': list(self.SUPPORTED_RESOURCES),
            'performance_target_met': avg_duration < 100,  # <100ms requirement per PRD
            'safety_checks_enabled': True
        }