"""
REFACTOR-005 + EPIC 7.6 + 7.8: Clinical Resource Factory - Advanced Clinical FHIR Resource Creation
Provides specialized creation for Observation, DiagnosticReport, ServiceRequest, Condition, AllergyIntolerance, RiskAssessment, and ImagingStudy resources
"""

import uuid
import time
import logging
import re
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from .base import BaseResourceFactory


logger = logging.getLogger(__name__)


class ClinicalResourceFactory(BaseResourceFactory):
    """
    Specialized factory for clinical FHIR resources with comprehensive medical coding integration.

    Supports:
    - Observation: Lab results, vital signs, clinical measurements
    - DiagnosticReport: Imaging reports, lab summaries
    - ServiceRequest: Orders, referrals, test requests
    - Condition: Diagnoses, clinical problems
    - AllergyIntolerance: Allergies, adverse reactions

    Features:
    - LOINC/SNOMED/ICD-10/RxNorm coding systems
    - Clinical safety validation
    - Advanced medical terminology mapping
    - Performance optimized for healthcare environments
    """

    SUPPORTED_RESOURCES: Set[str] = {
        'Observation', 'DiagnosticReport', 'ServiceRequest',
        'Condition', 'AllergyIntolerance', 'RiskAssessment', 'ImagingStudy'
    }

    def __init__(self, validators, coders, reference_manager):
        """Initialize clinical factory with medical coding capabilities"""
        super().__init__(validators, coders, reference_manager)

        # Clinical-specific caching and tracking
        self._clinical_metrics = {}
        self._loinc_cache = {}
        self._snomed_cache = {}

        # Initialize clinical coding mappings
        self._init_vital_signs_mapping()
        self._init_lab_test_mapping()
        self._init_diagnostic_procedure_mapping()
        self._init_condition_mapping()
        self._init_allergy_mapping()

        self.logger.info("ClinicalResourceFactory initialized with comprehensive medical coding support")

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the clinical resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _get_required_fields(self, resource_type: str) -> list[str]:
        """
        Get required fields for clinical resource types.

        Override to use clinical-specific field names.
        """
        required_fields_map = {
            'Observation': ['patient_id'],  # Code and status handled by factory
            'DiagnosticReport': ['patient_id'],  # Code and status handled by factory
            'ServiceRequest': ['patient_id'],  # Code and status handled by factory
            'Condition': ['patient_id'],  # Code handled by factory
            'AllergyIntolerance': ['patient_id'],  # Code handled by factory
            'RiskAssessment': ['patient_id'],  # Status handled by factory
            'ImagingStudy': ['patient_id'],  # Status and series handled by factory
        }
        return required_fields_map.get(resource_type, [])

    def _create_resource(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create clinical resource based on type"""
        self.logger.debug(f"[{request_id}] Creating {resource_type} resource with ClinicalResourceFactory")

        start_time = time.time()

        try:
            if resource_type == 'Observation':
                resource = self._create_observation(data, request_id)
            elif resource_type == 'DiagnosticReport':
                resource = self._create_diagnostic_report(data, request_id)
            elif resource_type == 'ServiceRequest':
                resource = self._create_service_request(data, request_id)
            elif resource_type == 'Condition':
                resource = self._create_condition(data, request_id)
            elif resource_type == 'AllergyIntolerance':
                resource = self._create_allergy_intolerance(data, request_id)
            elif resource_type == 'RiskAssessment':
                resource = self._create_risk_assessment(data, request_id)
            elif resource_type == 'ImagingStudy':
                resource = self._create_imaging_study(data, request_id)
            else:
                raise ValueError(f"Unsupported clinical resource type: {resource_type}")

            # Track clinical factory performance
            duration_ms = (time.time() - start_time) * 1000
            self._update_clinical_metrics(resource_type, duration_ms, success=True)

            return resource

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._update_clinical_metrics(resource_type, duration_ms, success=False)
            self.logger.error(f"[{request_id}] Failed to create {resource_type}: {e}")
            raise

    def _create_observation(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create Observation resource with comprehensive LOINC coding"""
        observation = {
            'resourceType': 'Observation',
            'id': self._generate_clinical_id(data, 'obs'),
            'status': self._normalize_observation_status(data.get('status', 'final'))
        }

        # Patient reference (required)
        observation['subject'] = self._create_patient_reference(data)

        # Observation coding with LOINC priority
        observation['code'] = self._create_observation_code(data)

        # Category determination
        observation['category'] = self._determine_observation_category(data, observation['code'])

        # Value processing (supports multiple value types)
        self._add_observation_value(observation, data)

        # Components for complex observations (e.g., blood pressure)
        if 'components' in data:
            observation['component'] = self._process_observation_components(data['components'])

        # Clinical context
        if 'encounter_ref' in data or 'encounter_id' in data:
            observation['encounter'] = self._create_encounter_reference(data)

        if 'performer' in data or 'practitioner_id' in data:
            observation['performer'] = [self._create_practitioner_reference(data)]

        # Effective time
        if 'effective_time' in data:
            observation['effectiveDateTime'] = data['effective_time']
        elif 'observed_at' in data:
            observation['effectiveDateTime'] = data['observed_at']
        else:
            observation['effectiveDateTime'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Device reference (for monitoring equipment)
        if 'device' in data or 'device_id' in data:
            observation['device'] = self._create_device_reference(data)

        # Note/interpretation
        if 'note' in data:
            observation['note'] = [{'text': str(data['note'])}]

        if 'interpretation' in data:
            observation['interpretation'] = [self._create_interpretation_code(data['interpretation'])]

        # Add clinical metadata
        self._add_clinical_metadata(observation, request_id, 'observation')

        return observation

    def _create_diagnostic_report(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create DiagnosticReport resource"""
        report = {
            'resourceType': 'DiagnosticReport',
            'id': self._generate_clinical_id(data, 'report'),
            'status': self._normalize_report_status(data.get('status', 'final'))
        }

        # Patient reference (required)
        report['subject'] = self._create_patient_reference(data)

        # Report coding
        report['code'] = self._create_diagnostic_report_code(data)

        # Category determination
        report['category'] = [self._determine_report_category(data, report['code'])]

        # Effective time
        if 'effective_time' in data:
            report['effectiveDateTime'] = data['effective_time']
        elif 'report_date' in data:
            report['effectiveDateTime'] = data['report_date']
        else:
            report['effectiveDateTime'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        # Issued time
        report['issued'] = data.get('issued', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

        # Performer/author
        if 'performer' in data or 'practitioner_id' in data:
            report['performer'] = [self._create_practitioner_reference(data)]

        # Results (observations)
        if 'observations' in data or 'results' in data:
            report['result'] = self._create_observation_references(data)

        # Service request reference
        if 'service_request' in data or 'order_ref' in data:
            report['basedOn'] = [self._create_service_request_reference(data)]

        # Clinical conclusion
        if 'conclusion' in data:
            report['conclusion'] = data['conclusion']

        # Encounter reference
        if 'encounter_ref' in data or 'encounter_id' in data:
            report['encounter'] = self._create_encounter_reference(data)

        # Add clinical metadata
        self._add_clinical_metadata(report, request_id, 'diagnostic_report')

        return report

    def _create_service_request(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create ServiceRequest resource with comprehensive test/procedure coding"""
        service_request = {
            'resourceType': 'ServiceRequest',
            'id': self._generate_clinical_id(data, 'service'),
            'status': self._normalize_service_request_status(data.get('status', 'active')),
            'intent': data.get('intent', 'order')
        }

        # Patient reference (required)
        service_request['subject'] = self._create_patient_reference(data)

        # Service coding with LOINC/SNOMED priority
        service_request['code'] = self._create_service_request_code(data)

        # Category determination
        service_request['category'] = [self._determine_service_request_category(data, service_request['code'])]

        # Priority/urgency
        if 'priority' in data or 'urgency' in data:
            service_request['priority'] = self._normalize_priority(data.get('priority') or data.get('urgency', 'routine'))

        # Requester
        if 'requester' in data or 'practitioner_id' in data or 'ordering_provider' in data:
            service_request['requester'] = self._create_practitioner_reference(data, field_names=['requester', 'practitioner_id', 'ordering_provider'])

        # Occurrence timing
        if 'occurrence_date' in data:
            service_request['occurrenceDateTime'] = data['occurrence_date']
        elif 'scheduled_date' in data:
            service_request['occurrenceDateTime'] = data['scheduled_date']

        # Authored date
        service_request['authoredOn'] = data.get('authored_on', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

        # Reason/indication
        if 'reason' in data or 'indication' in data:
            reason_text = data.get('reason') or data.get('indication')
            service_request['reasonCode'] = [self.create_codeable_concept_from_text(reason_text)]

        # Encounter reference
        if 'encounter_ref' in data or 'encounter_id' in data:
            service_request['encounter'] = self._create_encounter_reference(data)

        # Note/instructions
        if 'note' in data or 'instructions' in data:
            note_text = data.get('note') or data.get('instructions')
            service_request['note'] = [{'text': str(note_text)}]

        # Add clinical metadata
        self._add_clinical_metadata(service_request, request_id, 'service_request')

        return service_request

    def _create_condition(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create Condition resource with ICD-10/SNOMED coding"""
        condition = {
            'resourceType': 'Condition',
            'id': self._generate_clinical_id(data, 'condition')
        }

        # Patient reference (required)
        condition['subject'] = self._create_patient_reference(data)

        # Condition coding with ICD-10/SNOMED priority
        condition['code'] = self._create_condition_code(data)

        # Clinical status
        condition['clinicalStatus'] = self._create_clinical_status(data.get('clinical_status', 'active'))

        # Verification status
        condition['verificationStatus'] = self._create_verification_status(data.get('verification_status', 'confirmed'))

        # Severity
        if 'severity' in data:
            condition['severity'] = self._create_severity_code(data['severity'])

        # Onset
        if 'onset_date' in data:
            condition['onsetDateTime'] = data['onset_date']
        elif 'onset_age' in data:
            condition['onsetAge'] = self._create_age_quantity(data['onset_age'])
        elif 'onset_period' in data:
            condition['onsetPeriod'] = data['onset_period']

        # Recorded date
        condition['recordedDate'] = data.get('recorded_date', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

        # Asserter
        if 'asserter' in data or 'practitioner_id' in data:
            condition['asserter'] = self._create_practitioner_reference(data, field_names=['asserter', 'practitioner_id'])

        # Encounter reference
        if 'encounter_ref' in data or 'encounter_id' in data:
            condition['encounter'] = self._create_encounter_reference(data)

        # Note
        if 'note' in data:
            condition['note'] = [{'text': str(data['note'])}]

        # Add clinical metadata
        self._add_clinical_metadata(condition, request_id, 'condition')

        return condition

    def _create_allergy_intolerance(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create AllergyIntolerance resource with comprehensive substance coding"""
        allergy = {
            'resourceType': 'AllergyIntolerance',
            'id': self._generate_clinical_id(data, 'allergy')
        }

        # Patient reference (required)
        allergy['patient'] = self._create_patient_reference(data)

        # Substance coding with RxNorm/SNOMED priority
        allergy['code'] = self._create_allergy_code(data)

        # Category determination
        if 'category' in data:
            allergy['category'] = [data['category']]
        else:
            allergy['category'] = [self._determine_allergy_category(data, allergy['code'])]

        # Type (allergy vs intolerance)
        allergy['type'] = data.get('type', 'allergy')

        # Criticality
        if 'criticality' in data:
            allergy['criticality'] = self._normalize_criticality(data['criticality'])

        # Clinical status
        allergy['clinicalStatus'] = self._create_clinical_status(data.get('clinical_status', 'active'))

        # Verification status
        allergy['verificationStatus'] = self._create_verification_status(data.get('verification_status', 'confirmed'))

        # Onset
        if 'onset_date' in data:
            allergy['onsetDateTime'] = data['onset_date']
        elif 'onset_age' in data:
            allergy['onsetAge'] = self._create_age_quantity(data['onset_age'])

        # Recorded date
        allergy['recordedDate'] = data.get('recorded_date', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

        # Recorder
        if 'recorder' in data or 'practitioner_id' in data:
            allergy['recorder'] = self._create_practitioner_reference(data, field_names=['recorder', 'practitioner_id'])

        # Asserter
        if 'asserter' in data:
            allergy['asserter'] = self._create_practitioner_reference(data, field_names=['asserter'])

        # Reactions
        if 'reactions' in data:
            allergy['reaction'] = self._process_allergy_reactions(data['reactions'])

        # Note
        if 'note' in data:
            allergy['note'] = [{'text': str(data['note'])}]

        # Encounter reference
        if 'encounter_ref' in data or 'encounter_id' in data:
            allergy['encounter'] = self._create_encounter_reference(data)

        # Add clinical metadata
        self._add_clinical_metadata(allergy, request_id, 'allergy_intolerance')

        return allergy

    def _create_risk_assessment(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a FHIR R4 RiskAssessment resource.

        RiskAssessment structure includes:
        - status: registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown (required)
        - subject: Patient reference (required)
        - method: Mechanism used for assessment
        - code: Type of assessment
        - encounter: Where assessment was performed
        - occurrenceDateTime/occurrencePeriod: When was assessment made
        - condition: Condition assessed
        - performer: Who did assessment
        - reasonCode/reasonReference: Why assessment was performed
        - basis: Information used as basis (Observation, Condition references)
        - prediction: Outcome predicted with probability/qualitative risk/when
        - mitigation: How to reduce the risk
        - note: Comments about the risk assessment
        """
        # Generate unique ID
        risk_id = data.get('identifier', f"risk-assessment-{uuid.uuid4().hex[:8]}")

        # Normalize status
        status = self._normalize_risk_assessment_status(data.get('status', 'final'))

        # Build basic RiskAssessment structure
        risk_assessment = {
            'resourceType': 'RiskAssessment',
            'id': risk_id,
            'status': status,
            'subject': {
                'reference': f"Patient/{data.get('patient_id', data.get('patient_ref', ''))}"
            }
        }

        # Add method (evaluation mechanism)
        if 'method' in data:
            method_data = data['method']
            if isinstance(method_data, dict):
                risk_assessment['method'] = method_data
            else:
                risk_assessment['method'] = {
                    'text': str(method_data)
                }

        # Add code (type of risk assessment)
        if 'code' in data:
            code_data = data['code']
            if isinstance(code_data, dict):
                risk_assessment['code'] = code_data
            else:
                risk_assessment['code'] = {
                    'text': str(code_data)
                }

        # Add encounter reference
        if 'encounter' in data or 'encounter_id' in data:
            encounter_ref = data.get('encounter', data.get('encounter_id'))
            if isinstance(encounter_ref, dict) and 'reference' in encounter_ref:
                risk_assessment['encounter'] = encounter_ref
            else:
                ref_str = str(encounter_ref)
                if '/' not in ref_str:
                    ref_str = f"Encounter/{ref_str}"
                risk_assessment['encounter'] = {'reference': ref_str}

        # Add occurrence (when assessment was made)
        if 'occurrence_datetime' in data or 'occurrenceDateTime' in data:
            risk_assessment['occurrenceDateTime'] = data.get('occurrence_datetime', data.get('occurrenceDateTime'))
        elif 'occurrence_period' in data or 'occurrencePeriod' in data:
            period_data = data.get('occurrence_period', data.get('occurrencePeriod'))
            risk_assessment['occurrencePeriod'] = {}
            if 'start' in period_data:
                risk_assessment['occurrencePeriod']['start'] = period_data['start']
            if 'end' in period_data:
                risk_assessment['occurrencePeriod']['end'] = period_data['end']

        # Add condition assessed
        if 'condition' in data:
            condition_ref = data['condition']
            if isinstance(condition_ref, dict) and 'reference' in condition_ref:
                risk_assessment['condition'] = condition_ref
            else:
                ref_str = str(condition_ref)
                if '/' not in ref_str:
                    ref_str = f"Condition/{ref_str}"
                risk_assessment['condition'] = {'reference': ref_str}

        # Add performer
        if 'performer' in data:
            performer = data['performer']
            if isinstance(performer, dict) and 'reference' in performer:
                risk_assessment['performer'] = performer
            else:
                ref_str = str(performer)
                if '/' not in ref_str:
                    ref_str = f"Practitioner/{ref_str}"
                risk_assessment['performer'] = {'reference': ref_str}

        # Add reason code
        if 'reason_code' in data or 'reasonCode' in data:
            reason_codes = data.get('reason_code', data.get('reasonCode'))
            if not isinstance(reason_codes, list):
                reason_codes = [reason_codes]
            risk_assessment['reasonCode'] = []
            for reason in reason_codes:
                if isinstance(reason, dict):
                    risk_assessment['reasonCode'].append(reason)
                else:
                    risk_assessment['reasonCode'].append({'text': str(reason)})

        # Add reason reference
        if 'reason_reference' in data or 'reasonReference' in data:
            reason_refs = data.get('reason_reference', data.get('reasonReference'))
            if not isinstance(reason_refs, list):
                reason_refs = [reason_refs]
            risk_assessment['reasonReference'] = []
            for ref in reason_refs:
                if isinstance(ref, dict) and 'reference' in ref:
                    risk_assessment['reasonReference'].append(ref)
                else:
                    risk_assessment['reasonReference'].append({'reference': str(ref)})

        # Add basis (observations, conditions used for assessment)
        if 'basis' in data:
            basis_refs = data['basis'] if isinstance(data['basis'], list) else [data['basis']]
            risk_assessment['basis'] = []
            for basis in basis_refs:
                if isinstance(basis, dict) and 'reference' in basis:
                    risk_assessment['basis'].append(basis)
                else:
                    risk_assessment['basis'].append({'reference': str(basis)})

        # Add prediction (outcome with probability and timeframe)
        if 'prediction' in data:
            predictions = data['prediction'] if isinstance(data['prediction'], list) else [data['prediction']]
            risk_assessment['prediction'] = []
            for pred in predictions:
                prediction_entry = self._create_risk_prediction(pred)
                if prediction_entry:
                    risk_assessment['prediction'].append(prediction_entry)

        # Add mitigation
        if 'mitigation' in data:
            risk_assessment['mitigation'] = str(data['mitigation'])

        # Add notes
        if 'note' in data or 'notes' in data:
            notes = data.get('note', data.get('notes'))
            if isinstance(notes, str):
                risk_assessment['note'] = [{
                    'text': notes,
                    'time': datetime.utcnow().isoformat() + 'Z'
                }]
            elif isinstance(notes, list):
                risk_assessment['note'] = []
                for note_text in notes:
                    if isinstance(note_text, dict):
                        risk_assessment['note'].append(note_text)
                    else:
                        risk_assessment['note'].append({
                            'text': str(note_text),
                            'time': datetime.utcnow().isoformat() + 'Z'
                        })

        # Add clinical metadata
        self._add_clinical_metadata(risk_assessment, request_id, 'risk_assessment')

        return risk_assessment

    def _normalize_risk_assessment_status(self, status: str) -> str:
        """Normalize input status to FHIR RiskAssessment status"""
        status_lower = status.lower()

        # Valid FHIR statuses
        valid_statuses = {
            'registered', 'preliminary', 'final', 'amended',
            'corrected', 'cancelled', 'entered-in-error', 'unknown'
        }

        if status_lower in valid_statuses:
            return status_lower

        # Map common aliases
        status_mapping = {
            'draft': 'preliminary',
            'completed': 'final',
            'active': 'final',
            'error': 'entered-in-error'
        }

        return status_mapping.get(status_lower, 'final')

    def _create_risk_prediction(self, prediction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a risk assessment prediction entry"""
        if not isinstance(prediction_data, dict):
            return None

        prediction = {}

        # Add outcome (what could happen)
        if 'outcome' in prediction_data:
            outcome = prediction_data['outcome']
            if isinstance(outcome, dict):
                prediction['outcome'] = outcome
            else:
                prediction['outcome'] = {
                    'text': str(outcome)
                }

        # Add probability (as decimal or range)
        if 'probability_decimal' in prediction_data or 'probabilityDecimal' in prediction_data:
            prediction['probabilityDecimal'] = prediction_data.get('probability_decimal', prediction_data.get('probabilityDecimal'))
        elif 'probability_range' in prediction_data or 'probabilityRange' in prediction_data:
            prob_range = prediction_data.get('probability_range', prediction_data.get('probabilityRange'))
            prediction['probabilityRange'] = {}
            if 'low' in prob_range:
                prediction['probabilityRange']['low'] = prob_range['low']
            if 'high' in prob_range:
                prediction['probabilityRange']['high'] = prob_range['high']

        # Add qualitative risk (low, moderate, high)
        if 'qualitative_risk' in prediction_data or 'qualitativeRisk' in prediction_data:
            qual_risk = prediction_data.get('qualitative_risk', prediction_data.get('qualitativeRisk'))
            if isinstance(qual_risk, dict):
                prediction['qualitativeRisk'] = qual_risk
            else:
                # Map to standard coding
                risk_level = str(qual_risk).lower()
                risk_display_map = {
                    'low': 'Low Risk',
                    'moderate': 'Moderate Risk',
                    'medium': 'Moderate Risk',
                    'high': 'High Risk'
                }
                display = risk_display_map.get(risk_level, risk_level.title())
                prediction['qualitativeRisk'] = {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/risk-probability',
                        'code': risk_level if risk_level in ['low', 'moderate', 'high'] else 'moderate',
                        'display': display
                    }],
                    'text': display
                }

        # Add relative risk
        if 'relative_risk' in prediction_data or 'relativeRisk' in prediction_data:
            prediction['relativeRisk'] = prediction_data.get('relative_risk', prediction_data.get('relativeRisk'))

        # Add when (period or range)
        if 'when_period' in prediction_data or 'whenPeriod' in prediction_data:
            when_period = prediction_data.get('when_period', prediction_data.get('whenPeriod'))
            prediction['whenPeriod'] = {}
            if 'start' in when_period:
                prediction['whenPeriod']['start'] = when_period['start']
            if 'end' in when_period:
                prediction['whenPeriod']['end'] = when_period['end']
        elif 'when_range' in prediction_data or 'whenRange' in prediction_data:
            when_range = prediction_data.get('when_range', prediction_data.get('whenRange'))
            prediction['whenRange'] = {}
            if 'low' in when_range:
                prediction['whenRange']['low'] = when_range['low']
            if 'high' in when_range:
                prediction['whenRange']['high'] = when_range['high']

        # Add rationale
        if 'rationale' in prediction_data:
            prediction['rationale'] = str(prediction_data['rationale'])

        return prediction if prediction else None

    def _create_imaging_study(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a FHIR R4 ImagingStudy resource.

        ImagingStudy structure includes:
        - status: registered | available | cancelled | entered-in-error | unknown (required)
        - subject: Patient reference (required)
        - series: Array of series, each with uid and modality (required if present)
        - encounter: Where imaging was performed
        - started: When study began
        - basedOn: ServiceRequest/CarePlan references
        - referrer: Referring physician
        - endpoint: Access endpoints for images
        - numberOfSeries: Number of series in study
        - numberOfInstances: Total number of instances
        - procedureReference/procedureCode: Procedure performed
        - reasonCode/reasonReference: Why imaging was ordered
        - description: Institution-generated description
        - location: Where study was performed
        """
        # Generate unique ID
        study_id = data.get('identifier', f"imaging-study-{uuid.uuid4().hex[:8]}")

        # Normalize status
        status = self._normalize_imaging_study_status(data.get('status', 'available'))

        # Build basic ImagingStudy structure
        imaging_study = {
            'resourceType': 'ImagingStudy',
            'id': study_id,
            'status': status,
            'subject': {
                'reference': f"Patient/{data.get('patient_id', data.get('patient_ref', ''))}"
            }
        }

        # Add encounter reference
        if 'encounter' in data or 'encounter_id' in data:
            encounter_ref = data.get('encounter', data.get('encounter_id'))
            if isinstance(encounter_ref, dict) and 'reference' in encounter_ref:
                imaging_study['encounter'] = encounter_ref
            else:
                ref_str = str(encounter_ref)
                if '/' not in ref_str:
                    ref_str = f"Encounter/{ref_str}"
                imaging_study['encounter'] = {'reference': ref_str}

        # Add started datetime
        if 'started' in data:
            imaging_study['started'] = data['started']
        elif status == 'available':
            imaging_study['started'] = datetime.utcnow().isoformat() + 'Z'

        # Add basedOn (ServiceRequest, CarePlan references)
        if 'based_on' in data or 'basedOn' in data:
            based_on_refs = data.get('based_on', data.get('basedOn'))
            if not isinstance(based_on_refs, list):
                based_on_refs = [based_on_refs]
            imaging_study['basedOn'] = []
            for ref in based_on_refs:
                if isinstance(ref, dict) and 'reference' in ref:
                    imaging_study['basedOn'].append(ref)
                else:
                    imaging_study['basedOn'].append({'reference': str(ref)})

        # Add referrer
        if 'referrer' in data:
            referrer = data['referrer']
            if isinstance(referrer, dict) and 'reference' in referrer:
                imaging_study['referrer'] = referrer
            else:
                ref_str = str(referrer)
                if '/' not in ref_str:
                    ref_str = f"Practitioner/{ref_str}"
                imaging_study['referrer'] = {'reference': ref_str}

        # Add endpoint (image access)
        if 'endpoint' in data:
            endpoints = data['endpoint'] if isinstance(data['endpoint'], list) else [data['endpoint']]
            imaging_study['endpoint'] = []
            for ep in endpoints:
                if isinstance(ep, dict) and 'reference' in ep:
                    imaging_study['endpoint'].append(ep)
                else:
                    ref_str = str(ep)
                    if '/' not in ref_str:
                        ref_str = f"Endpoint/{ref_str}"
                    imaging_study['endpoint'].append({'reference': ref_str})

        # Add series (CRITICAL: required structure)
        if 'series' in data:
            series_list = data['series'] if isinstance(data['series'], list) else [data['series']]
            imaging_study['series'] = []
            for series_data in series_list:
                series_entry = self._create_imaging_series(series_data)
                if series_entry:
                    imaging_study['series'].append(series_entry)

            # Count series and instances
            if imaging_study['series']:
                imaging_study['numberOfSeries'] = len(imaging_study['series'])
                total_instances = sum(s.get('numberOfInstances', 0) for s in imaging_study['series'])
                if total_instances > 0:
                    imaging_study['numberOfInstances'] = total_instances

        # Add procedure reference
        if 'procedure_reference' in data or 'procedureReference' in data:
            proc_ref = data.get('procedure_reference', data.get('procedureReference'))
            if isinstance(proc_ref, list):
                imaging_study['procedureReference'] = []
                for ref in proc_ref:
                    if isinstance(ref, dict) and 'reference' in ref:
                        imaging_study['procedureReference'].append(ref)
                    else:
                        imaging_study['procedureReference'].append({'reference': str(ref)})
            else:
                if isinstance(proc_ref, dict) and 'reference' in proc_ref:
                    imaging_study['procedureReference'] = [proc_ref]
                else:
                    imaging_study['procedureReference'] = [{'reference': str(proc_ref)}]

        # Add procedure code
        if 'procedure_code' in data or 'procedureCode' in data:
            proc_code = data.get('procedure_code', data.get('procedureCode'))
            if isinstance(proc_code, list):
                imaging_study['procedureCode'] = proc_code
            elif isinstance(proc_code, dict):
                imaging_study['procedureCode'] = [proc_code]
            else:
                imaging_study['procedureCode'] = [{'text': str(proc_code)}]

        # Add reason code
        if 'reason_code' in data or 'reasonCode' in data:
            reason_codes = data.get('reason_code', data.get('reasonCode'))
            if not isinstance(reason_codes, list):
                reason_codes = [reason_codes]
            imaging_study['reasonCode'] = []
            for reason in reason_codes:
                if isinstance(reason, dict):
                    imaging_study['reasonCode'].append(reason)
                else:
                    imaging_study['reasonCode'].append({'text': str(reason)})

        # Add reason reference
        if 'reason_reference' in data or 'reasonReference' in data:
            reason_refs = data.get('reason_reference', data.get('reasonReference'))
            if not isinstance(reason_refs, list):
                reason_refs = [reason_refs]
            imaging_study['reasonReference'] = []
            for ref in reason_refs:
                if isinstance(ref, dict) and 'reference' in ref:
                    imaging_study['reasonReference'].append(ref)
                else:
                    imaging_study['reasonReference'].append({'reference': str(ref)})

        # Add description
        if 'description' in data:
            imaging_study['description'] = str(data['description'])

        # Add location
        if 'location' in data:
            location = data['location']
            if isinstance(location, dict) and 'reference' in location:
                imaging_study['location'] = location
            else:
                ref_str = str(location)
                if '/' not in ref_str:
                    ref_str = f"Location/{ref_str}"
                imaging_study['location'] = {'reference': ref_str}

        # Add clinical metadata
        self._add_clinical_metadata(imaging_study, request_id, 'imaging_study')

        return imaging_study

    def _normalize_imaging_study_status(self, status: str) -> str:
        """Normalize input status to FHIR ImagingStudy status"""
        status_lower = status.lower()

        # Valid FHIR statuses
        valid_statuses = {'registered', 'available', 'cancelled', 'entered-in-error', 'unknown'}

        if status_lower in valid_statuses:
            return status_lower

        # Map common aliases
        status_mapping = {
            'completed': 'available',
            'active': 'available',
            'final': 'available',
            'preliminary': 'registered',
            'error': 'entered-in-error'
        }

        return status_mapping.get(status_lower, 'available')

    def _create_imaging_series(self, series_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an imaging series entry"""
        if not isinstance(series_data, dict):
            return None

        # UID is required for series
        if 'uid' not in series_data:
            series_data['uid'] = f"2.25.{uuid.uuid4().int}"

        series = {
            'uid': series_data['uid']
        }

        # Modality is required (DICOM modality code)
        if 'modality' in series_data:
            modality = series_data['modality']
            if isinstance(modality, dict):
                series['modality'] = modality
            else:
                # Common modality codes
                modality_map = {
                    'ct': ('CT', 'Computed Tomography'),
                    'mr': ('MR', 'Magnetic Resonance'),
                    'xr': ('CR', 'Computed Radiography'),
                    'us': ('US', 'Ultrasound'),
                    'dx': ('DX', 'Digital Radiography'),
                    'mg': ('MG', 'Mammography'),
                    'pt': ('PT', 'Positron Emission Tomography'),
                    'nm': ('NM', 'Nuclear Medicine')
                }
                mod_lower = str(modality).lower()
                if mod_lower in modality_map:
                    code, display = modality_map[mod_lower]
                    series['modality'] = {
                        'system': 'http://dicom.nema.org/resources/ontology/DCM',
                        'code': code,
                        'display': display
                    }
                else:
                    series['modality'] = {'text': str(modality)}
        else:
            # Default modality if not specified
            series['modality'] = {'text': 'Other'}

        # Add optional fields
        if 'number' in series_data:
            series['number'] = series_data['number']

        if 'description' in series_data:
            series['description'] = str(series_data['description'])

        if 'number_of_instances' in series_data or 'numberOfInstances' in series_data:
            series['numberOfInstances'] = series_data.get('number_of_instances', series_data.get('numberOfInstances'))

        if 'body_site' in series_data or 'bodySite' in series_data:
            body_site = series_data.get('body_site', series_data.get('bodySite'))
            if isinstance(body_site, dict):
                series['bodySite'] = body_site
            else:
                series['bodySite'] = {'text': str(body_site)}

        # Add instances if provided
        if 'instance' in series_data:
            instances = series_data['instance'] if isinstance(series_data['instance'], list) else [series_data['instance']]
            series['instance'] = []
            for inst in instances:
                if isinstance(inst, dict) and 'uid' in inst:
                    series['instance'].append(inst)

        return series

    # Initialize clinical coding mappings
    def _init_vital_signs_mapping(self):
        """Initialize LOINC codes for vital signs and monitoring"""
        self._vital_signs_loinc = {
            # Basic vital signs
            'blood_pressure': {'systolic': '8480-6', 'diastolic': '8462-4', 'panel': '85354-9'},
            'heart_rate': '8867-4',
            'respiratory_rate': '9279-1',
            'temperature': '8310-5',
            'oxygen_saturation': '2708-6',
            'pulse': '8867-4',
            'weight': '29463-7',
            'height': '8302-2',
            'bmi': '39156-5',

            # Infusion monitoring
            'infusion_rate': '33747-0',
            'iv_site_assessment': '8693-6',
            'fluid_balance': '19994-3',
            'pump_alarm': '33748-8',

            # Pain assessment
            'pain_scale': '72133-2',
            'pain_location': '72134-0',

            # Advanced monitoring
            'level_of_consciousness': '80288-4',
            'glasgow_coma_scale': '9269-2',
            'neurological_assessment': '72133-2'
        }

    def _init_lab_test_mapping(self):
        """Initialize LOINC codes for laboratory tests"""
        self._lab_test_loinc = {
            # Basic chemistry
            'cbc': '58410-2',
            'cmp': '24323-8',  # Comprehensive metabolic panel
            'bmp': '51990-0',  # Basic metabolic panel
            'glucose': '2345-7',
            'creatinine': '2160-0',
            'bun': '3094-0',
            'sodium': '2951-2',
            'potassium': '2823-3',
            'chloride': '2075-0',

            # Cardiac markers
            'troponin': '6598-7',
            'bnp': '33762-6',
            'ck_mb': '13969-1',

            # Endocrine
            'hba1c': '4548-4',
            'tsh': '3016-3',
            'insulin': '20448-7',

            # Coagulation
            'pt': '5902-2',
            'ptt': '14979-9',
            'inr': '34714-6',

            # Inflammatory markers
            'crp': '1988-5',
            'esr': '30341-2',

            # Specialty tests
            'psa': '2857-1',
            'cea': '2039-6'
        }

    def _init_diagnostic_procedure_mapping(self):
        """Initialize SNOMED CT codes for diagnostic procedures"""
        self._diagnostic_procedures_snomed = {
            # Imaging
            'chest_xray': '399208008',
            'ct_scan': '77477000',
            'mri': '113091000',
            'ultrasound': '16310003',
            'mammography': '71651007',

            # Cardiology
            'ecg': '29303009',
            'echocardiogram': '40701008',
            'stress_test': '18501008',
            'cardiac_catheterization': '41976001',

            # Gastroenterology
            'colonoscopy': '73761001',
            'upper_endoscopy': '1919006',
            'ct_abdomen': '169070008',

            # Pulmonary
            'pulmonary_function_test': '23426006',
            'chest_ct': '169069000',

            # Neurology
            'eeg': '54550000',
            'lumbar_puncture': '277762005'
        }

    def _init_condition_mapping(self):
        """Initialize ICD-10 and SNOMED CT codes for conditions"""
        self._condition_codes = {
            # Common conditions with ICD-10 CM codes
            'diabetes': {'icd10': 'E11.9', 'snomed': '44054006'},
            'hypertension': {'icd10': 'I10', 'snomed': '38341003'},
            'pneumonia': {'icd10': 'J18.9', 'snomed': '233604007'},
            'copd': {'icd10': 'J44.1', 'snomed': '13645005'},
            'heart_failure': {'icd10': 'I50.9', 'snomed': '84114007'},
            'atrial_fibrillation': {'icd10': 'I48.91', 'snomed': '49436004'},
            'acute_mi': {'icd10': 'I21.9', 'snomed': '57054005'},
            'stroke': {'icd10': 'I63.9', 'snomed': '230690007'}
        }

    def _init_allergy_mapping(self):
        """Initialize substance coding for allergies"""
        self._allergy_substances = {
            # Categories with SNOMED CT codes
            'medication': {'snomed': '373873005', 'category': 'medication'},
            'food': {'snomed': '255620007', 'category': 'food'},
            'environment': {'snomed': '111088007', 'category': 'environment'},

            # Common allergens
            'penicillin': {'rxnorm': '7980', 'snomed': '373270004', 'category': 'medication'},
            'peanuts': {'snomed': '256349002', 'category': 'food'},
            'shellfish': {'snomed': '44027008', 'category': 'food'},
            'latex': {'snomed': '111088007', 'category': 'environment'},
            'pollen': {'snomed': '256277009', 'category': 'environment'}
        }

    # Helper methods for clinical resource creation
    def _generate_clinical_id(self, data: Dict[str, Any], resource_subtype: str) -> str:
        """Generate unique clinical resource ID (FHIR compliant)"""
        if 'id' in data:
            return str(data['id'])

        # Generate short unique ID
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8]

        # Use clinical term if available
        if 'name' in data or 'code' in data or 'text' in data:
            term = data.get('name') or data.get('code') or data.get('text')
            clean_term = re.sub(r'[^a-zA-Z0-9]', '', str(term).lower())[:12]
            return f"clinical-{resource_subtype}-{clean_term}-{short_uuid}"

        return f"clinical-{resource_subtype}-{short_uuid}"

    def _create_patient_reference(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create patient reference from various field patterns"""
        if 'patient_ref' in data:
            return {'reference': data['patient_ref']}
        elif 'patient_id' in data:
            return {'reference': f"Patient/{data['patient_id']}"}
        elif 'subject' in data:
            return data['subject'] if isinstance(data['subject'], dict) else {'reference': data['subject']}
        else:
            raise ValueError("Patient reference is required for clinical resources")

    def _create_encounter_reference(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create encounter reference from various field patterns"""
        if 'encounter_ref' in data:
            return {'reference': data['encounter_ref']}
        elif 'encounter_id' in data:
            return {'reference': f"Encounter/{data['encounter_id']}"}
        elif 'encounter' in data:
            return data['encounter'] if isinstance(data['encounter'], dict) else {'reference': data['encounter']}

    def _create_practitioner_reference(self, data: Dict[str, Any], field_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create practitioner reference from various field patterns"""
        if not field_names:
            field_names = ['performer', 'practitioner_id', 'provider_id']

        for field in field_names:
            if field in data:
                ref_value = data[field]
                if isinstance(ref_value, dict):
                    return ref_value
                elif ref_value.startswith('Practitioner/'):
                    return {'reference': ref_value}
                else:
                    return {'reference': f"Practitioner/{ref_value}"}

        return None

    def _create_device_reference(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create device reference from various field patterns"""
        if 'device_ref' in data:
            return {'reference': data['device_ref']}
        elif 'device_id' in data:
            return {'reference': f"Device/{data['device_id']}"}
        elif 'device' in data:
            return data['device'] if isinstance(data['device'], dict) else {'reference': data['device']}

    def _update_clinical_metrics(self, resource_type: str, duration_ms: float, success: bool):
        """Update clinical factory performance metrics"""
        if resource_type not in self._clinical_metrics:
            self._clinical_metrics[resource_type] = {
                'created': 0, 'failed': 0, 'total_time_ms': 0.0, 'avg_time_ms': 0.0
            }

        metrics = self._clinical_metrics[resource_type]
        if success:
            metrics['created'] += 1
        else:
            metrics['failed'] += 1

        metrics['total_time_ms'] += duration_ms
        total_requests = metrics['created'] + metrics['failed']
        metrics['avg_time_ms'] = metrics['total_time_ms'] / total_requests if total_requests > 0 else 0.0

    def _add_clinical_metadata(self, resource: Dict[str, Any], request_id: Optional[str], resource_subtype: str):
        """Add clinical-specific metadata to resource"""
        resource['meta'] = {
            'profile': [f'http://hl7.org/fhir/StructureDefinition/{resource["resourceType"]}'],
            'lastUpdated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'source': f'NL-FHIR-Clinical-{resource_subtype.title()}',
            'factory': 'ClinicalResourceFactory',
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }

        if request_id:
            resource['meta']['request_id'] = request_id

    # Status normalization methods
    def _normalize_observation_status(self, status: str) -> str:
        """Normalize observation status to FHIR values"""
        status_map = {
            'final': 'final',
            'preliminary': 'preliminary',
            'registered': 'registered',
            'amended': 'amended',
            'corrected': 'corrected',
            'cancelled': 'cancelled',
            'unknown': 'unknown'
        }
        return status_map.get(str(status).lower(), 'final')

    def _normalize_report_status(self, status: str) -> str:
        """Normalize diagnostic report status to FHIR values"""
        status_map = {
            'final': 'final',
            'preliminary': 'preliminary',
            'registered': 'registered',
            'partial': 'partial',
            'amended': 'amended',
            'corrected': 'corrected',
            'cancelled': 'cancelled',
            'unknown': 'unknown'
        }
        return status_map.get(str(status).lower(), 'final')

    def _normalize_service_request_status(self, status: str) -> str:
        """Normalize service request status to FHIR values"""
        status_map = {
            'active': 'active',
            'on-hold': 'on-hold',
            'revoked': 'revoked',
            'completed': 'completed',
            'entered-in-error': 'entered-in-error',
            'draft': 'draft'
        }
        return status_map.get(str(status).lower(), 'active')

    def _normalize_priority(self, priority: str) -> str:
        """Normalize priority to FHIR values"""
        priority_map = {
            'routine': 'routine',
            'urgent': 'urgent',
            'asap': 'asap',
            'stat': 'stat',
            'emergency': 'urgent'
        }
        return priority_map.get(str(priority).lower(), 'routine')

    def _normalize_criticality(self, criticality: str) -> str:
        """Normalize allergy criticality to FHIR values"""
        criticality_map = {
            'low': 'low',
            'high': 'high',
            'unable-to-assess': 'unable-to-assess',
            'unknown': 'unable-to-assess'
        }
        return criticality_map.get(str(criticality).lower(), 'low')

    # Implementation of complex clinical coding logic
    def _create_observation_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create observation code with LOINC priority"""
        if 'code' in data and isinstance(data['code'], dict):
            return data['code']

        # Extract observation identifier
        obs_name = (data.get('name') or data.get('code') or data.get('text', '')).lower().strip()

        # Look up LOINC code for vital signs
        for vital_sign, loinc_info in self._vital_signs_loinc.items():
            if vital_sign.replace('_', ' ') in obs_name or vital_sign in obs_name:
                display_name = vital_sign.replace('_', ' ').title()
                # Create text-based concept with LOINC reference for now
                return {
                    'text': display_name,
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': loinc_info if isinstance(loinc_info, str) else str(loinc_info.get('panel', '85354-9')),
                        'display': display_name
                    }]
                }

        # Look up LOINC code for lab tests
        for lab_test, loinc_code in self._lab_test_loinc.items():
            if lab_test.replace('_', ' ') in obs_name or lab_test in obs_name:
                display_name = lab_test.replace('_', ' ').upper()
                # Create text-based concept with LOINC reference for now
                return {
                    'text': display_name,
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': loinc_code,
                        'display': display_name
                    }]
                }

        # Fallback to text-only concept
        return {'text': data.get('name') or data.get('code') or data.get('text', 'Clinical observation')}

    def _determine_observation_category(self, data: Dict[str, Any], code: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine observation category based on observation type"""
        obs_name = (data.get('name') or data.get('code') or data.get('text', '')).lower()

        # Vital signs category
        vital_signs_keywords = ['blood_pressure', 'heart_rate', 'temperature', 'respiratory_rate', 'oxygen_saturation', 'pulse', 'weight', 'height', 'bmi']
        if any(keyword in obs_name or keyword.replace('_', ' ') in obs_name for keyword in vital_signs_keywords):
            return [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'vital-signs',
                    'display': 'Vital Signs'
                }]
            }]

        # Laboratory category
        lab_keywords = ['cbc', 'cmp', 'bmp', 'glucose', 'creatinine', 'troponin', 'hba1c', 'lab', 'blood', 'serum', 'plasma']
        if any(keyword in obs_name for keyword in lab_keywords):
            return [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'laboratory',
                    'display': 'Laboratory'
                }]
            }]

        # Imaging category
        imaging_keywords = ['xray', 'ct', 'mri', 'ultrasound', 'scan', 'imaging']
        if any(keyword in obs_name for keyword in imaging_keywords):
            return [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'imaging',
                    'display': 'Imaging'
                }]
            }]

        # Procedure category
        procedure_keywords = ['procedure', 'surgery', 'operation', 'intervention']
        if any(keyword in obs_name for keyword in procedure_keywords):
            return [{
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'procedure',
                    'display': 'Procedure'
                }]
            }]

        # Default to survey/assessment
        return [{
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                'code': 'survey',
                'display': 'Survey'
            }]
        }]

    def _add_observation_value(self, observation: Dict[str, Any], data: Dict[str, Any]):
        """Add observation value with appropriate FHIR data type"""
        if 'value_quantity' in data:
            observation['valueQuantity'] = {
                'value': float(data['value_quantity']),
                'unit': data.get('unit', ''),
                'system': 'http://unitsofmeasure.org',
                'code': data.get('unit_code', data.get('unit', ''))
            }
        elif 'value_string' in data:
            observation['valueString'] = str(data['value_string'])
        elif 'value_boolean' in data:
            observation['valueBoolean'] = bool(data['value_boolean'])
        elif 'value_integer' in data:
            observation['valueInteger'] = int(data['value_integer'])
        elif 'value_datetime' in data:
            observation['valueDateTime'] = data['value_datetime']
        elif 'value_codeable_concept' in data:
            observation['valueCodeableConcept'] = data['value_codeable_concept']
        elif 'value' in data:
            # Try to infer type from value
            value = data['value']
            try:
                # Try numeric first
                if '.' in str(value):
                    observation['valueQuantity'] = {
                        'value': float(value),
                        'unit': data.get('unit', ''),
                        'system': 'http://unitsofmeasure.org'
                    }
                else:
                    observation['valueInteger'] = int(value)
            except (ValueError, TypeError):
                # Fallback to string
                observation['valueString'] = str(value)

    def _process_observation_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process complex observation components (e.g., blood pressure systolic/diastolic)"""
        fhir_components = []

        for component in components:
            fhir_component = {
                'code': self._create_observation_code(component)
            }

            # Add component value
            if 'value' in component:
                self._add_observation_value(fhir_component, component)

            # Add interpretation if present
            if 'interpretation' in component:
                fhir_component['interpretation'] = [self._create_interpretation_code(component['interpretation'])]

            fhir_components.append(fhir_component)

        return fhir_components

    def _create_diagnostic_report_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create diagnostic report code with LOINC/SNOMED priority"""
        if 'code' in data and isinstance(data['code'], dict):
            return data['code']

        report_name = (data.get('name') or data.get('report_type') or data.get('text', '')).lower().strip()

        # Look up diagnostic procedure codes
        for procedure, snomed_code in self._diagnostic_procedures_snomed.items():
            if procedure.replace('_', ' ') in report_name or procedure in report_name:
                display_name = procedure.replace('_', ' ').title()
                return {'text': display_name, 'coding': [{'system': 'http://snomed.info/sct', 'code': snomed_code, 'display': display_name}]}

        # Common diagnostic report types
        if 'lab' in report_name or 'laboratory' in report_name:
            return {'text': 'Laboratory report', 'coding': [{'system': 'http://loinc.org', 'code': '11502-2', 'display': 'Laboratory report'}]}
        elif 'radiology' in report_name or 'imaging' in report_name:
            return {'text': 'Diagnostic imaging report', 'coding': [{'system': 'http://loinc.org', 'code': '18748-4', 'display': 'Diagnostic imaging report'}]}
        elif 'pathology' in report_name:
            return {'text': 'Comprehensive pathology report', 'coding': [{'system': 'http://loinc.org', 'code': '60567-5', 'display': 'Comprehensive pathology report'}]}

        # Fallback to text-only concept
        return {'text': data.get('name') or data.get('report_type', 'Diagnostic report')}

    def _determine_report_category(self, data: Dict[str, Any], code: Dict[str, Any]) -> Dict[str, Any]:
        """Determine diagnostic report category based on report type"""
        report_name = (data.get('name') or data.get('report_type') or data.get('text', '')).lower()

        # Imaging reports
        imaging_keywords = ['radiology', 'xray', 'x-ray', 'ct', 'mri', 'ultrasound', 'mammography', 'imaging']
        if any(keyword in report_name for keyword in imaging_keywords):
            return {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                    'code': 'RAD',
                    'display': 'Radiology'
                }]
            }

        # Laboratory reports
        lab_keywords = ['lab', 'laboratory', 'blood', 'serum', 'chemistry', 'hematology']
        if any(keyword in report_name for keyword in lab_keywords):
            return {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                    'code': 'LAB',
                    'display': 'Laboratory'
                }]
            }

        # Pathology reports
        pathology_keywords = ['pathology', 'biopsy', 'cytology', 'histology']
        if any(keyword in report_name for keyword in pathology_keywords):
            return {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                    'code': 'PAT',
                    'display': 'Pathology'
                }]
            }

        # Cardiology reports
        cardiology_keywords = ['ecg', 'echo', 'cardiac', 'cardiology', 'heart']
        if any(keyword in report_name for keyword in cardiology_keywords):
            return {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                    'code': 'CG',
                    'display': 'Cardiology'
                }]
            }

        # Default to other
        return {
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                'code': 'OTH',
                'display': 'Other'
            }]
        }

    def _create_service_request_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create service request code with LOINC/SNOMED priority"""
        if 'code' in data and isinstance(data['code'], dict):
            return data['code']

        service_name = (data.get('name') or data.get('service') or data.get('text', '')).lower().strip()

        # Look up LOINC codes for lab tests
        for lab_test, loinc_code in self._lab_test_loinc.items():
            if lab_test.replace('_', ' ') in service_name or lab_test in service_name:
                display_name = lab_test.replace('_', ' ').upper()
                return {'text': display_name, 'coding': [{'system': 'http://loinc.org', 'code': loinc_code, 'display': display_name}]}

        # Look up SNOMED codes for diagnostic procedures
        for procedure, snomed_code in self._diagnostic_procedures_snomed.items():
            if procedure.replace('_', ' ') in service_name or procedure in service_name:
                display_name = procedure.replace('_', ' ').title()
                return {'text': display_name, 'coding': [{'system': 'http://snomed.info/sct', 'code': snomed_code, 'display': display_name}]}

        # Common service request types
        if 'consultation' in service_name or 'referral' in service_name:
            return {'text': 'Consultation', 'coding': [{'system': 'http://snomed.info/sct', 'code': '11429006', 'display': 'Consultation'}]}
        elif 'imaging' in service_name:
            return {'text': 'Imaging', 'coding': [{'system': 'http://snomed.info/sct', 'code': '363679005', 'display': 'Imaging'}]}
        elif 'surgery' in service_name or 'procedure' in service_name:
            return {'text': 'Surgical procedure', 'coding': [{'system': 'http://snomed.info/sct', 'code': '387713003', 'display': 'Surgical procedure'}]}

        # Fallback to text-only concept
        return {'text': data.get('name') or data.get('service', 'Clinical service')}

    def _determine_service_request_category(self, data: Dict[str, Any], code: Dict[str, Any]) -> Dict[str, Any]:
        """Determine service request category based on service type"""
        service_name = (data.get('name') or data.get('service') or data.get('text', '')).lower()

        # Laboratory category
        lab_keywords = ['lab', 'blood', 'serum', 'chemistry', 'hematology', 'cbc', 'cmp', 'bmp']
        if any(keyword in service_name for keyword in lab_keywords):
            return {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '108252007',
                    'display': 'Laboratory procedure'
                }]
            }

        # Imaging category
        imaging_keywords = ['imaging', 'xray', 'ct', 'mri', 'ultrasound', 'scan']
        if any(keyword in service_name for keyword in imaging_keywords):
            return {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '363679005',
                    'display': 'Imaging'
                }]
            }

        # Consultation category
        consultation_keywords = ['consultation', 'referral', 'specialist', 'opinion']
        if any(keyword in service_name for keyword in consultation_keywords):
            return {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '11429006',
                    'display': 'Consultation'
                }]
            }

        # Surgical category
        surgical_keywords = ['surgery', 'operation', 'procedure', 'surgical']
        if any(keyword in service_name for keyword in surgical_keywords):
            return {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '387713003',
                    'display': 'Surgical procedure'
                }]
            }

        # Default to diagnostic procedure
        return {
            'coding': [{
                'system': 'http://snomed.info/sct',
                'code': '103693007',
                'display': 'Diagnostic procedure'
            }]
        }

    def _create_condition_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create condition code with ICD-10/SNOMED priority"""
        if 'code' in data and isinstance(data['code'], dict):
            return data['code']

        condition_name = (data.get('name') or data.get('condition') or data.get('text', '')).lower().strip()

        # Look up common conditions
        for condition, codes in self._condition_codes.items():
            if condition.replace('_', ' ') in condition_name or condition in condition_name:
                display_name = condition.replace('_', ' ').title()
                # Prefer ICD-10 with SNOMED as additional coding
                return {
                    'coding': [
                        {
                            'system': 'http://hl7.org/fhir/sid/icd-10-cm',
                            'code': codes['icd10'],
                            'display': display_name
                        },
                        {
                            'system': 'http://snomed.info/sct',
                            'code': codes['snomed'],
                            'display': display_name
                        }
                    ],
                    'text': display_name
                }

        # Check for specific ICD-10 code in data
        if 'icd10_code' in data:
            return {
                'coding': [{
                    'system': 'http://hl7.org/fhir/sid/icd-10-cm',
                    'code': data['icd10_code'],
                    'display': data.get('name', 'Clinical condition')
                }],
                'text': data.get('name', 'Clinical condition')
            }

        # Check for specific SNOMED code in data
        if 'snomed_code' in data:
            return {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': data['snomed_code'],
                    'display': data.get('name', 'Clinical condition')
                }],
                'text': data.get('name', 'Clinical condition')
            }

        # Fallback to text-only concept
        return {'text': data.get('name') or data.get('condition', 'Clinical condition')}

    def _create_allergy_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create allergy code with RxNorm/SNOMED priority"""
        if 'code' in data and isinstance(data['code'], dict):
            return data['code']

        substance_name = (data.get('name') or data.get('substance') or data.get('text', '')).lower().strip()

        # Look up common allergens
        for allergen, codes in self._allergy_substances.items():
            if allergen.replace('_', ' ') in substance_name or allergen in substance_name:
                display_name = allergen.replace('_', ' ').title()
                coding = []

                # Add RxNorm code if available (for medications)
                if 'rxnorm' in codes:
                    coding.append({
                        'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                        'code': codes['rxnorm'],
                        'display': display_name
                    })

                # Add SNOMED code
                if 'snomed' in codes:
                    coding.append({
                        'system': 'http://snomed.info/sct',
                        'code': codes['snomed'],
                        'display': display_name
                    })

                return {
                    'coding': coding,
                    'text': display_name
                }

        # Check for specific RxNorm code in data
        if 'rxnorm_code' in data:
            return {
                'coding': [{
                    'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                    'code': data['rxnorm_code'],
                    'display': data.get('name', 'Allergenic substance')
                }],
                'text': data.get('name', 'Allergenic substance')
            }

        # Check for specific SNOMED code in data
        if 'snomed_code' in data:
            return {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': data['snomed_code'],
                    'display': data.get('name', 'Allergenic substance')
                }],
                'text': data.get('name', 'Allergenic substance')
            }

        # Fallback to text-only concept
        return {'text': data.get('name') or data.get('substance', 'Allergenic substance')}

    def _determine_allergy_category(self, data: Dict[str, Any], code: Dict[str, Any]) -> str:
        """Determine allergy category based on substance type"""
        substance_name = (data.get('name') or data.get('substance') or data.get('text', '')).lower()

        # Check predefined allergen categories
        for allergen, info in self._allergy_substances.items():
            if allergen.replace('_', ' ') in substance_name or allergen in substance_name:
                return info['category']

        # Category keywords
        if any(keyword in substance_name for keyword in ['medication', 'drug', 'medicine', 'antibiotic', 'penicillin']):
            return 'medication'
        elif any(keyword in substance_name for keyword in ['food', 'peanut', 'shellfish', 'milk', 'egg', 'soy']):
            return 'food'
        elif any(keyword in substance_name for keyword in ['environment', 'pollen', 'dust', 'latex', 'animal']):
            return 'environment'
        elif any(keyword in substance_name for keyword in ['biologic', 'vaccine', 'serum']):
            return 'biologic'

        # Default to medication
        return 'medication'

    # Clinical status helpers
    def _create_clinical_status(self, status: str) -> Dict[str, Any]:
        """Create clinical status coding"""
        status_map = {
            'active': {'code': 'active', 'display': 'Active'},
            'inactive': {'code': 'inactive', 'display': 'Inactive'},
            'resolved': {'code': 'resolved', 'display': 'Resolved'}
        }
        status_info = status_map.get(status, status_map['active'])
        return {
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                'code': status_info['code'],
                'display': status_info['display']
            }]
        }

    def _create_verification_status(self, status: str) -> Dict[str, Any]:
        """Create verification status coding"""
        status_map = {
            'confirmed': {'code': 'confirmed', 'display': 'Confirmed'},
            'unconfirmed': {'code': 'unconfirmed', 'display': 'Unconfirmed'},
            'presumed': {'code': 'presumed', 'display': 'Presumed'},
            'refuted': {'code': 'refuted', 'display': 'Refuted'}
        }
        status_info = status_map.get(status, status_map['confirmed'])
        return {
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/condition-ver-status',
                'code': status_info['code'],
                'display': status_info['display']
            }]
        }

    def create_codeable_concept_from_text(self, text: str) -> Dict[str, Any]:
        """Create a text-only CodeableConcept"""
        return {'text': str(text)}

    # Additional implemented methods
    def _create_observation_references(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create observation references for diagnostic reports"""
        references = []

        # Handle observations field
        if 'observations' in data:
            for obs in data['observations']:
                if isinstance(obs, dict):
                    if 'reference' in obs:
                        references.append(obs)
                    elif 'id' in obs:
                        references.append({'reference': f"Observation/{obs['id']}"})
                else:
                    references.append({'reference': f"Observation/{obs}"})

        # Handle results field (alternative)
        if 'results' in data:
            for result in data['results']:
                if isinstance(result, dict):
                    if 'reference' in result:
                        references.append(result)
                    elif 'id' in result:
                        references.append({'reference': f"Observation/{result['id']}"})
                else:
                    references.append({'reference': f"Observation/{result}"})

        return references

    def _create_service_request_reference(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create service request reference"""
        if 'service_request' in data:
            service_request = data['service_request']
            if isinstance(service_request, dict):
                return service_request if 'reference' in service_request else {'reference': f"ServiceRequest/{service_request.get('id', 'unknown')}"}
            else:
                return {'reference': f"ServiceRequest/{service_request}"}
        elif 'order_ref' in data:
            return {'reference': data['order_ref']} if data['order_ref'].startswith('ServiceRequest/') else {'reference': f"ServiceRequest/{data['order_ref']}"}
        elif 'order_id' in data:
            return {'reference': f"ServiceRequest/{data['order_id']}"}

        return None

    def _create_interpretation_code(self, interpretation: str) -> Dict[str, Any]:
        """Create interpretation code with SNOMED/HL7 coding"""
        interpretation_lower = str(interpretation).lower().strip()

        # Standard HL7 interpretation codes
        interpretation_map = {
            'high': {'code': 'H', 'display': 'High', 'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation'},
            'low': {'code': 'L', 'display': 'Low', 'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation'},
            'normal': {'code': 'N', 'display': 'Normal', 'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation'},
            'abnormal': {'code': 'A', 'display': 'Abnormal', 'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation'},
            'critical': {'code': 'HH', 'display': 'Critical high', 'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation'},
            'panic': {'code': 'HH', 'display': 'Critical high', 'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation'}
        }

        for key, coding_info in interpretation_map.items():
            if key in interpretation_lower:
                return {
                    'coding': [{
                        'system': coding_info['system'],
                        'code': coding_info['code'],
                        'display': coding_info['display']
                    }],
                    'text': str(interpretation)
                }

        # Fallback to text-only
        return {'text': str(interpretation)}

    def _create_severity_code(self, severity: str) -> Dict[str, Any]:
        """Create severity code with SNOMED coding"""
        severity_lower = str(severity).lower().strip()

        # SNOMED CT severity codes
        severity_map = {
            'mild': {'snomed': '255604002', 'display': 'Mild'},
            'moderate': {'snomed': '6736007', 'display': 'Moderate'},
            'severe': {'snomed': '24484000', 'display': 'Severe'},
            'low': {'snomed': '255604002', 'display': 'Mild'},
            'high': {'snomed': '24484000', 'display': 'Severe'}
        }

        for key, coding_info in severity_map.items():
            if key in severity_lower:
                return {
                    'coding': [{
                        'system': 'http://snomed.info/sct',
                        'code': coding_info['snomed'],
                        'display': coding_info['display']
                    }],
                    'text': str(severity)
                }

        # Fallback to text-only
        return {'text': str(severity)}

    def _create_age_quantity(self, age: Any) -> Dict[str, Any]:
        """Create age quantity with proper UCUM units"""
        try:
            age_value = float(age)
            return {
                'value': age_value,
                'unit': 'years',
                'system': 'http://unitsofmeasure.org',
                'code': 'a'
            }
        except (ValueError, TypeError):
            # Handle string formats like "65 years", "2 months"
            age_str = str(age).lower().strip()

            if 'year' in age_str:
                age_value = float(''.join(filter(str.isdigit, age_str)))
                return {
                    'value': age_value,
                    'unit': 'years',
                    'system': 'http://unitsofmeasure.org',
                    'code': 'a'
                }
            elif 'month' in age_str:
                age_value = float(''.join(filter(str.isdigit, age_str)))
                return {
                    'value': age_value,
                    'unit': 'months',
                    'system': 'http://unitsofmeasure.org',
                    'code': 'mo'
                }
            elif 'day' in age_str:
                age_value = float(''.join(filter(str.isdigit, age_str)))
                return {
                    'value': age_value,
                    'unit': 'days',
                    'system': 'http://unitsofmeasure.org',
                    'code': 'd'
                }

            # Fallback
            return {
                'value': 0,
                'unit': 'years',
                'system': 'http://unitsofmeasure.org',
                'code': 'a'
            }

    def _process_allergy_reactions(self, reactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process allergy reactions with SNOMED coding"""
        fhir_reactions = []

        for reaction in reactions:
            fhir_reaction = {}

            # Substance (if different from main allergen)
            if 'substance' in reaction:
                fhir_reaction['substance'] = self._create_allergy_code(reaction)

            # Manifestations (symptoms)
            if 'manifestations' in reaction or 'symptoms' in reaction:
                manifestations = reaction.get('manifestations') or reaction.get('symptoms', [])
                fhir_reaction['manifestation'] = []

                for manifestation in manifestations:
                    if isinstance(manifestation, str):
                        # Common allergy manifestations with SNOMED codes
                        manifestation_codes = {
                            'rash': {'snomed': '271807003', 'display': 'Skin rash'},
                            'hives': {'snomed': '126485001', 'display': 'Urticaria'},
                            'itching': {'snomed': '418290006', 'display': 'Itching'},
                            'swelling': {'snomed': '267038008', 'display': 'Edema'},
                            'anaphylaxis': {'snomed': '39579001', 'display': 'Anaphylaxis'},
                            'shortness of breath': {'snomed': '267036007', 'display': 'Dyspnea'}
                        }

                        found_code = None
                        for symptom, coding_info in manifestation_codes.items():
                            if symptom in manifestation.lower():
                                found_code = {
                                    'coding': [{
                                        'system': 'http://snomed.info/sct',
                                        'code': coding_info['snomed'],
                                        'display': coding_info['display']
                                    }],
                                    'text': manifestation
                                }
                                break

                        if not found_code:
                            found_code = {'text': manifestation}

                        fhir_reaction['manifestation'].append(found_code)
                    else:
                        fhir_reaction['manifestation'].append(manifestation)

            # Severity
            if 'severity' in reaction:
                fhir_reaction['severity'] = self._normalize_severity(reaction['severity'])

            # Onset
            if 'onset' in reaction:
                fhir_reaction['onset'] = reaction['onset']

            # Description/note
            if 'description' in reaction or 'note' in reaction:
                fhir_reaction['description'] = reaction.get('description') or reaction.get('note')

            fhir_reactions.append(fhir_reaction)

        return fhir_reactions

    def _normalize_severity(self, severity: str) -> str:
        """Normalize reaction severity to FHIR values"""
        severity_map = {
            'mild': 'mild',
            'moderate': 'moderate',
            'severe': 'severe',
            'low': 'mild',
            'high': 'severe'
        }
        return severity_map.get(str(severity).lower(), 'mild')

    def get_clinical_statistics(self) -> Dict[str, Any]:
        """Get clinical factory performance statistics"""
        return {
            'supported_resources': len(self.SUPPORTED_RESOURCES),
            'resource_metrics': self._clinical_metrics,
            'coding_cache_size': {
                'loinc': len(self._loinc_cache),
                'snomed': len(self._snomed_cache)
            },
            'factory_type': 'ClinicalResourceFactory'
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on clinical factory"""
        try:
            # Test clinical factory performance
            start_time = time.time()
            test_data = {'name': 'test', 'patient_id': 'test-patient'}
            test_observation = self._create_observation(test_data, 'health-check')
            creation_time = (time.time() - start_time) * 1000

            return {
                'status': 'healthy',
                'supported_resources': len(self.SUPPORTED_RESOURCES),
                'creation_time_ms': creation_time,
                'performance_ok': creation_time < 10.0,  # <10ms requirement
                'coding_systems': ['LOINC', 'SNOMED-CT', 'ICD-10', 'RxNorm'],
                'shared_components': {
                    'validators': self.validators is not None,
                    'coders': self.coders is not None,
                    'reference_manager': self.reference_manager is not None
                }
            }
        except Exception as e:
            logger.error(f"Clinical factory health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }