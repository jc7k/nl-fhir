#!/usr/bin/env python3
"""
Quick test to check if Goal and RelatedPerson factory methods exist
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_fhir.services.fhir.factory_adapter import get_factory_adapter

def test_factory_methods():
    """Test if factory methods exist"""
    print("=" * 70)
    print("🔍 EPIC 7 PHASE 1: Factory Method Availability Check")
    print("=" * 70)

    factory = get_factory_adapter()
    factory.initialize()

    # Test 1: Check if create_goal_resource exists
    print("\n📋 Test 1: Goal Resource Factory Method")
    try:
        if hasattr(factory, 'create_goal_resource'):
            print("✅ create_goal_resource() method EXISTS")
            # Try to call it
            try:
                goal_data = {
                    "description": "Test goal",
                    "status": "active",
                    "priority": "high"
                }
                goal = factory.create_goal_resource(goal_data, "Patient/test-123")
                print(f"✅ Goal resource created successfully: {goal['resourceType']}")
                print(f"   ID: {goal.get('id', 'N/A')}")
            except Exception as e:
                print(f"⚠️  Method exists but failed: {e}")
        else:
            print("❌ create_goal_resource() method NOT FOUND")
            print("   → Need to implement Goal resource factory")
    except Exception as e:
        print(f"❌ Error checking Goal: {e}")

    # Test 2: Check if create_related_person_resource exists
    print("\n👥 Test 2: RelatedPerson Resource Factory Method")
    try:
        if hasattr(factory, 'create_related_person_resource'):
            print("✅ create_related_person_resource() method EXISTS")
            # Try to call it
            try:
                related_data = {
                    "name": "Test Contact",
                    "relationship": "spouse",
                    "gender": "female"
                }
                related = factory.create_related_person_resource(related_data, "Patient/test-456")
                print(f"✅ RelatedPerson resource created successfully: {related['resourceType']}")
                print(f"   ID: {related.get('id', 'N/A')}")
                print(f"   Patient Ref: {related['patient']['reference']}")
            except Exception as e:
                print(f"⚠️  Method exists but failed: {e}")
        else:
            print("❌ create_related_person_resource() method NOT FOUND")
            print("   → Need to implement RelatedPerson resource factory")
    except Exception as e:
        print(f"❌ Error checking RelatedPerson: {e}")

    # Test 3: Check supported resources
    print("\n📊 Test 3: Factory Supported Resources")
    try:
        supported = factory.get_supported_resources()
        print(f"✅ Factory supports {len(supported)} resource types")

        # Check for our resources
        goal_supported = 'Goal' in supported
        related_supported = 'RelatedPerson' in supported

        print(f"   Goal: {'✅ SUPPORTED' if goal_supported else '❌ NOT in registry'}")
        print(f"   RelatedPerson: {'✅ SUPPORTED' if related_supported else '❌ NOT in registry'}")

    except Exception as e:
        print(f"⚠️  Could not get supported resources: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)

    goal_ready = hasattr(factory, 'create_goal_resource')
    related_ready = hasattr(factory, 'create_related_person_resource')

    if goal_ready and related_ready:
        print("✅ EXCELLENT: Both factory methods exist!")
        print("   Next step: Run full test suites for validation")
    elif related_ready and not goal_ready:
        print("🔶 PARTIAL: RelatedPerson exists, Goal needs implementation")
        print("   Next step: Implement create_goal_resource() method")
    elif goal_ready and not related_ready:
        print("🔶 PARTIAL: Goal exists, RelatedPerson needs implementation")
        print("   Next step: Implement create_related_person_resource() method")
    else:
        print("❌ NEEDS WORK: Both methods need implementation")
        print("   Next step: Implement both factory methods")

    print("=" * 70)

if __name__ == "__main__":
    try:
        test_factory_methods()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
