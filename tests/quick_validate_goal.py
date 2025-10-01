#!/usr/bin/env python3
"""
Quick validation test for Goal implementation
Tests the new create_goal_resource adapter method
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_fhir.services.fhir.factory_adapter import get_factory_adapter

def test_goal_implementation():
    """Test Goal resource creation"""
    print("=" * 70)
    print("🧪 GOAL IMPLEMENTATION VALIDATION")
    print("=" * 70)

    factory = get_factory_adapter()
    factory.initialize()

    # Test 1: Basic Goal creation
    print("\n✅ Test 1: Basic Goal Creation")
    try:
        goal_data = {
            "description": "Achieve HbA1c less than 7%",
            "status": "active",
            "priority": "high"
        }

        result = factory.create_goal_resource(
            goal_data,
            "Patient/test-123",
            request_id="test-goal-001"
        )

        assert result["resourceType"] == "Goal"
        assert result["lifecycleStatus"] == "active"
        assert result["subject"]["reference"] == "Patient/test-123"
        assert "description" in result
        print(f"   ✅ Resource created: {result['id']}")
        print(f"   ✅ Status: {result['lifecycleStatus']}")
        print(f"   ✅ Description: {result['description']['text']}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 2: Goal with target and due date
    print("\n✅ Test 2: Goal with Target and Due Date")
    try:
        target_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

        goal_data = {
            "description": "Reduce body weight by 10 pounds",
            "status": "active",
            "priority": "medium",
            "category": "behavioral",
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
            "Patient/test-456"
        )

        assert result["resourceType"] == "Goal"
        assert "target" in result
        assert "category" in result
        print(f"   ✅ Goal with target created")
        print(f"   ✅ Category: {result['category'][0]['text']}")
        if isinstance(result["target"], list):
            print(f"   ✅ Target due date: {result['target'][0]['dueDate']}")
        else:
            print(f"   ✅ Target due date: {result['target']['dueDate']}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 3: Goal with CarePlan integration
    print("\n✅ Test 3: Goal with CarePlan Integration")
    try:
        # First create a CarePlan
        careplan_data = {
            "title": "Diabetes Management Plan",
            "status": "active",
            "intent": "plan"
        }

        careplan = factory.create_careplan_resource(
            careplan_data,
            "Patient/test-789"
        )

        # Now create Goal linked to CarePlan
        goal_data = {
            "description": "Maintain blood glucose 80-120 mg/dL",
            "status": "active",
            "priority": "high",
            "achievement_status": "in-progress"
        }

        goal = factory.create_goal_resource(
            goal_data,
            "Patient/test-789",
            careplan_ref=f"CarePlan/{careplan['id']}"
        )

        assert goal["resourceType"] == "Goal"
        assert "addresses" in goal
        print(f"   ✅ Goal linked to CarePlan")
        print(f"   ✅ CarePlan ref: CarePlan/{careplan['id']}")
        print(f"   ✅ Achievement status: {goal.get('achievementStatus', {}).get('text', 'N/A')}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Goal with multiple targets
    print("\n✅ Test 4: Goal with Multiple Targets")
    try:
        goal_data = {
            "description": "Blood pressure control",
            "status": "active",
            "priority": "high",
            "target": [
                {
                    "measure": "systolic-bp",
                    "detail_range": {
                        "low": {"value": 110, "unit": "mmHg"},
                        "high": {"value": 130, "unit": "mmHg"}
                    }
                },
                {
                    "measure": "diastolic-bp",
                    "detail_range": {
                        "low": {"value": 70, "unit": "mmHg"},
                        "high": {"value": 80, "unit": "mmHg"}
                    }
                }
            ]
        }

        result = factory.create_goal_resource(
            goal_data,
            "Patient/test-multi"
        )

        assert result["resourceType"] == "Goal"
        assert "target" in result
        assert isinstance(result["target"], list)
        assert len(result["target"]) == 2
        print(f"   ✅ Multiple targets created")
        print(f"   ✅ Target count: {len(result['target'])}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 5: Goal lifecycle statuses
    print("\n✅ Test 5: Goal Lifecycle Statuses")
    try:
        statuses = ["proposed", "active", "on-hold", "completed", "cancelled"]

        for status in statuses:
            goal_data = {
                "description": f"Goal in {status} status",
                "status": status,
                "priority": "medium"
            }

            goal = factory.create_goal_resource(
                goal_data,
                "Patient/status-test"
            )

            assert goal["resourceType"] == "Goal"
            assert status in goal["lifecycleStatus"].lower()

        print(f"   ✅ All lifecycle statuses working")
        print(f"   ✅ Tested: {', '.join(statuses)}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   ✅ Basic goal creation working")
    print("   ✅ Targets and due dates working")
    print("   ✅ CarePlan integration working")
    print("   ✅ Multiple targets working")
    print("   ✅ Lifecycle status management working")
    print("\n🎯 Next Step: Run full test suite")
    print("   Command: uv run pytest tests/epic_7/test_goal_resource.py -v")
    print("=" * 70)

    return True

if __name__ == "__main__":
    try:
        success = test_goal_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
