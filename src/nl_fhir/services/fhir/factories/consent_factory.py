"""
ConsentFactory - Epic 9 Phase 3: User Story 2
FHIR R4 Consent resource factory with granular privacy controls.

Constitutional Compliance:
- Medical Safety First: Validates all consent data before processing
- HIPAA Compliance: Zero PHI in logs, uses patient references only
- FHIR R4 Compliance: 100% FHIR R4 Consent specification adherence
- Modular Architecture: ~500 lines, factory pattern with shared components
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
import logging
import uuid

from .base import BaseResourceFactory

logger = logging.getLogger(__name__)


class ConsentFactory(BaseResourceFactory):
    """
    Factory for creating FHIR R4 Consent resources with granular privacy controls.

    Supports:
    - Patient privacy consents (HIPAA, research, marketing)
    - Granular access control (purpose, actor, data category, time period)
    - Permit/deny decisions
    - Active/inactive status management
    - Consent enforcement checking
    """

    # Status constants
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_DRAFT = 'draft'
    STATUS_REJECTED = 'rejected'

    # Policy Rule constants (FHIR R4 uses policyRule, not decision)
    POLICY_OPTIN = 'OPTIN'  # Opt-in consent (permit)
    POLICY_OPTOUT = 'OPTOUT'  # Opt-out consent (deny)

    # Scope constants (FHIR R4 required field)
    SCOPE_PATIENT_PRIVACY = 'patient-privacy'
    SCOPE_RESEARCH = 'research'
    SCOPE_TREATMENT = 'treatment'

    # Category constants
    CATEGORY_HIPAA = 'HIPAA'
    CATEGORY_RESEARCH = 'research'
    CATEGORY_MARKETING = 'marketing'
    CATEGORY_DISCLOSURE = 'disclosure'

    # Purpose constants (FHIR purpose-of-use codes)
    PURPOSE_TREAT = 'TREAT'  # Treatment
    PURPOSE_PAYMENT = 'HPAYMT'  # Healthcare payment
    PURPOSE_OPERATIONS = 'HOPERAT'  # Healthcare operations
    PURPOSE_MARKETING = 'HMARKT'  # Marketing
    PURPOSE_RESEARCH = 'HRESCH'  # Healthcare research

    # Actor role constants
    ROLE_PRIMARY_CARE = 'PRCP'  # Primary care provider
    ROLE_CONSULTANT = 'CONSULT'  # Consultant
    ROLE_EMERGENCY = 'ECON'  # Emergency contact

    def __init__(self, validators=None, coders=None, reference_manager=None):
        """Initialize ConsentFactory with shared components."""
        super().__init__(validators=validators, coders=coders, reference_manager=reference_manager)
        logger.info("ConsentFactory initialized")

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type."""
        return resource_type == 'Consent'

    def _create_resource(
        self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create FHIR R4 Consent resource from input data.

        Args:
            resource_type: Must be 'Consent'
            data: Consent data with required fields:
                - status: active|inactive|draft|rejected
                - scope: Consent scope (patient-privacy, research, etc.)
                - category: List of consent categories
                - patient_id: Reference to Patient resource
                - date_time: DateTime of consent (ISO 8601 datetime string)
                - policy_rule: Policy rule code (OPTIN, OPTOUT, etc.)
                - purpose: Optional list of purpose codes (TREAT, HPAYMT, etc.)
            request_id: Optional request ID for audit logging

        Returns:
            FHIR R4 Consent resource as dict (manually constructed for R4 compliance)

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        self._validate_consent_data(data)

        # Build FHIR R4 Consent manually (fhir.resources 8.x uses R5/R6, not R4)
        consent_dict = {
            'resourceType': 'Consent',
            'id': str(uuid.uuid4()),
            'status': data['status'],
            'scope': self._create_scope(data.get('scope', 'patient-privacy')),
            'category': self._create_categories(data['category']),
            'patient': {'reference': data['patient_id']},
            'dateTime': data.get('date_time', datetime.now().isoformat()),
            'policyRule': self._create_policy_rule(data.get('policy_rule', 'OPTIN')),
        }

        # Add optional provision with granular controls
        provision = self._create_provision(data)
        if provision:
            consent_dict['provision'] = provision

        # Add optional fields
        if 'organization_id' in data:
            consent_dict['organization'] = [{'reference': data['organization_id']}]

        if 'performer' in data:
            consent_dict['performer'] = [{'reference': data['performer']}]

        logger.info(
            f"Created FHIR R4 Consent resource: scope={data.get('scope', 'patient-privacy')}, "
            f"patient={data['patient_id']}, request_id={request_id}"
        )

        return consent_dict

    def _validate_consent_data(self, data: Dict[str, Any]) -> None:
        """
        Validate consent data has required fields.

        Args:
            data: Input consent data

        Raises:
            ValueError: If required fields are missing
        """
        # FHIR R4 required fields (no 'decision' field in R4!)
        required_fields = ['status', 'category', 'patient_id']

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate status
        valid_statuses = [self.STATUS_ACTIVE, self.STATUS_INACTIVE, self.STATUS_DRAFT, self.STATUS_REJECTED]
        if data['status'] not in valid_statuses:
            raise ValueError(f"Invalid status: {data['status']}. Must be one of {valid_statuses}")

        # Validate category is a list
        if not isinstance(data['category'], list) or len(data['category']) == 0:
            raise ValueError("Category must be a non-empty list")

        # Validate patient_id format
        if not data['patient_id'].startswith('Patient/'):
            raise ValueError("patient_id must be a Patient reference (Patient/...)")

    def _create_scope(self, scope_code: str) -> Dict[str, Any]:
        """
        Create FHIR R4 scope CodeableConcept.

        Args:
            scope_code: Scope code (patient-privacy, research, etc.)

        Returns:
            FHIR CodeableConcept dict
        """
        return {
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/consentscope',
                'code': scope_code
            }]
        }

    def _create_policy_rule(self, policy_code: str) -> Dict[str, Any]:
        """
        Create FHIR R4 policyRule CodeableConcept.

        Args:
            policy_code: Policy rule code (OPTIN, OPTOUT, etc.)

        Returns:
            FHIR CodeableConcept dict
        """
        return {
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                'code': policy_code
            }]
        }

    def _create_categories(self, categories: List[str]) -> List[Dict[str, Any]]:
        """
        Create category CodeableConcepts from category strings.

        Args:
            categories: List of category strings

        Returns:
            List of FHIR CodeableConcept dicts (using LOINC codes for consent categories)
        """
        # Use LOINC codes for consent categories (required by HAPI)
        category_mapping = {
            'HIPAA': '59284-0',  # LOINC code for "Consent Document"
            'research': '64292-6',  # LOINC code for "Release of information consent"
            'marketing': '59284-0',  # Default to consent document
        }

        category_list = []
        for cat in categories:
            loinc_code = category_mapping.get(cat, '59284-0')
            category_list.append({
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': loinc_code
                }]
            })

        return category_list

    def _create_provision(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create consent provision with granular controls (FHIR R4 format).

        Args:
            data: Consent data with optional provision fields:
                - purpose: List of purpose codes
                - actor_id: Reference to actor (Practitioner, Organization)
                - actor_role: Role code for actor
                - period_start: Start date for validity period
                - period_end: End date for validity period

        Returns:
            Provision dict (object, not array) or None if no provision data
        """
        provision = {}

        # Add purpose (treatment, payment, operations, etc.)
        if 'purpose' in data and data['purpose']:
            provision['purpose'] = [
                {
                    'system': 'http://terminology.hl7.org/CodeSystem/v3-ActReason',
                    'code': purpose,
                    'display': self._get_purpose_display(purpose)
                }
                for purpose in data['purpose']
            ]

        # Add actor (specific practitioner or organization)
        if 'actor_id' in data:
            actor_role_code = data.get('actor_role', self.ROLE_PRIMARY_CARE)
            provision['actor'] = [{
                'role': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ParticipationType',
                        'code': actor_role_code,
                        'display': self._get_role_display(actor_role_code)
                    }]
                },
                'reference': {'reference': data['actor_id']}
            }]

        # Add time period
        if 'period_start' in data or 'period_end' in data:
            period = {}
            if 'period_start' in data:
                period['start'] = data['period_start']
            if 'period_end' in data:
                period['end'] = data['period_end']
            provision['period'] = period

        # Return provision if we have any data, otherwise None
        return provision if provision else None

    def _get_purpose_display(self, purpose_code: str) -> str:
        """Get human-readable display for purpose code."""
        purpose_displays = {
            self.PURPOSE_TREAT: 'Treatment',
            self.PURPOSE_PAYMENT: 'Healthcare Payment',
            self.PURPOSE_OPERATIONS: 'Healthcare Operations',
            self.PURPOSE_MARKETING: 'Marketing',
            self.PURPOSE_RESEARCH: 'Healthcare Research',
        }
        return purpose_displays.get(purpose_code, purpose_code)

    def _get_role_display(self, role_code: str) -> str:
        """Get human-readable display for actor role code."""
        role_displays = {
            self.ROLE_PRIMARY_CARE: 'Primary Care Provider',
            self.ROLE_CONSULTANT: 'Consultant',
            self.ROLE_EMERGENCY: 'Emergency Contact',
        }
        return role_displays.get(role_code, role_code)

    def check_consent(
        self, consent_resource: Dict[str, Any], purpose: str, actor_id: Optional[str] = None
    ) -> bool:
        """
        Check if consent permits access for given context (FHIR R4 format).

        Args:
            consent_resource: FHIR R4 Consent resource
            purpose: Purpose code to check (TREAT, HPAYMT, etc.)
            actor_id: Optional actor ID to check against

        Returns:
            True if consent permits access, False otherwise

        Note: FHIR R4 uses policyRule (OPTIN/OPTOUT) instead of decision field
        """
        # Check if consent is active
        if not self.is_consent_active(consent_resource):
            return False

        # Check policyRule (OPTIN = permit, OPTOUT = deny)
        policy_rule = consent_resource.get('policyRule', {})
        policy_code = policy_rule.get('coding', [{}])[0].get('code', 'OPTOUT')
        is_optin = policy_code == 'OPTIN'

        # If no provision, use policyRule directly
        provision = consent_resource.get('provision')
        if not provision:
            return is_optin

        # Check provision (object in R4, not array!)
        # Check purpose
        if 'purpose' in provision:
            purpose_codes = [p['code'] for p in provision['purpose']]
            if purpose and purpose not in purpose_codes:
                return False  # Purpose not in provision

        # Check actor if specified
        if actor_id and 'actor' in provision:
            actor_refs = [a['reference']['reference'] for a in provision['actor']]
            if actor_id not in actor_refs:
                return False  # Actor not in provision

        # Provision matches context
        return is_optin

    def is_consent_active(self, consent_resource: Dict[str, Any]) -> bool:
        """
        Check if consent is currently active and valid (FHIR R4 format).

        Args:
            consent_resource: FHIR R4 Consent resource

        Returns:
            True if consent is active and within validity period
        """
        # Check status
        if consent_resource.get('status') != self.STATUS_ACTIVE:
            return False

        # Check time period if present (provision is object in R4, not array!)
        provision = consent_resource.get('provision')
        if provision and 'period' in provision:
            period = provision['period']
            now = datetime.now().date()

            # Check start date
            if 'start' in period:
                start_date = date.fromisoformat(period['start'])
                if now < start_date:
                    return False

            # Check end date
            if 'end' in period:
                end_date = date.fromisoformat(period['end'])
                if now > end_date:
                    return False

        return True

    def query_consents_by_patient(
        self, patient_id: str, active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Create query parameters for searching consents by patient.

        Args:
            patient_id: Patient reference (Patient/...)
            active_only: If True, only return active consents

        Returns:
            Query parameters dict for FHIR search
        """
        query_params = {
            'subject': patient_id,
        }

        if active_only:
            query_params['status'] = self.STATUS_ACTIVE

        return query_params

    def query_consents_by_purpose(
        self, purpose: str, patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create query parameters for searching consents by purpose.

        Args:
            purpose: Purpose code (TREAT, HPAYMT, etc.)
            patient_id: Optional patient reference to filter by

        Returns:
            Query parameters dict for FHIR search
        """
        query_params = {
            'purpose': purpose,
        }

        if patient_id:
            query_params['subject'] = patient_id

        return query_params
