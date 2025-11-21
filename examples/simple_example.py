"""
Simple example of using the Agentic Regression Testing Framework.

This example demonstrates:
1. Loading an application profile
2. Creating an orchestrator
3. Running discovery
4. Creating a test plan
5. Generating tests
6. Executing tests
7. Generating reports
"""

from models.app_profile import ApplicationProfile, AuthConfig, DiscoveryConfig, ApplicationType, TestFramework
from agents.orchestrator import OrchestratorAgent


def main():
    """Run simple regression testing example."""

    # Create a custom application profile
    app_profile = ApplicationProfile(
        name="example_web_app",
        app_type=ApplicationType.WEB,
        adapter="web_adapter",
        base_url="https://example.com",

        auth=AuthConfig(
            auth_type="none"
        ),

        discovery=DiscoveryConfig(
            enabled=True,
            url="https://example.com",
            max_depth=2,
            max_pages=10
        ),

        test_framework=TestFramework.PLAYWRIGHT,
        parallel_execution=False,
        headless=True,

        description="Example web application for testing"
    )

    print("=" * 80)
    print("Agentic AI Regression Testing Framework - Simple Example")
    print("=" * 80)

    # Initialize orchestrator with FULL_AUTO mode (no human approval)
    orchestrator = OrchestratorAgent(
        app_profile=app_profile,
        hitl_mode="FULL_AUTO"
    )

    print(f"\n✓ Orchestrator initialized for: {app_profile.name}")
    print(f"  HITL Mode: {orchestrator.hitl_mode}")

    # Option 1: Run complete workflow with single command
    print("\n" + "=" * 80)
    print("Running Full Automated Workflow")
    print("=" * 80 + "\n")

    result = orchestrator.run_full_workflow(
        feature_description="User login and authentication"
    )

    if result["success"]:
        print("\n✓ Workflow completed successfully!")
        print(f"\nOutput:\n{result['output']}")
    else:
        print(f"\n✗ Workflow failed: {result.get('error')}")

    # Option 2: Run step-by-step
    print("\n\n" + "=" * 80)
    print("Running Step-by-Step Workflow")
    print("=" * 80 + "\n")

    # Step 1: Discovery
    print("Step 1: Running Discovery...")
    discovery_result = orchestrator.discovery_agent.discover()
    print(f"  - Found {len(discovery_result.elements)} elements")
    print(f"  - Crawled {len(discovery_result.pages)} pages")

    # Step 2: Test Planning
    print("\nStep 2: Creating Test Plan...")
    test_plan = orchestrator.test_planner.create_plan(
        feature_description="Dashboard functionality",
        discovery_result=discovery_result
    )
    print(f"  - Created plan with {len(test_plan.get('test_cases', []))} test cases")

    # Step 3: Test Generation
    print("\nStep 3: Generating Test Scripts...")
    test_cases = orchestrator.test_generator.generate_tests(test_plan)
    print(f"  - Generated {len(test_cases)} test scripts")

    # Step 4: Test Execution
    print("\nStep 4: Executing Tests...")
    test_results = orchestrator.test_executor.execute_tests(test_cases)
    summary = orchestrator.test_executor.get_summary()
    print(f"  - Executed {summary['total']} tests")
    print(f"  - Passed: {summary['passed']}, Failed: {summary['failed']}")
    print(f"  - Pass Rate: {summary['pass_rate']}")

    # Step 5: Reporting
    print("\nStep 5: Generating Report...")
    report_path = orchestrator.reporting_agent.generate_report(
        test_results,
        format="html"
    )
    print(f"  - Report saved to: {report_path}")

    # Cleanup
    print("\nCleaning up...")
    orchestrator.cleanup()

    print("\n" + "=" * 80)
    print("Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
