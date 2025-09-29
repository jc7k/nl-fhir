"""
REFACTOR-006: CarePlan Resource Factory - Care Management and Coordination
Provides specialized creation for CarePlan FHIR resources
"""

import uuid
import time
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from .base import BaseResourceFactory


logger = logging.getLogger(__name__)


class CarePlanResourceFactory(BaseResourceFactory):
    """
    Specialized factory for CarePlan FHIR resources for care management and coordination.

    Supports:
    - CarePlan: Care management plans with activities, goals, and care team coordination

    Features:
    - SNOMED CT coding for care plan categories
    - Support for complex multi-activity care plans
    - Care team and goal references
    - Status and intent validation
    - Period management for care plan timelines
    """

    SUPPORTED_RESOURCES: Set[str] = {'CarePlan'}

    # CarePlan status values
    CAREPLAN_STATUSES = {
        'draft', 'active', 'on-hold', 'revoked', 'completed',
        'entered-in-error', 'unknown'
    }

    # CarePlan intent values
    CAREPLAN_INTENTS = {
        'proposal', 'plan', 'order', 'option', 'directive'
    }

    def __init__(self, validators, coders, reference_manager):
        """Initialize CarePlan factory with care coordination capabilities"""
        super().__init__(validators, coders, reference_manager)

        # CarePlan-specific caching and tracking
        self._careplan_metrics = {
            'total_careplans': 0,
            'active_careplans': 0,
            'careplans_with_activities': 0,
            'careplans_with_goals': 0
        }

        # Initialize care plan category mappings
        self._init_careplan_category_mapping()
        self._init_activity_kind_mapping()

        self.logger.info("CarePlanResourceFactory initialized with care coordination support")

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the CarePlan resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _get_required_fields(self, resource_type: str) -> list[str]:
        """Get required fields for CarePlan resource"""
        if resource_type == 'CarePlan':
            return ['patient_id']  # Status and intent handled by factory
        return []

    def _create_resource(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create CarePlan resource"""
        self.logger.debug(f"[{request_id}] Creating {resource_type} resource with CarePlanResourceFactory")

        start_time = time.time()

        try:
            if resource_type == 'CarePlan':
                resource = self._create_careplan(data, request_id)
            else:
                raise ValueError(f"Unsupported resource type for CarePlanResourceFactory: {resource_type}")

            # Track CarePlan factory performance
            duration_ms = (time.time() - start_time) * 1000
            self._track_careplan_metrics(resource_type, duration_ms)

            # Add factory metadata
            resource['meta'] = resource.get('meta', {})
            resource['meta']['factory'] = 'CarePlanResourceFactory'
            resource['meta']['creation_time_ms'] = round(duration_ms, 2)
            if request_id:
                resource['meta']['request_id'] = request_id

            return resource

        except Exception as e:
            self.logger.error(f"[{request_id}] CarePlan creation failed: {str(e)}")
            raise

    def _create_careplan(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a FHIR R4 CarePlan resource.

        CarePlan structure includes:
        - status: draft | active | on-hold | revoked | completed | entered-in-error | unknown
        - intent: proposal | plan | order | option | directive
        - category: Type of care plan (e.g., assessment, therapy)
        - title: Human-readable name
        - description: Summary of plan
        - subject: Patient reference
        - period: Time period covered
        - created: Date record was created
        - author: Who created the plan
        - contributor: Who contributed to content
        - careTeam: Care team responsible
        - addresses: Health issues addressed
        - goal: Desired outcomes
        - activity: Action to occur as part of plan
        """
        # Generate unique ID
        careplan_id = f"careplan-{uuid.uuid4().hex[:8]}"

        # Get or generate status and intent
        status = data.get('status', 'active')
        if status not in self.CAREPLAN_STATUSES:
            self.logger.warning(f"Invalid CarePlan status '{status}', defaulting to 'active'")
            status = 'active'

        intent = data.get('intent', 'plan')
        if intent not in self.CAREPLAN_INTENTS:
            self.logger.warning(f"Invalid CarePlan intent '{intent}', defaulting to 'plan'")
            intent = 'plan'

        # Build basic CarePlan structure
        careplan = {
            'resourceType': 'CarePlan',
            'id': careplan_id,
            'status': status,
            'intent': intent,
            'subject': {
                'reference': f"Patient/{data['patient_id']}"
            }
        }

        # Add category with SNOMED CT coding
        category = self._determine_careplan_category(data)
        if category:
            careplan['category'] = [category]

        # Add title and description
        if 'title' in data:
            careplan['title'] = data['title']
        elif 'name' in data:
            careplan['title'] = data['name']
        else:
            careplan['title'] = f"Care Plan for Patient {data['patient_id']}"

        if 'description' in data:
            careplan['description'] = data['description']

        # Add period
        period = self._create_careplan_period(data)
        if period:
            careplan['period'] = period

        # Add created timestamp
        careplan['created'] = data.get('created', datetime.utcnow().isoformat() + 'Z')

        # Add author (required in many contexts)
        if 'author' in data or 'practitioner_id' in data:
            author_id = data.get('author', data.get('practitioner_id'))
            careplan['author'] = {
                'reference': f"Practitioner/{author_id}"
            }

        # Add contributors
        if 'contributors' in data:
            careplan['contributor'] = []
            for contributor_id in data['contributors']:
                careplan['contributor'].append({
                    'reference': f"Practitioner/{contributor_id}"
                })

        # Add care team reference
        if 'care_team_id' in data:
            careplan['careTeam'] = [{
                'reference': f"CareTeam/{data['care_team_id']}"
            }]

        # Add conditions/problems being addressed
        if 'addresses' in data or 'conditions' in data:
            careplan['addresses'] = []
            conditions = data.get('addresses', data.get('conditions', []))
            if isinstance(conditions, str):
                conditions = [conditions]
            for condition in conditions:
                if '/' in condition:  # Already a reference
                    careplan['addresses'].append({'reference': condition})
                else:
                    careplan['addresses'].append({'reference': f"Condition/{condition}"})

        # Add goals
        goals = self._create_careplan_goals(data)
        if goals:
            careplan['goal'] = goals

        # Add activities
        activities = self._create_careplan_activities(data)
        if activities:
            careplan['activity'] = activities
            self._careplan_metrics['careplans_with_activities'] += 1

        # Add notes if provided
        if 'notes' in data or 'note' in data:
            notes = data.get('notes', data.get('note', []))
            if isinstance(notes, str):
                notes = [notes]
            careplan['note'] = []
            for note_text in notes:
                careplan['note'].append({
                    'text': note_text,
                    'time': datetime.utcnow().isoformat() + 'Z'
                })

        # Update metrics
        self._careplan_metrics['total_careplans'] += 1
        if status == 'active':
            self._careplan_metrics['active_careplans'] += 1
        if 'goal' in careplan:
            self._careplan_metrics['careplans_with_goals'] += 1

        return careplan

    def _init_careplan_category_mapping(self):
        """Initialize care plan category mappings with SNOMED CT codes"""
        self.careplan_categories = {
            'assessment': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '386053000',
                    'display': 'Evaluation procedure'
                }],
                'text': 'Assessment and Evaluation'
            },
            'therapy': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '386056008',
                    'display': 'Therapeutic procedure'
                }],
                'text': 'Therapy Plan'
            },
            'education': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '311401005',
                    'display': 'Patient education'
                }],
                'text': 'Patient Education Plan'
            },
            'medication': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '385798007',
                    'display': 'Medication therapy management'
                }],
                'text': 'Medication Management Plan'
            },
            'diet': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '226078001',
                    'display': 'Dietary management'
                }],
                'text': 'Dietary Plan'
            },
            'exercise': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '226029000',
                    'display': 'Physical activity plan'
                }],
                'text': 'Exercise Plan'
            },
            'discharge': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '736366004',
                    'display': 'Discharge planning'
                }],
                'text': 'Discharge Plan'
            }
        }

    def _init_activity_kind_mapping(self):
        """Initialize activity kind mappings"""
        self.activity_kinds = {
            'appointment': 'Appointment',
            'communication': 'CommunicationRequest',
            'device': 'DeviceRequest',
            'medication': 'MedicationRequest',
            'nutrition': 'NutritionOrder',
            'task': 'Task',
            'procedure': 'ServiceRequest',
            'observation': 'ServiceRequest',
            'diagnostic': 'ServiceRequest',
            'supply': 'SupplyRequest',
            'vision': 'VisionPrescription'
        }

    def _determine_careplan_category(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine care plan category based on input data"""
        # Check explicit category
        if 'category' in data:
            category_key = data['category'].lower()
            if category_key in self.careplan_categories:
                return self.careplan_categories[category_key]
            # Return custom category if not in predefined list
            return {
                'text': data['category']
            }

        # Try to infer from title or description
        text_to_check = f"{data.get('title', '')} {data.get('description', '')}".lower()

        # Check for keywords
        if any(word in text_to_check for word in ['assess', 'evaluat', 'screen']):
            return self.careplan_categories['assessment']
        elif any(word in text_to_check for word in ['therap', 'treatment', 'rehabilitation']):
            return self.careplan_categories['therapy']
        elif any(word in text_to_check for word in ['educat', 'teach', 'instruct']):
            return self.careplan_categories['education']
        elif any(word in text_to_check for word in ['medicat', 'drug', 'prescription']):
            return self.careplan_categories['medication']
        elif any(word in text_to_check for word in ['diet', 'nutrition', 'meal']):
            return self.careplan_categories['diet']
        elif any(word in text_to_check for word in ['exercis', 'physical', 'activity']):
            return self.careplan_categories['exercise']
        elif any(word in text_to_check for word in ['discharge', 'transition']):
            return self.careplan_categories['discharge']

        # Default to assessment if no specific category found
        return self.careplan_categories['assessment']

    def _create_careplan_period(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create period for care plan"""
        period = {}

        # Handle various period input formats
        if 'period_start' in data:
            period['start'] = data['period_start']
        elif 'start_date' in data:
            period['start'] = data['start_date']
        elif 'created' not in data:
            # Default to current date if not specified
            period['start'] = datetime.utcnow().date().isoformat()

        if 'period_end' in data:
            period['end'] = data['period_end']
        elif 'end_date' in data:
            period['end'] = data['end_date']
        elif 'duration_days' in data and 'start' in period:
            # Calculate end date from duration
            start_date = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
            end_date = start_date + timedelta(days=int(data['duration_days']))
            period['end'] = end_date.date().isoformat()

        return period if period else None

    def _create_careplan_goals(self, data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Create goal references for care plan"""
        goals = []

        if 'goals' in data:
            goal_data = data['goals']
            if isinstance(goal_data, str):
                goal_data = [goal_data]

            for goal in goal_data:
                if isinstance(goal, str):
                    if '/' in goal:  # Already a reference
                        goals.append({'reference': goal})
                    else:
                        goals.append({'reference': f"Goal/{goal}"})
                elif isinstance(goal, dict):
                    # Handle structured goal data
                    goal_ref = {'reference': f"Goal/{goal.get('id', uuid.uuid4().hex[:8])}"}
                    if 'display' in goal or 'description' in goal:
                        goal_ref['display'] = goal.get('display', goal.get('description'))
                    goals.append(goal_ref)

        return goals if goals else None

    def _create_careplan_activities(self, data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Create activity components for care plan"""
        activities = []

        if 'activities' in data:
            activity_data = data['activities']
            if not isinstance(activity_data, list):
                activity_data = [activity_data]

            for activity in activity_data:
                if isinstance(activity, str):
                    # Simple activity description
                    activities.append({
                        'detail': {
                            'description': activity,
                            'status': 'not-started'
                        }
                    })
                elif isinstance(activity, dict):
                    # Structured activity data
                    activity_component = {}

                    # Add outcome code bindings if present
                    if 'outcome_codes' in activity:
                        activity_component['outcomeCodeableConcept'] = [
                            {'text': code} for code in activity['outcome_codes']
                        ]

                    # Add outcome references if present
                    if 'outcome_references' in activity:
                        activity_component['outcomeReference'] = [
                            {'reference': ref} for ref in activity['outcome_references']
                        ]

                    # Add progress notes if present
                    if 'progress' in activity:
                        activity_component['progress'] = [
                            {'text': activity['progress']}
                        ]

                    # Add reference to another resource if present
                    if 'reference' in activity:
                        activity_component['reference'] = {
                            'reference': activity['reference']
                        }

                    # Add activity detail
                    detail = {}

                    # Activity kind
                    if 'kind' in activity:
                        kind = activity['kind'].lower()
                        if kind in self.activity_kinds:
                            detail['kind'] = self.activity_kinds[kind]

                    # Activity code
                    if 'code' in activity:
                        detail['code'] = {'text': activity['code']}
                    elif 'name' in activity:
                        detail['code'] = {'text': activity['name']}

                    # Status (required)
                    detail['status'] = activity.get('status', 'not-started')

                    # Prohibited flag
                    if 'prohibited' in activity:
                        detail['doNotPerform'] = activity['prohibited']

                    # Scheduled timing
                    if 'scheduled_time' in activity:
                        detail['scheduledTiming'] = {
                            'event': [activity['scheduled_time']]
                        }
                    elif 'scheduled_period' in activity:
                        detail['scheduledPeriod'] = activity['scheduled_period']
                    elif 'frequency' in activity:
                        detail['scheduledTiming'] = {
                            'repeat': {
                                'frequency': activity['frequency'],
                                'period': 1,
                                'periodUnit': activity.get('period_unit', 'd')
                            }
                        }

                    # Location
                    if 'location' in activity:
                        detail['location'] = {
                            'reference': f"Location/{activity['location']}"
                        }

                    # Performers
                    if 'performer' in activity:
                        detail['performer'] = [
                            {'reference': f"Practitioner/{activity['performer']}"}
                        ]
                    elif 'performers' in activity:
                        detail['performer'] = [
                            {'reference': f"Practitioner/{p}"} for p in activity['performers']
                        ]

                    # Product reference (for medication/device activities)
                    if 'product_reference' in activity:
                        detail['productReference'] = {
                            'reference': activity['product_reference']
                        }
                    elif 'product_code' in activity:
                        detail['productCodeableConcept'] = {
                            'text': activity['product_code']
                        }

                    # Quantity
                    if 'quantity' in activity:
                        detail['quantity'] = {
                            'value': activity['quantity'],
                            'unit': activity.get('unit', 'unit')
                        }

                    # Description
                    if 'description' in activity:
                        detail['description'] = activity['description']

                    # Goal references for this activity
                    if 'goals' in activity:
                        detail['goal'] = [
                            {'reference': f"Goal/{g}"} for g in activity['goals']
                        ]

                    if detail:
                        activity_component['detail'] = detail

                    activities.append(activity_component)

        return activities if activities else None

    def _track_careplan_metrics(self, resource_type: str, duration_ms: float):
        """Track CarePlan-specific metrics"""
        # Update base class metrics
        self._metrics['created'] += 1
        self._metrics['total_time_ms'] += duration_ms
        if self._metrics['created'] > 0:
            self._metrics['avg_time_ms'] = self._metrics['total_time_ms'] / self._metrics['created']

    def get_careplan_statistics(self) -> Dict[str, Any]:
        """Get CarePlan factory statistics"""
        return {
            'supported_resources': len(self.SUPPORTED_RESOURCES),
            'careplan_metrics': self._careplan_metrics,
            'performance_metrics': self._metrics,
            'factory_type': 'CarePlanResourceFactory'
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on CarePlan factory"""
        try:
            # Test basic CarePlan creation
            test_data = {
                'patient_id': 'test-patient',
                'title': 'Health Check Test Plan',
                'status': 'draft'
            }

            start_time = time.time()
            test_resource = self._create_careplan(test_data, 'health-check')
            creation_time = (time.time() - start_time) * 1000

            return {
                'status': 'healthy',
                'supported_resources': len(self.SUPPORTED_RESOURCES),
                'creation_time_ms': round(creation_time, 2),
                'performance_ok': creation_time < 10.0,
                'careplan_categories': len(self.careplan_categories),
                'activity_kinds': len(self.activity_kinds),
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