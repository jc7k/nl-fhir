"""
Task Workflow Service for Epic TW-001/TW-002
Detects workflow patterns and creates linked Task resources
HIPAA Compliant: No PHI logging, secure Task resource creation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from .nlp.entity_extractor import EntityType, MedicalEntity

logger = logging.getLogger(__name__)


class TaskWorkflowService:
    """Service for detecting workflow patterns and creating Task resources"""

    def __init__(self):
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize workflow detection service"""
        try:
            self.initialized = True
            logger.info("Task workflow service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize task workflow service: {e}")
            return False

    def detect_workflow_patterns(self, entities: List[MedicalEntity],
                                text: str, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Detect workflow patterns from extracted entities and create Task specifications

        Args:
            entities: List of extracted medical entities
            text: Original clinical text
            request_id: Request ID for logging

        Returns:
            List of Task specifications for creation
        """
        if not self.initialized:
            logger.warning(f"[{request_id}] Task workflow service not initialized")
            return []

        workflow_tasks = []

        # Find workflow entities
        workflow_entities = [e for e in entities if e.entity_type == EntityType.WORKFLOW]

        if workflow_entities:
            logger.info(f"[{request_id}] Found {len(workflow_entities)} workflow patterns")

            for workflow_entity in workflow_entities:
                # Analyze workflow pattern and create Task specification
                task_spec = self._analyze_workflow_pattern(workflow_entity, text, request_id)
                if task_spec:
                    workflow_tasks.append(task_spec)

        # Always check for implicit workflow patterns
        implicit_tasks = self._detect_implicit_workflow_patterns(entities, text, request_id)
        workflow_tasks.extend(implicit_tasks)

        logger.info(f"[{request_id}] Generated {len(workflow_tasks)} Task specifications")
        return workflow_tasks

    def _analyze_workflow_pattern(self, workflow_entity: MedicalEntity,
                                 text: str, request_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Analyze a specific workflow entity and create Task specification"""

        workflow_text = workflow_entity.text.lower()
        full_context = text[max(0, workflow_entity.start_char - 50):
                           min(len(text), workflow_entity.end_char + 50)]

        task_spec = {
            "description": f"Workflow task: {workflow_entity.text}",
            "status": "requested",
            "intent": "order",
            "priority": "routine",
            "workflow_type": None,
            "focus_type": None
        }

        # Assignment patterns
        if any(word in workflow_text for word in ["assign", "delegate", "refer", "send", "forward"]):
            task_spec["workflow_type"] = "assignment"
            task_spec["code"] = {
                "system": "http://hl7.org/fhir/CodeSystem/task-code",
                "code": "fulfill",
                "display": "Fulfill the focal request"
            }

            # Extract assignment target
            if "pharmacy" in full_context.lower():
                task_spec["description"] = "Assign medication review to pharmacy team"
                task_spec["focus_type"] = "MedicationRequest"
            elif "nurse" in full_context.lower() or "nursing" in full_context.lower():
                task_spec["description"] = "Assign care coordination to nursing team"
            elif "doctor" in full_context.lower() or "physician" in full_context.lower():
                task_spec["description"] = "Refer to physician for evaluation"

        # Scheduling patterns
        elif any(word in workflow_text for word in ["schedule", "book", "arrange", "plan"]):
            task_spec["workflow_type"] = "scheduling"
            task_spec["code"] = {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "TASK",
                "display": "Task"
            }

            if "follow-up" in full_context.lower():
                task_spec["description"] = "Schedule follow-up appointment"
            elif "education" in full_context.lower():
                task_spec["description"] = "Schedule patient education session"
            elif "consultation" in full_context.lower():
                task_spec["description"] = "Schedule consultation"

        # Monitoring patterns
        elif any(word in workflow_text for word in ["monitor", "track", "watch", "observe", "check"]):
            task_spec["workflow_type"] = "monitoring"
            task_spec["code"] = {
                "system": "http://snomed.info/sct",
                "code": "182836005",
                "display": "Review of medication"
            }
            task_spec["description"] = f"Monitor {self._extract_monitoring_target(full_context)}"
            task_spec["focus_type"] = "Observation"

        # Review patterns
        elif any(word in workflow_text for word in ["review", "evaluate", "assess", "analyze"]):
            task_spec["workflow_type"] = "review"
            task_spec["code"] = {
                "system": "http://snomed.info/sct",
                "code": "386053000",
                "display": "Evaluation procedure"
            }

            if "lab" in full_context.lower() or "result" in full_context.lower():
                task_spec["description"] = "Review lab results and contact patient with findings"
                task_spec["focus_type"] = "DiagnosticReport"
            else:
                task_spec["description"] = "Review clinical status and progress"

        return task_spec

    def _extract_monitoring_target(self, context: str) -> str:
        """Extract what should be monitored from context"""
        context_lower = context.lower()

        if "red man syndrome" in context_lower or "vancomycin" in context_lower:
            return "for red man syndrome"
        elif "blood pressure" in context_lower:
            return "blood pressure"
        elif "glucose" in context_lower:
            return "glucose levels"
        elif "vital signs" in context_lower:
            return "vital signs"
        elif "reaction" in context_lower:
            return "for adverse reactions"
        else:
            return "patient status"

    def _detect_implicit_workflow_patterns(self, entities: List[MedicalEntity],
                                         text: str, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect implicit workflow patterns that don't have explicit workflow entities"""
        implicit_tasks = []
        text_lower = text.lower()

        # High-risk medication patterns that imply monitoring tasks
        high_risk_patterns = [
            ("vancomycin", "Monitor for red man syndrome"),
            ("warfarin", "Monitor INR levels"),
            ("insulin", "Monitor blood glucose"),
            ("digoxin", "Monitor digoxin levels"),
            ("heparin", "Monitor PTT/aPTT")
        ]

        for medication, monitoring_task in high_risk_patterns:
            if medication in text_lower:
                implicit_tasks.append({
                    "description": monitoring_task,
                    "status": "requested",
                    "intent": "order",
                    "priority": "routine",
                    "workflow_type": "monitoring",
                    "focus_type": "MedicationRequest",
                    "code": {
                        "system": "http://snomed.info/sct",
                        "code": "182836005",
                        "display": "Review of medication"
                    }
                })

        # Lab orders that imply follow-up tasks
        if any(lab in text_lower for lab in ["cbc", "bmp", "cmp", "glucose", "creatinine"]):
            implicit_tasks.append({
                "description": "Review lab results and follow up with patient",
                "status": "requested",
                "intent": "order",
                "priority": "routine",
                "workflow_type": "review",
                "focus_type": "ServiceRequest",
                "code": {
                    "system": "http://snomed.info/sct",
                    "code": "386053000",
                    "display": "Evaluation procedure"
                }
            })

        if implicit_tasks:
            logger.info(f"[{request_id}] Generated {len(implicit_tasks)} implicit workflow tasks")

        return implicit_tasks

    def link_tasks_to_resources(self, task_specs: List[Dict[str, Any]],
                               resources: List[Dict[str, Any]],
                               request_id: Optional[str] = None) -> List[Tuple[Dict[str, Any], Optional[str]]]:
        """
        Link Task specifications to related FHIR resources

        Returns:
            List of tuples (task_spec, focus_reference)
        """
        linked_tasks = []

        for task_spec in task_specs:
            focus_ref = None
            focus_type = task_spec.get("focus_type")

            if focus_type:
                # Find matching resource by type
                for resource in resources:
                    if resource.get("resourceType") == focus_type:
                        focus_ref = f"{focus_type}/{resource.get('id')}"
                        break

            linked_tasks.append((task_spec, focus_ref))

            if focus_ref:
                logger.info(f"[{request_id}] Linked task '{task_spec['description']}' to {focus_ref}")
            else:
                logger.info(f"[{request_id}] Created standalone task '{task_spec['description']}'")

        return linked_tasks

    def determine_task_assignments(self, task_spec: Dict[str, Any],
                                  text: str, request_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Determine requester and owner for a task based on context

        Returns:
            Tuple of (requester_ref, owner_ref)
        """
        requester_ref = None
        owner_ref = None

        # For now, use simple defaults - could be enhanced with more sophisticated NLP
        workflow_type = task_spec.get("workflow_type")

        if workflow_type == "assignment":
            # Requester is typically the ordering provider
            requester_ref = "Practitioner/ordering-provider"

            # Owner depends on assignment target
            if "pharmacy" in task_spec["description"].lower():
                owner_ref = "Practitioner/pharmacist"
            elif "nurse" in task_spec["description"].lower():
                owner_ref = "Practitioner/nurse"
            elif "doctor" in task_spec["description"].lower():
                owner_ref = "Practitioner/physician"

        elif workflow_type in ["monitoring", "review"]:
            requester_ref = "Practitioner/ordering-provider"
            owner_ref = "Practitioner/nurse"  # Default to nursing for monitoring

        return requester_ref, owner_ref


# Global task workflow service instance
_task_workflow_service = None

async def get_task_workflow_service() -> TaskWorkflowService:
    """Get initialized task workflow service instance"""
    global _task_workflow_service

    if _task_workflow_service is None:
        _task_workflow_service = TaskWorkflowService()
        _task_workflow_service.initialize()

    return _task_workflow_service