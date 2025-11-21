"""
Demo: Individual Agent Usage

This demo shows how to use each agent independently without the orchestrator.
Useful when you only need specific parts of the workflow.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Auto-register all tools
import tools.auto_register

from agents_v2 import (
    DiscoveryAgentV2,
    TestPlannerAgentV2,
    TestGeneratorAgentV2,
    TestExecutorAgentV2,
    ReportingAgentV2,
)
from models.app_profile import ApplicationProfile, TestFramework, ApplicationType


def demo_discovery_agent():
    """Demo: Discovery Agent standalone usage"""
    print("\n" + "=" * 80)
    print("🔍 DEMO 1: Discovery Agent V2")
    print("=" * 80)

    app_profile = ApplicationProfile(
        name="Demo App",
        base_url="https://example.com",
        app_type=ApplicationType.WEB,
        test_framework=TestFramework.PLAYWRIGHT,
        adapter="web",
    )

    # Create discovery agent
    discovery_agent = DiscoveryAgentV2(app_profile=app_profile)

    print("\n📍 Running discovery...")
    discovery_state = discovery_agent.discover(app_profile=app_profile)

    print(f"✅ Status: {discovery_state.get('status')}")
    print(f"   Elements found: {len(discovery_state.get('elements', []))}")
    print(f"   Pages found: {len(discovery_state.get('pages', []))}")

    return discovery_state


def demo_test_planner_agent(discovery_state):
    """Demo: Test Planner Agent standalone usage"""
    print("\n" + "=" * 80)
    print("📋 DEMO 2: Test Planner Agent V2")
    print("=" * 80)

    app_profile = ApplicationProfile(
        name="Demo App",
        base_url="https://example.com",
        app_type=ApplicationType.WEB,
        test_framework=TestFramework.PLAYWRIGHT,
        adapter="web",
    )

    # Create test planner
    planner = TestPlannerAgentV2(app_profile=app_profile)

    print("\n📍 Creating test plan...")
    planning_state = planner.create_plan(
        app_profile=app_profile,
        feature_description="User authentication flow",
        discovery_result=discovery_state.get('discovery_result', {}),
    )

    print(f"✅ Status: {planning_state.get('status')}")
    print(f"   Test cases created: {len(planning_state.get('test_cases', []))}")

    # Show sample test case
    test_cases = planning_state.get('test_cases', [])
    if test_cases:
        print(f"\n   Sample test case:")
        sample = test_cases[0]
        print(f"   - Name: {sample.get('name', 'N/A')}")
        print(f"   - Priority: {sample.get('priority', 'N/A')}")

    return planning_state


def demo_test_generator_agent(planning_state):
    """Demo: Test Generator Agent standalone usage"""
    print("\n" + "=" * 80)
    print("⚙️  DEMO 3: Test Generator Agent V2")
    print("=" * 80)

    app_profile = ApplicationProfile(
        name="Demo App",
        base_url="https://example.com",
        app_type=ApplicationType.WEB,
        test_framework=TestFramework.PLAYWRIGHT,
        adapter="web",
    )

    # Create test generator
    generator = TestGeneratorAgentV2(
        app_profile=app_profile,
        output_dir="demo_tests",
    )

    print("\n📍 Generating test scripts...")
    generation_state = generator.generate_tests(
        test_cases=planning_state.get('test_cases', []),
    )

    print(f"✅ Status: {generation_state.get('status')}")
    print(f"   Scripts generated: {len(generation_state.get('generated_scripts', []))}")

    # Show sample script info
    scripts = generation_state.get('generated_scripts', [])
    if scripts:
        print(f"\n   Sample generated script:")
        sample = scripts[0]
        print(f"   - Filename: {sample.get('filename', 'N/A')}")
        print(f"   - File path: {sample.get('file_path', 'N/A')}")

    return generation_state


def demo_test_executor_agent(generation_state):
    """Demo: Test Executor Agent standalone usage"""
    print("\n" + "=" * 80)
    print("🧪 DEMO 4: Test Executor Agent V2")
    print("=" * 80)

    # Create test executor
    executor = TestExecutorAgentV2(framework="pytest")

    print("\n📍 Executing tests...")
    execution_state = executor.execute_tests(
        test_scripts=generation_state.get('generated_scripts', []),
    )

    print(f"✅ Status: {execution_state.get('status')}")
    print(f"   Tests executed: {len(execution_state.get('test_results', []))}")
    print(f"   Passed: {execution_state.get('passed_count', 0)}")
    print(f"   Failed: {execution_state.get('failed_count', 0)}")

    return execution_state


def demo_reporting_agent(execution_state):
    """Demo: Reporting Agent standalone usage"""
    print("\n" + "=" * 80)
    print("📊 DEMO 5: Reporting Agent V2")
    print("=" * 80)

    # Create reporting agent
    reporter = ReportingAgentV2(output_dir="demo_reports")

    print("\n📍 Generating reports...")
    reporting_state = reporter.generate_reports(
        test_results=execution_state.get('test_results', []),
        app_name="Demo Application",
        report_formats=["html", "json", "markdown"],
    )

    print(f"✅ Status: {reporting_state.get('status')}")
    print(f"   Reports generated: {len(reporting_state.get('generated_reports', []))}")

    # Show report files
    reports = reporting_state.get('generated_reports', [])
    if reports:
        print(f"\n   Generated report files:")
        for report in reports:
            if 'file_path' in report:
                print(f"   - {report.get('format', 'unknown').upper()}: {report['file_path']}")

    return reporting_state


def main():
    """Run all individual agent demos"""

    print("=" * 80)
    print("🎯 DEMO: Individual Agent Usage")
    print("=" * 80)
    print("\nThis demo shows how to use each agent independently.")
    print("Each agent can be used standalone for specific tasks.\n")

    try:
        # Run each demo in sequence
        discovery_state = demo_discovery_agent()
        planning_state = demo_test_planner_agent(discovery_state)
        generation_state = demo_test_generator_agent(planning_state)
        execution_state = demo_test_executor_agent(generation_state)
        reporting_state = demo_reporting_agent(execution_state)

        # Summary
        print("\n" + "=" * 80)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nKey Takeaways:")
        print("✅ Each agent can be used independently")
        print("✅ Agents communicate through state dictionaries")
        print("✅ Output from one agent feeds into the next")
        print("✅ Flexible workflow - use only what you need")
        print()

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        print(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
