"""
EPIC 7.4 & 7.5: Encounter, Goal, and CommunicationRequest Resource Factory
Provides specialized creation for Encounter, Goal, CareTeam, and CommunicationRequest FHIR resources
"""

import uuid
import time
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from .base import BaseResourceFactory


logger = logging.getLogger(__name__)


class EncounterResourceFactory(BaseResourceFactory):
    """
    Specialized factory for Encounter, Goal, CareTeam, and CommunicationRequest FHIR resources.

    Supports:
    - Goal: Clinical care goals with targets, achievement status, and outcome tracking
    - CommunicationRequest: Communication requests for patient care coordination (EPIC 7.5)
    - Encounter: Patient encounters and visits (future implementation)
    - CareTeam: Care team coordination (future implementation)

    Features:
    - SNOMED CT coding for goal categories
    - Target measurements with LOINC codes
    - Achievement status tracking
    - CarePlan integration
    - Lifecycle status management
    - Communication request tracking with priority and medium
    """

    SUPPORTED_RESOURCES: Set[str] = {'Goal', 'Encounter', 'CareTeam', 'CommunicationRequest'}

    # Goal lifecycle statuses (FHIR R4)
    GOAL_LIFECYCLE_STATUSES = {
        'proposed', 'planned', 'accepted', 'active', 'on-hold',
        'completed', 'cancelled', 'entered-in-error', 'rejected'
    }

    # Goal achievement statuses (FHIR R4)
    GOAL_ACHIEVEMENT_STATUSES = {
        'in-progress', 'improving', 'worsening', 'no-change',
        'achieved', 'sustaining', 'not-achieved', 'no-progress',
        'not-attainable'
    }

    # Goal priority values
    GOAL_PRIORITIES = {
        'high-priority', 'medium-priority', 'low-priority'
    }

    # CommunicationRequest status values (FHIR R4)
    COMMUNICATION_REQUEST_STATUSES = {
        'draft', 'active', 'on-hold', 'revoked',
        'completed', 'entered-in-error', 'unknown'
    }

    # CommunicationRequest intent values (FHIR R4)
    COMMUNICATION_REQUEST_INTENTS = {
        'proposal', 'plan', 'directive', 'order',
        'original-order', 'reflex-order', 'filler-order', 'instance-order', 'option'
    }

    # CommunicationRequest priority values (FHIR R4)
    COMMUNICATION_REQUEST_PRIORITIES = {
        'routine', 'urgent', 'asap', 'stat'
    }

    def __init__(self, validators, coders, reference_manager):
        """Initialize Encounter factory with goal tracking and communication request capabilities"""
        super().__init__(validators, coders, reference_manager)

        # Goal-specific metrics
        self._goal_metrics = {
            'total_goals': 0,
            'active_goals': 0,
            'completed_goals': 0,
            'goals_with_targets': 0,
            'goals_with_careplan': 0
        }

        # CommunicationRequest-specific metrics
        self._communication_request_metrics = {
            'total_requests': 0,
            'active_requests': 0,
            'completed_requests': 0,
            'urgent_requests': 0,
            'stat_requests': 0
        }

        # Initialize goal category mappings
        self._init_goal_category_mapping()

        # Initialize communication request category mappings
        self._init_communication_request_categories()

        self.logger.info("EncounterResourceFactory initialized with goal tracking and communication request support")

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _get_required_fields(self, resource_type: str) -> List[str]:
        """Get required fields for resource type"""
        if resource_type == 'Goal':
            return ['description', 'patient_id']  # lifecycleStatus handled by factory
        elif resource_type == 'CommunicationRequest':
            return ['patient_id']  # status and intent handled by factory
        elif resource_type == 'Encounter':
            return ['patient_id', 'class']
        elif resource_type == 'CareTeam':
            return ['patient_id']
        return []

    def _create_resource(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create resource based on type"""
        self.logger.debug(f"[{request_id}] Creating {resource_type} resource with EncounterResourceFactory")

        start_time = time.time()

        try:
            if resource_type == 'Goal':
                resource = self._create_goal(data, request_id)
            elif resource_type == 'CommunicationRequest':
                resource = self._create_communication_request(data, request_id)
            elif resource_type == 'Encounter':
                resource = self._create_encounter(data, request_id)
            elif resource_type == 'CareTeam':
                resource = self._create_careteam(data, request_id)
            else:
                raise ValueError(f"Unsupported resource type for EncounterResourceFactory: {resource_type}")

            # Track performance
            duration_ms = (time.time() - start_time) * 1000
            self._track_metrics(resource_type, duration_ms)

            # Add factory metadata
            resource['meta'] = resource.get('meta', {})
            resource['meta']['factory'] = 'EncounterResourceFactory'
            resource['meta']['creation_time_ms'] = round(duration_ms, 2)
            if request_id:
                resource['meta']['request_id'] = request_id

            return resource

        except Exception as e:
            self.logger.error(f"[{request_id}] {resource_type} creation failed: {str(e)}")
            raise

    def _create_goal(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a FHIR R4 Goal resource.

        Goal structure includes:
        - lifecycleStatus: proposed | planned | accepted | active | on-hold | completed | cancelled | entered-in-error | rejected
        - achievementStatus: in-progress | improving | worsening | no-change | achieved | sustaining | not-achieved | no-progress | not-attainable
        - category: Type of goal (dietary, safety, behavioral, etc.)
        - priority: high-priority | medium-priority | low-priority
        - description: Human-readable description of the goal
        - subject: Patient reference
        - startDate: When goal pursuit begins
        - target: Target outcome for goal
        - addresses: Health issues this goal addresses
        - outcomeReference: Observations/resources documenting outcomes
        """
        # Generate unique ID
        goal_id = data.get('identifier', f"goal-{uuid.uuid4().hex[:8]}")

        # Map status variations to FHIR lifecycleStatus
        status = data.get('status', 'active').lower()
        lifecycle_status = self._normalize_goal_status(status)

        # Build basic Goal structure
        goal = {
            'resourceType': 'Goal',
            'id': goal_id,
            'lifecycleStatus': lifecycle_status,
            'description': self._create_goal_description(data),
            'subject': {
                'reference': f"Patient/{data.get('patient_id', data.get('patient_ref', ''))}"
            }
        }

        # Add category with SNOMED CT coding
        category = self._determine_goal_category(data)
        if category:
            goal['category'] = [category]

        # Add priority
        priority = self._normalize_goal_priority(data.get('priority'))
        if priority:
            goal['priority'] = priority

        # Add achievement status
        if 'achievement_status' in data or 'achievementStatus' in data:
            achievement = data.get('achievement_status', data.get('achievementStatus'))
            normalized_achievement = self._normalize_achievement_status(achievement)
            if normalized_achievement:
                goal['achievementStatus'] = normalized_achievement

        # Add start date
        if 'start_date' in data or 'startDate' in data:
            goal['startDate'] = data.get('start_date', data.get('startDate'))
        elif lifecycle_status == 'active':
            goal['startDate'] = datetime.utcnow().date().isoformat()

        # Add target(s)
        targets = self._create_goal_targets(data)
        if targets:
            goal['target'] = targets
            self._goal_metrics['goals_with_targets'] += 1

        # Add addresses (conditions/problems this goal addresses)
        if 'addresses' in data:
            goal['addresses'] = []
            addresses = data['addresses'] if isinstance(data['addresses'], list) else [data['addresses']]
            for addr in addresses:
                if '/' in str(addr):  # Already a reference
                    goal['addresses'].append({'reference': str(addr)})
                else:
                    goal['addresses'].append({'reference': f"Condition/{addr}"})

        # Add outcome references
        if 'outcome' in data or 'outcomeReference' in data:
            outcome_data = data.get('outcome', data.get('outcomeReference'))
            if isinstance(outcome_data, dict) and 'reference' in outcome_data:
                goal['outcomeReference'] = [outcome_data]
            elif isinstance(outcome_data, list):
                goal['outcomeReference'] = outcome_data
            else:
                goal['outcomeReference'] = [{'reference': str(outcome_data)}]

        # Add notes if provided
        if 'note' in data or 'notes' in data:
            notes = data.get('note', data.get('notes'))
            if isinstance(notes, str):
                goal['note'] = [{
                    'text': notes,
                    'time': datetime.utcnow().isoformat() + 'Z'
                }]
            elif isinstance(notes, list):
                goal['note'] = []
                for note_text in notes:
                    goal['note'].append({
                        'text': note_text if isinstance(note_text, str) else note_text.get('text', ''),
                        'time': datetime.utcnow().isoformat() + 'Z'
                    })

        # Track metrics
        self._goal_metrics['total_goals'] += 1
        if lifecycle_status == 'active':
            self._goal_metrics['active_goals'] += 1
        elif lifecycle_status == 'completed':
            self._goal_metrics['completed_goals'] += 1

        return goal

    def _create_encounter(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a FHIR R4 Encounter resource.

        Placeholder implementation for future Epic development.
        """
        encounter_id = f"encounter-{uuid.uuid4().hex[:8]}"

        encounter = {
            'resourceType': 'Encounter',
            'id': encounter_id,
            'status': data.get('status', 'planned'),
            'class': {
                'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                'code': data.get('class', 'AMB'),
                'display': data.get('class_display', 'ambulatory')
            },
            'subject': {
                'reference': f"Patient/{data.get('patient_id', data.get('patient_ref', ''))}"
            }
        }

        return encounter

    def _create_careteam(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a FHIR R4 CareTeam resource.

        Placeholder implementation for future Epic development.
        """
        careteam_id = f"careteam-{uuid.uuid4().hex[:8]}"

        careteam = {
            'resourceType': 'CareTeam',
            'id': careteam_id,
            'status': data.get('status', 'active'),
            'subject': {
                'reference': f"Patient/{data.get('patient_id', data.get('patient_ref', ''))}"
            }
        }

        return careteam

    def _create_communication_request(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a FHIR R4 CommunicationRequest resource.

        CommunicationRequest structure includes:
        - status: draft | active | on-hold | revoked | completed | entered-in-error | unknown (required)
        - intent: proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option (required)
        - category: Type of communication (alert, notification, reminder, instruction)
        - priority: routine | urgent | asap | stat
        - medium: Communication channel (phone, fax, email, etc.)
        - subject: Patient reference (required)
        - recipient: Who should receive the communication
        - sender: Who is requesting the communication
        - payload: Content to be communicated
        - occurrence: When communication should occur
        - authoredOn: When request was created
        - reasonCode: Why communication is requested
        - reasonReference: Related resources explaining why
        - note: Additional notes about the request
        """
        # Generate unique ID
        comm_req_id = data.get('identifier', f"comm-req-{uuid.uuid4().hex[:8]}")

        # Normalize status and intent
        status = self._normalize_communication_request_status(data.get('status', 'active'))
        intent = self._normalize_communication_request_intent(data.get('intent', 'order'))

        # Build basic CommunicationRequest structure
        communication_request = {
            'resourceType': 'CommunicationRequest',
            'id': comm_req_id,
            'status': status,
            'intent': intent,
            'subject': {
                'reference': f"Patient/{data.get('patient_id', data.get('patient_ref', ''))}"
            }
        }

        # Add category (type of communication)
        if 'category' in data:
            categories = data['category'] if isinstance(data['category'], list) else [data['category']]
            communication_request['category'] = []
            for cat in categories:
                communication_request['category'].append(self._create_communication_category(cat))

        # Add priority
        if 'priority' in data:
            priority = self._normalize_communication_request_priority(data.get('priority'))
            if priority:
                communication_request['priority'] = priority

        # Add medium (communication channel)
        if 'medium' in data:
            media = data['medium'] if isinstance(data['medium'], list) else [data['medium']]
            communication_request['medium'] = []
            for medium in media:
                communication_request['medium'].append(self._create_communication_medium(medium))

        # Add recipient(s)
        if 'recipient' in data:
            recipients = data['recipient'] if isinstance(data['recipient'], list) else [data['recipient']]
            communication_request['recipient'] = []
            for recipient in recipients:
                if isinstance(recipient, dict) and 'reference' in recipient:
                    communication_request['recipient'].append(recipient)
                else:
                    # Assume it's a practitioner or related person reference
                    ref_str = str(recipient)
                    if '/' not in ref_str:
                        ref_str = f"Practitioner/{ref_str}"
                    communication_request['recipient'].append({'reference': ref_str})

        # Add sender
        if 'sender' in data:
            sender = data['sender']
            if isinstance(sender, dict) and 'reference' in sender:
                communication_request['sender'] = sender
            else:
                ref_str = str(sender)
                if '/' not in ref_str:
                    ref_str = f"Practitioner/{ref_str}"
                communication_request['sender'] = {'reference': ref_str}

        # Add payload (content to be communicated)
        if 'payload' in data:
            payloads = data['payload'] if isinstance(data['payload'], list) else [data['payload']]
            communication_request['payload'] = []
            for payload in payloads:
                if isinstance(payload, dict):
                    # Payload can have contentString, contentAttachment, or contentReference
                    payload_entry = {}
                    if 'contentString' in payload or 'content_string' in payload:
                        payload_entry['contentString'] = payload.get('contentString', payload.get('content_string'))
                    elif 'contentAttachment' in payload or 'content_attachment' in payload:
                        payload_entry['contentAttachment'] = payload.get('contentAttachment', payload.get('content_attachment'))
                    elif 'contentReference' in payload or 'content_reference' in payload:
                        payload_entry['contentReference'] = payload.get('contentReference', payload.get('content_reference'))
                    elif 'content' in payload:
                        # Generic content field - treat as string
                        payload_entry['contentString'] = str(payload['content'])

                    if payload_entry:
                        communication_request['payload'].append(payload_entry)
                elif isinstance(payload, str):
                    # Simple string payload
                    communication_request['payload'].append({'contentString': payload})

        # Add occurrence (when to send)
        if 'occurrence_datetime' in data or 'occurrenceDateTime' in data:
            communication_request['occurrenceDateTime'] = data.get('occurrence_datetime', data.get('occurrenceDateTime'))
        elif 'occurrence_period' in data or 'occurrencePeriod' in data:
            period_data = data.get('occurrence_period', data.get('occurrencePeriod'))
            communication_request['occurrencePeriod'] = {}
            if 'start' in period_data:
                communication_request['occurrencePeriod']['start'] = period_data['start']
            if 'end' in period_data:
                communication_request['occurrencePeriod']['end'] = period_data['end']

        # Add authoredOn (when request was created)
        if 'authored_on' in data or 'authoredOn' in data:
            communication_request['authoredOn'] = data.get('authored_on', data.get('authoredOn'))
        elif status in ['active', 'draft']:
            # Auto-generate for new requests
            communication_request['authoredOn'] = datetime.utcnow().isoformat() + 'Z'

        # Add reasonCode (why communication is needed)
        if 'reason_code' in data or 'reasonCode' in data:
            reason_codes = data.get('reason_code', data.get('reasonCode'))
            if not isinstance(reason_codes, list):
                reason_codes = [reason_codes]
            communication_request['reasonCode'] = []
            for reason in reason_codes:
                if isinstance(reason, dict):
                    communication_request['reasonCode'].append(reason)
                else:
                    communication_request['reasonCode'].append({'text': str(reason)})

        # Add reasonReference (reference to related resources)
        if 'reason_reference' in data or 'reasonReference' in data:
            reason_refs = data.get('reason_reference', data.get('reasonReference'))
            if not isinstance(reason_refs, list):
                reason_refs = [reason_refs]
            communication_request['reasonReference'] = []
            for ref in reason_refs:
                if isinstance(ref, dict) and 'reference' in ref:
                    communication_request['reasonReference'].append(ref)
                else:
                    communication_request['reasonReference'].append({'reference': str(ref)})

        # Add encounter reference if provided
        if 'encounter' in data or 'encounter_id' in data:
            encounter_ref = data.get('encounter', data.get('encounter_id'))
            if isinstance(encounter_ref, dict) and 'reference' in encounter_ref:
                communication_request['encounter'] = encounter_ref
            else:
                ref_str = str(encounter_ref)
                if '/' not in ref_str:
                    ref_str = f"Encounter/{ref_str}"
                communication_request['encounter'] = {'reference': ref_str}

        # Add notes
        if 'note' in data or 'notes' in data:
            notes = data.get('note', data.get('notes'))
            if isinstance(notes, str):
                communication_request['note'] = [{
                    'text': notes,
                    'time': datetime.utcnow().isoformat() + 'Z'
                }]
            elif isinstance(notes, list):
                communication_request['note'] = []
                for note_text in notes:
                    if isinstance(note_text, dict):
                        communication_request['note'].append(note_text)
                    else:
                        communication_request['note'].append({
                            'text': str(note_text),
                            'time': datetime.utcnow().isoformat() + 'Z'
                        })

        # Track metrics
        self._communication_request_metrics['total_requests'] += 1
        if status == 'active':
            self._communication_request_metrics['active_requests'] += 1
        elif status == 'completed':
            self._communication_request_metrics['completed_requests'] += 1

        priority_str = communication_request.get('priority', '').lower()
        if priority_str == 'urgent':
            self._communication_request_metrics['urgent_requests'] += 1
        elif priority_str == 'stat':
            self._communication_request_metrics['stat_requests'] += 1

        return communication_request

    def _init_goal_category_mapping(self):
        """Initialize goal category mappings with SNOMED CT codes"""
        self.goal_categories = {
            'dietary': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-category',
                    'code': 'dietary',
                    'display': 'Dietary'
                }],
                'text': 'Dietary Goal'
            },
            'safety': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-category',
                    'code': 'safety',
                    'display': 'Safety'
                }],
                'text': 'Safety Goal'
            },
            'behavioral': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-category',
                    'code': 'behavioral',
                    'display': 'Behavioral'
                }],
                'text': 'Behavioral Goal'
            },
            'nursing': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-category',
                    'code': 'nursing',
                    'display': 'Nursing'
                }],
                'text': 'Nursing Goal'
            },
            'physiotherapy': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-category',
                    'code': 'physiotherapy',
                    'display': 'Physiotherapy'
                }],
                'text': 'Physiotherapy Goal'
            }
        }

    def _normalize_goal_status(self, status: str) -> str:
        """Normalize input status to FHIR lifecycleStatus"""
        status_lower = status.lower()

        # Handle common variations
        if status_lower in self.GOAL_LIFECYCLE_STATUSES:
            return status_lower

        # Map common aliases
        status_mapping = {
            'in-progress': 'active',
            'in progress': 'active',
            'draft': 'proposed',
            'pending': 'proposed',
            'finished': 'completed',
            'done': 'completed',
            'stopped': 'cancelled',
            'abandoned': 'cancelled'
        }

        return status_mapping.get(status_lower, 'active')  # Default to active

    def _normalize_achievement_status(self, status: str) -> Optional[Dict[str, Any]]:
        """Normalize achievement status to FHIR CodeableConcept"""
        if not status:
            return None

        status_lower = status.lower().replace(' ', '-')

        # Map to standard FHIR achievement status codes
        status_mapping = {
            'in-progress': 'in-progress',
            'in_progress': 'in-progress',
            'improving': 'improving',
            'worsening': 'worsening',
            'no-change': 'no-change',
            'no_change': 'no-change',
            'achieved': 'achieved',
            'sustaining': 'sustaining',
            'not-achieved': 'not-achieved',
            'not_achieved': 'not-achieved',
            'no-progress': 'no-progress',
            'no_progress': 'no-progress',
            'not-attainable': 'not-attainable',
            'not_attainable': 'not-attainable'
        }

        code = status_mapping.get(status_lower, status_lower)

        if code in self.GOAL_ACHIEVEMENT_STATUSES:
            return {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-achievement',
                    'code': code,
                    'display': code.replace('-', ' ').title()
                }],
                'text': code.replace('-', ' ').title()
            }

        return None

    def _normalize_goal_priority(self, priority: Optional[str]) -> Optional[Dict[str, Any]]:
        """Normalize priority to FHIR CodeableConcept"""
        if not priority:
            return None

        priority_lower = priority.lower()

        # Map to FHIR priority codes
        priority_mapping = {
            'high': 'high-priority',
            'medium': 'medium-priority',
            'low': 'low-priority',
            'high-priority': 'high-priority',
            'medium-priority': 'medium-priority',
            'low-priority': 'low-priority'
        }

        code = priority_mapping.get(priority_lower)

        if code:
            return {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/goal-priority',
                    'code': code,
                    'display': code.replace('-', ' ').title()
                }],
                'text': code.replace('-', ' ').title()
            }

        return None

    def _create_goal_description(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create goal description CodeableConcept"""
        description = data.get('description', 'Clinical Goal')

        return {
            'text': description
        }

    def _determine_goal_category(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine goal category based on input data"""
        # Check explicit category
        if 'category' in data:
            category_key = data['category'].lower()
            if category_key in self.goal_categories:
                return self.goal_categories[category_key]
            # Return custom category if not in predefined list
            return {
                'text': data['category']
            }

        # Try to infer from description
        description = data.get('description', '').lower()

        # Check for keywords
        if any(word in description for word in ['diet', 'nutrition', 'weight', 'food', 'eating']):
            return self.goal_categories['dietary']
        elif any(word in description for word in ['safety', 'fall', 'risk', 'harm']):
            return self.goal_categories['safety']
        elif any(word in description for word in ['behavior', 'smoking', 'exercise', 'activity', 'habit']):
            return self.goal_categories['behavioral']
        elif any(word in description for word in ['nursing', 'wound', 'care']):
            return self.goal_categories['nursing']
        elif any(word in description for word in ['physical', 'mobility', 'movement', 'therapy']):
            return self.goal_categories['physiotherapy']

        # No specific category determined
        return None

    def _create_goal_targets(self, data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Create target measurements for goal"""
        targets = []

        if 'target' in data:
            target_data = data['target']

            # Handle single target or list of targets
            if not isinstance(target_data, list):
                target_data = [target_data]

            for target in target_data:
                target_component = {}

                # Add measure (what is being measured)
                if 'measure' in target:
                    measure_text = target['measure']
                    target_component['measure'] = {
                        'text': measure_text
                    }

                # Add detail quantity
                if 'detail_quantity' in target or 'detailQuantity' in target:
                    detail = target.get('detail_quantity', target.get('detailQuantity'))
                    target_component['detailQuantity'] = {
                        'value': detail.get('value'),
                        'unit': detail.get('unit', 'unit')
                    }
                    if 'system' in detail:
                        target_component['detailQuantity']['system'] = detail['system']
                    if 'code' in detail:
                        target_component['detailQuantity']['code'] = detail['code']

                # Add detail range
                if 'detail_range' in target or 'detailRange' in target:
                    detail = target.get('detail_range', target.get('detailRange'))
                    target_component['detailRange'] = {}
                    if 'low' in detail:
                        target_component['detailRange']['low'] = {
                            'value': detail['low'].get('value'),
                            'unit': detail['low'].get('unit', 'unit')
                        }
                    if 'high' in detail:
                        target_component['detailRange']['high'] = {
                            'value': detail['high'].get('value'),
                            'unit': detail['high'].get('unit', 'unit')
                        }

                # Add detail codeable concept
                if 'detail_concept' in target or 'detailCodeableConcept' in target:
                    detail = target.get('detail_concept', target.get('detailCodeableConcept'))
                    target_component['detailCodeableConcept'] = {
                        'text': detail if isinstance(detail, str) else detail.get('text', '')
                    }

                # Add due date
                if 'due_date' in target or 'dueDate' in target:
                    target_component['dueDate'] = target.get('due_date', target.get('dueDate'))

                if target_component:
                    targets.append(target_component)

        return targets if targets else None

    def _normalize_communication_request_status(self, status: str) -> str:
        """Normalize input status to FHIR CommunicationRequest status"""
        status_lower = status.lower()

        # Handle common variations
        if status_lower in self.COMMUNICATION_REQUEST_STATUSES:
            return status_lower

        # Map common aliases
        status_mapping = {
            'pending': 'draft',
            'requested': 'active',
            'cancelled': 'revoked',
            'finished': 'completed',
            'done': 'completed',
            'error': 'entered-in-error'
        }

        return status_mapping.get(status_lower, 'active')  # Default to active

    def _normalize_communication_request_intent(self, intent: str) -> str:
        """Normalize input intent to FHIR CommunicationRequest intent"""
        intent_lower = intent.lower()

        # Handle common variations
        if intent_lower in self.COMMUNICATION_REQUEST_INTENTS:
            return intent_lower

        # Map common aliases
        intent_mapping = {
            'request': 'order',
            'recommendation': 'proposal',
            'scheduled': 'plan'
        }

        return intent_mapping.get(intent_lower, 'order')  # Default to order

    def _normalize_communication_request_priority(self, priority: str) -> Optional[str]:
        """Normalize input priority to FHIR CommunicationRequest priority"""
        if not priority:
            return None

        priority_lower = priority.lower()

        # Handle common variations
        if priority_lower in self.COMMUNICATION_REQUEST_PRIORITIES:
            return priority_lower

        # Map common aliases
        priority_mapping = {
            'normal': 'routine',
            'high': 'urgent',
            'emergency': 'stat',
            'immediate': 'asap'
        }

        return priority_mapping.get(priority_lower, priority_lower)

    def _create_communication_category(self, category: Any) -> Dict[str, Any]:
        """Create a communication category CodeableConcept"""
        if isinstance(category, dict):
            # Already a CodeableConcept structure
            return category

        # Create from string
        category_str = str(category).lower()

        # Predefined categories
        category_codes = {
            'alert': 'Alert',
            'notification': 'Notification',
            'reminder': 'Reminder',
            'instruction': 'Instruction',
            'appointment-reminder': 'Appointment Reminder',
            'phone-consult': 'Phone Consult',
            'prescription-refill': 'Prescription Refill',
            'lab-results': 'Lab Results',
            'discharge-instructions': 'Discharge Instructions'
        }

        display = category_codes.get(category_str, category_str.replace('-', ' ').title())

        return {
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/communication-category',
                'code': category_str,
                'display': display
            }],
            'text': display
        }

    def _create_communication_medium(self, medium: Any) -> Dict[str, Any]:
        """Create a communication medium CodeableConcept"""
        if isinstance(medium, dict):
            # Already a CodeableConcept structure
            return medium

        # Create from string
        medium_str = str(medium).lower()

        # Predefined communication channels
        medium_codes = {
            'phone': ('WRITTEN', 'written'),
            'fax': ('FAX', 'fax'),
            'email': ('EMAI', 'email'),
            'sms': ('SMS', 'SMS'),
            'video': ('VIDEOCONF', 'video conference'),
            'voice': ('VOICE', 'voice'),
            'mail': ('POSTAL', 'postal mail'),
            'portal': ('PORTAL', 'patient portal'),
            'text': ('SMS', 'text message')
        }

        if medium_str in medium_codes:
            code, display = medium_codes[medium_str]
            return {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v3-ParticipationMode',
                    'code': code,
                    'display': display
                }],
                'text': display
            }
        else:
            # Custom medium
            return {
                'text': medium_str.replace('-', ' ').title()
            }

    def _init_communication_request_categories(self):
        """Initialize common communication request category mappings"""
        self.communication_categories = {
            'alert': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/communication-category',
                    'code': 'alert',
                    'display': 'Alert'
                }],
                'text': 'Alert'
            },
            'notification': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/communication-category',
                    'code': 'notification',
                    'display': 'Notification'
                }],
                'text': 'Notification'
            },
            'reminder': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/communication-category',
                    'code': 'reminder',
                    'display': 'Reminder'
                }],
                'text': 'Reminder'
            },
            'instruction': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/communication-category',
                    'code': 'instruction',
                    'display': 'Instruction'
                }],
                'text': 'Instruction'
            }
        }

    def _track_metrics(self, resource_type: str, duration_ms: float):
        """Track resource-specific metrics"""
        # Update base class metrics
        self._metrics['created'] += 1
        self._metrics['total_time_ms'] += duration_ms
        if self._metrics['created'] > 0:
            self._metrics['avg_time_ms'] = self._metrics['total_time_ms'] / self._metrics['created']

    def get_goal_statistics(self) -> Dict[str, Any]:
        """Get Goal factory statistics"""
        return {
            'supported_resources': len(self.SUPPORTED_RESOURCES),
            'goal_metrics': self._goal_metrics,
            'performance_metrics': self._metrics,
            'factory_type': 'EncounterResourceFactory'
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Encounter factory"""
        try:
            # Test basic Goal creation
            test_data = {
                'patient_id': 'test-patient',
                'description': 'Health Check Test Goal',
                'status': 'proposed'
            }

            start_time = time.time()
            test_resource = self._create_goal(test_data, 'health-check')
            creation_time = (time.time() - start_time) * 1000

            return {
                'status': 'healthy',
                'supported_resources': len(self.SUPPORTED_RESOURCES),
                'creation_time_ms': round(creation_time, 2),
                'performance_ok': creation_time < 10.0,
                'goal_categories': len(self.goal_categories),
                'shared_components': {
                    'validators': self.validators is not None,
                    'coders': self.coders is not None,
                    'reference_manager': self.reference_manager is not None
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'supported_resources': len(self.SUPPORTED_RESOURCES)
            }
