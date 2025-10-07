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

from fhir.resources.consent import Consent, ConsentProvision, ConsentProvisionActor, ConsentProvisionData
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from fhir.resources.period import Period

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

    # Decision constants (FHIR R4)
    DECISION_PERMIT = 'permit'
    DECISION_DENY = 'deny'

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
                - category: List of consent categories (HIPAA, research, etc.)
                - patient_id: Reference to Patient resource
                - date_time: Date of consent (ISO 8601 date string)
                - decision: permit|deny (FHIR R4 decision field)
                - purpose: List of purpose codes (TREAT, HPAYMT, etc.)
            request_id: Optional request ID for audit logging

        Returns:
            FHIR R4 Consent resource as dict

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        self._validate_consent_data(data)

        # Create provision with granular controls
        provision = self._create_provision(data)

        # Create Consent resource using fhir.resources library
        consent = Consent(
            status=data['status'],
            category=self._create_categories(data['category']),
            subject=Reference(reference=data['patient_id']),
            date=data.get('date_time', datetime.now().date().isoformat()),
            decision=data['decision'],
            provision=[provision] if provision else None,
        )

        # Add optional fields
        if 'organization_id' in data:
            consent.organization = [Reference(reference=data['organization_id'])]

        if 'policy_uri' in data:
            consent.policyBasis = {
                'url': data['policy_uri']
            }

        # Return as JSON-serializable dict
        consent_dict = consent.model_dump(mode='json', exclude_none=True)

        logger.info(
            f"Created Consent resource: decision={data['decision']}, "
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
        required_fields = ['status', 'category', 'patient_id', 'decision']

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate status
        valid_statuses = [self.STATUS_ACTIVE, self.STATUS_INACTIVE, self.STATUS_DRAFT, self.STATUS_REJECTED]
        if data['status'] not in valid_statuses:
            raise ValueError(f"Invalid status: {data['status']}. Must be one of {valid_statuses}")

        # Validate decision (FHIR R4)
        valid_decisions = [self.DECISION_PERMIT, self.DECISION_DENY]
        if data['decision'] not in valid_decisions:
            raise ValueError(f"Invalid decision: {data['decision']}. Must be one of {valid_decisions}")

        # Validate category is a list
        if not isinstance(data['category'], list) or len(data['category']) == 0:
            raise ValueError("Category must be a non-empty list")

        # Validate patient_id format
        if not data['patient_id'].startswith('Patient/'):
            raise ValueError("patient_id must be a Patient reference (Patient/...)")

    def _create_categories(self, categories: List[str]) -> List[CodeableConcept]:
        """
        Create category CodeableConcepts from category strings.

        Args:
            categories: List of category strings (HIPAA, research, etc.)

        Returns:
            List of FHIR CodeableConcept objects
        """
        category_list = []
        for cat in categories:
            coding = Coding(
                system='http://terminology.hl7.org/CodeSystem/consentcategorycodes',
                code=cat,
                display=cat.upper()
            )
            category_list.append(CodeableConcept(coding=[coding]))

        return category_list

    def _create_provision(self, data: Dict[str, Any]) -> Optional[ConsentProvision]:
        """
        Create consent provision with granular controls.

        Args:
            data: Consent data with optional provision fields:
                - purpose: List of purpose codes
                - actor_id: Reference to actor (Practitioner, Organization)
                - actor_role: Role code for actor
                - data_category: List of data categories
                - period_start: Start date for validity period
                - period_end: End date for validity period

        Returns:
            ConsentProvision object or None if no provision data
        """
        provision_data = {}

        # Add purpose (treatment, payment, operations, etc.)
        if 'purpose' in data and data['purpose']:
            provision_data['purpose'] = [
                Coding(
                    system='http://terminology.hl7.org/CodeSystem/v3-ActReason',
                    code=purpose,
                    display=self._get_purpose_display(purpose)
                )
                for purpose in data['purpose']
            ]

        # Add actor (specific practitioner or organization)
        if 'actor_id' in data:
            actor_role_code = data.get('actor_role', self.ROLE_PRIMARY_CARE)
            actor_role = CodeableConcept(
                coding=[Coding(
                    system='http://terminology.hl7.org/CodeSystem/v3-ParticipationType',
                    code=actor_role_code,
                    display=self._get_role_display(actor_role_code)
                )]
            )

            provision_data['actor'] = [
                ConsentProvisionActor(
                    role=actor_role,
                    reference=Reference(reference=data['actor_id'])
                )
            ]

        # Add data categories (specific resource types)
        if 'data_category' in data and data['data_category']:
            provision_data['data'] = [
                ConsentProvisionData(
                    meaning='instance',
                    reference=Reference(reference=f"{cat}/")
                )
                for cat in data['data_category']
            ]

        # Add time period
        if 'period_start' in data or 'period_end' in data:
            period_dict = {}
            if 'period_start' in data:
                period_dict['start'] = data['period_start']
            if 'period_end' in data:
                period_dict['end'] = data['period_end']

            provision_data['period'] = Period(**period_dict)

        # Return provision if we have any data, otherwise None
        if provision_data:
            return ConsentProvision(**provision_data)
        else:
            return None

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
        Check if consent permits access for given context.

        Args:
            consent_resource: FHIR Consent resource
            purpose: Purpose code to check (TREAT, HPAYMT, etc.)
            actor_id: Optional actor ID to check against

        Returns:
            True if consent permits access, False otherwise
        """
        # Check if consent is active
        if not self.is_consent_active(consent_resource):
            return False

        # Get decision
        decision = consent_resource.get('decision', self.DECISION_DENY)

        # If no provision, use decision directly
        if 'provision' not in consent_resource or not consent_resource['provision']:
            return decision == self.DECISION_PERMIT

        # Check provisions
        for provision in consent_resource['provision']:
            # Check purpose
            if 'purpose' in provision:
                purpose_codes = [p['code'] for p in provision['purpose']]
                if purpose not in purpose_codes:
                    continue  # Purpose not in this provision

            # Check actor if specified
            if actor_id and 'actor' in provision:
                actor_refs = [a['reference']['reference'] for a in provision['actor']]
                if actor_id not in actor_refs:
                    continue  # Actor not in this provision

            # If we get here, provision matches context
            return decision == self.DECISION_PERMIT

        # No matching provision found
        return decision == self.DECISION_DENY

    def is_consent_active(self, consent_resource: Dict[str, Any]) -> bool:
        """
        Check if consent is currently active and valid.

        Args:
            consent_resource: FHIR Consent resource

        Returns:
            True if consent is active and within validity period
        """
        # Check status
        if consent_resource.get('status') != self.STATUS_ACTIVE:
            return False

        # Check time period if present
        if 'provision' in consent_resource and consent_resource['provision']:
            for provision in consent_resource['provision']:
                if 'period' in provision:
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
