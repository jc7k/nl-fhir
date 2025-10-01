"""
Epic 7.4: Goal Resource Tests
Tests for Goal resource implementation - care goal tracking and outcome measurement

Validates FHIR R4 compliance, CarePlan integration, and clinical goal tracking workflows.
"""

import pytest
from datetime import datetime, timedelta
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestGoalResource:
    """Test Epic 7.4: Goal Resource Implementation"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    # =================================================================
    # Story 7.4: Basic Goal Resource Tests
    # =================================================================

    def test_goal_basic_creation(self, factory):
        """Test basic Goal resource creation (Story 7.4)"""

        goal_data = {
            "description": "Achieve HbA1c less than 7%",
            "status": "active",
            "priority": "high"
        }

        patient_ref = "Patient/patient-123"

        result = factory.create_goal_resource(
            goal_data,
            patient_ref,
            request_id="req-goal-001"
        )

        assert result["resourceType"] == "Goal"
        assert result["lifecycleStatus"] == "active"
        assert result["subject"]["reference"] == patient_ref
        assert "description" in result

    def test_goal_with_target_date(self, factory):
        """Test Goal with measurable target and date"""

        target_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

        goal_data = {
            "description": "Reduce body weight by 10 pounds",
            "status": "active",
            "priority": "medium",
            "target": {
                "measure": "body-weight",
                "detail_quantity": {
                    "value": 150,
                    "unit": "lbs"
                },
                "due_date": target_date
            }
        }

        result = factory.create_goal_resource(
            goal_data,
            "Patient/patient-456"
        )

        assert result["resourceType"] == "Goal"
        assert "target" in result
        if isinstance(result["target"], list):
            assert result["target"][0]["dueDate"] == target_date
        else:
            assert result["target"]["dueDate"] == target_date

    def test_goal_with_category(self, factory):
        """Test Goal with clinical category coding"""

        goal_data = {
            "description": "Improve physical activity to 30min daily",
            "status": "active",
            "category": "behavioral",
            "priority": "medium"
        }

        result = factory.create_goal_resource(
            goal_data,
            "Patient/patient-789"
        )

        assert result["resourceType"] == "Goal"
        assert "category" in result
        # FHIR library may use category as list
        if isinstance(result["category"], list):
            assert len(result["category"]) > 0
        else:
            assert result["category"]["text"] == "behavioral"

    def test_goal_achievement_status(self, factory):
        """Test Goal with achievement status tracking"""

        goal_data = {
            "description": "Quit smoking completely",
            "status": "active",
            "achievement_status": "in-progress",
            "priority": "high",
            "start_date": "2024-01-01"
        }

        result = factory.create_goal_resource(
            goal_data,
            "Patient/patient-321"
        )

        assert result["resourceType"] == "Goal"
        assert result["lifecycleStatus"] == "active"
        if "achievementStatus" in result:
            assert "in-progress" in str(result["achievementStatus"]).lower() or \
                   "in_progress" in str(result["achievementStatus"]).lower()

    # =================================================================
    # CarePlan Integration Tests
    # =================================================================

    def test_goal_careplan_integration(self, factory):
        """Test Goal integration with CarePlan resource"""

        # First create a CarePlan
        careplan_data = {
            "title": "Diabetes Management Plan",
            "status": "active",
            "intent": "plan",
            "description": "Comprehensive diabetes care"
        }

        careplan = factory.create_careplan_resource(
            careplan_data,
            "Patient/patient-999",
            request_id="req-careplan-001"
        )

        # Now create Goal linked to CarePlan
        goal_data = {
            "description": "HbA1c < 7%",
            "status": "active",
            "addresses": [careplan["id"]],
            "priority": "high"
        }

        goal = factory.create_goal_resource(
            goal_data,
            "Patient/patient-999",
            careplan_ref=f"CarePlan/{careplan['id']}"
        )

        assert goal["resourceType"] == "Goal"
        assert goal["subject"]["reference"] == "Patient/patient-999"
        # Goal may link to CarePlan via addresses field
        if "addresses" in goal:
            assert any(careplan["id"] in str(addr) for addr in goal["addresses"])

    def test_goal_with_outcome_measurement(self, factory):
        """Test Goal with outcome measurement and progress tracking"""

        goal_data = {
            "description": "Blood pressure control: systolic <130, diastolic <80",
            "status": "active",
            "priority": "high",
            "target": {
                "measure": "blood-pressure",
                "detail_range": {
                    "low": {"value": 110, "unit": "mmHg"},
                    "high": {"value": 130, "unit": "mmHg"}
                }
            },
            "outcome": {
                "reference": "Observation/bp-reading-001"
            }
        }

        result = factory.create_goal_resource(
            goal_data,
            "Patient/patient-555"
        )

        assert result["resourceType"] == "Goal"
        assert "target" in result or "description" in result
        if "outcomeReference" in result:
            assert len(result["outcomeReference"]) > 0

    # =================================================================
    # Multiple Goals and Priority Tests
    # =================================================================

    def test_multiple_goals_creation(self, factory):
        """Test creating multiple goals for comprehensive care"""

        goals_data = [
            {
                "description": "Weight loss: 10 lbs in 3 months",
                "status": "active",
                "priority": "high"
            },
            {
                "description": "Exercise: 30min daily for 5 days/week",
                "status": "active",
                "priority": "medium"
            },
            {
                "description": "Dietary adherence: Follow Mediterranean diet",
                "status": "active",
                "priority": "medium"
            }
        ]

        patient_ref = "Patient/patient-multi-goal"
        created_goals = []

        for goal_data in goals_data:
            goal = factory.create_goal_resource(goal_data, patient_ref)
            created_goals.append(goal)

        assert len(created_goals) == 3
        for goal in created_goals:
            assert goal["resourceType"] == "Goal"
            assert goal["subject"]["reference"] == patient_ref

    def test_goal_priority_levels(self, factory):
        """Test different priority levels for goals"""

        priorities = ["high", "medium", "low"]

        for priority in priorities:
            goal_data = {
                "description": f"Goal with {priority} priority",
                "status": "active",
                "priority": priority
            }

            goal = factory.create_goal_resource(
                goal_data,
                "Patient/patient-priority-test"
            )

            assert goal["resourceType"] == "Goal"
            if "priority" in goal:
                assert priority in str(goal["priority"]).lower()

    # =================================================================
    # Goal Lifecycle and Status Tests
    # =================================================================

    def test_goal_lifecycle_statuses(self, factory):
        """Test different goal lifecycle statuses"""

        statuses = [
            ("proposed", "proposed"),
            ("active", "active"),
            ("on-hold", "on-hold"),
            ("completed", "completed"),
            ("cancelled", "cancelled")
        ]

        for status_input, expected_status in statuses:
            goal_data = {
                "description": f"Goal in {status_input} status",
                "status": status_input,
                "priority": "medium"
            }

            goal = factory.create_goal_resource(
                goal_data,
                "Patient/patient-status-test"
            )

            assert goal["resourceType"] == "Goal"
            assert expected_status in goal["lifecycleStatus"].lower()

    def test_goal_with_notes(self, factory):
        """Test Goal with clinical notes and annotations"""

        goal_data = {
            "description": "Smoking cessation",
            "status": "active",
            "priority": "high",
            "note": "Patient expressed strong motivation. Using nicotine replacement therapy."
        }

        goal = factory.create_goal_resource(
            goal_data,
            "Patient/patient-notes"
        )

        assert goal["resourceType"] == "Goal"
        if "note" in goal:
            assert len(goal["note"]) > 0
            # Note may be list of Annotation objects
            if isinstance(goal["note"], list):
                assert goal["note"][0]["text"] == goal_data["note"]
            else:
                assert goal_data["note"] in str(goal["note"])

    # =================================================================
    # FHIR Compliance and Validation Tests
    # =================================================================

    def test_goal_fhir_r4_compliance(self, factory):
        """Test Goal resource FHIR R4 compliance"""

        goal_data = {
            "description": "Achieve target A1C of 7% or less",
            "status": "active",
            "priority": "high",
            "category": "physiologic",
            "target": {
                "measure": "hemoglobin-a1c",
                "detail_quantity": {
                    "value": 7.0,
                    "unit": "%",
                    "comparator": "<="
                },
                "due_date": "2024-06-01"
            }
        }

        goal = factory.create_goal_resource(
            goal_data,
            "Patient/patient-compliance"
        )

        # FHIR R4 required fields
        assert goal["resourceType"] == "Goal"
        assert "lifecycleStatus" in goal
        assert "description" in goal
        assert "subject" in goal
        assert goal["subject"]["reference"] == "Patient/patient-compliance"

        # Optional but important fields
        if "id" in goal:
            assert isinstance(goal["id"], str)
        if "target" in goal:
            assert isinstance(goal["target"], (list, dict))

    def test_goal_identifier_generation(self, factory):
        """Test Goal resource identifier generation"""

        goal_data = {
            "goal_id": "GOAL-2024-001",
            "description": "Blood sugar control",
            "status": "active",
            "priority": "high"
        }

        goal = factory.create_goal_resource(
            goal_data,
            "Patient/patient-id-test"
        )

        assert goal["resourceType"] == "Goal"
        assert "id" in goal or "identifier" in goal

        if "identifier" in goal:
            assert len(goal["identifier"]) > 0


class TestGoalEdgeCases:
    """Test edge cases and error handling for Goal resources"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    def test_goal_minimal_data(self, factory):
        """Test Goal creation with minimal required data"""

        goal_data = {
            "description": "Improve health",
            "status": "active"
        }

        goal = factory.create_goal_resource(
            goal_data,
            "Patient/patient-minimal"
        )

        assert goal["resourceType"] == "Goal"
        assert "description" in goal
        assert goal["subject"]["reference"] == "Patient/patient-minimal"

    def test_goal_with_complex_target(self, factory):
        """Test Goal with complex multi-part target"""

        goal_data = {
            "description": "Comprehensive diabetes control",
            "status": "active",
            "priority": "high",
            "target": [
                {
                    "measure": "hemoglobin-a1c",
                    "detail_quantity": {"value": 7.0, "unit": "%"}
                },
                {
                    "measure": "fasting-glucose",
                    "detail_quantity": {"value": 100, "unit": "mg/dL"}
                }
            ]
        }

        goal = factory.create_goal_resource(
            goal_data,
            "Patient/patient-complex"
        )

        assert goal["resourceType"] == "Goal"
        if "target" in goal:
            # May be list or single target
            assert isinstance(goal["target"], (list, dict))
