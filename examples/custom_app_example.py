"""
Example of testing a custom application with the framework.

This demonstrates how to:
1. Create a custom adapter
2. Register it with the framework
3. Use HITL (Human-in-the-Loop) features
4. Collect feedback
"""

from models.app_profile import (
    ApplicationProfile,
    AuthConfig,
    DiscoveryConfig,
    ApplicationType,
    TestFramework
)
from adapters import register_adapter
from adapters.custom_adapter import CustomAdapter
from agents.orchestrator import OrchestratorAgent


class MyCustomAppAdapter(CustomAdapter):
    """Custom adapter for my specific application."""

    def authenticate(self) -> bool:
        """Custom authentication logic."""
        print(f"  Authenticating with {self.name}...")
        # Implement your authentication here
        return True

    def discover_elements(self):
        """Custom discovery logic."""
        print(f"  Discovering elements in {self.name}...")
        from adapters.base_adapter import DiscoveryResult, Element

        result = DiscoveryResult()

        # Add discovered elements
        result.elements.append(Element(
            id="custom_button_1",
            type="button",
            name="Submit Button",
            attributes={"id": "submit-btn"}
        ))

        result.elements.append(Element(
            id="custom_form_1",
            type="form",
            name="Main Form",
            attributes={"id": "main-form"}
        ))

        return result


def main():
    """Run custom application testing example."""

    print("=" * 80)
    print("Custom Application Testing Example")
    print("=" * 80)

    # Register custom adapter
    register_adapter("my_custom_adapter", MyCustomAppAdapter)
    print("\n✓ Registered custom adapter: my_custom_adapter")

    # Create application profile for custom app
    app_profile = ApplicationProfile(
        name="my_custom_app",
        app_type=ApplicationType.CUSTOM,
        adapter="my_custom_adapter",  # Use our custom adapter
        base_url="https://mycustomapp.com",

        auth=AuthConfig(
            auth_type="custom",
            username="test_user",
            password="test_pass"
        ),

        discovery=DiscoveryConfig(
            enabled=True,
            max_depth=3
        ),

        test_framework=TestFramework.PLAYWRIGHT,

        modules=["module_a", "module_b"],
        features=["feature_1", "feature_2"],

        custom_config={
            "custom_setting_1": "value1",
            "custom_setting_2": "value2",
        },

        description="My custom application"
    )

    print(f"✓ Created profile: {app_profile.name}")

    # Initialize orchestrator with INTERACTIVE mode
    # This will prompt for human approval at each step
    orchestrator = OrchestratorAgent(
        app_profile=app_profile,
        hitl_mode="APPROVE_PLAN"  # Approve test plans only
    )

    print(f"✓ Orchestrator initialized with HITL mode: {orchestrator.hitl_mode}\n")

    # Run workflow
    print("Starting test workflow with human approval...\n")

    # The framework will now:
    # 1. Use your custom adapter for discovery
    # 2. Create a test plan and wait for your approval
    # 3. Generate and execute tests
    # 4. Generate reports

    result = orchestrator.run("""
    Please test the following feature of my custom application:
    - Feature: User registration workflow
    - Include: form validation, success/error scenarios
    - Priority: High

    Steps:
    1. Discover the application
    2. Create a test plan (will require approval)
    3. Generate test scripts
    4. Execute tests
    5. Generate report
    """)

    if result["success"]:
        print("\n✓ Workflow completed!")
        print(f"\nResult:\n{result['output']}")
    else:
        print(f"\n✗ Workflow failed: {result.get('error')}")

    # Cleanup
    orchestrator.cleanup()

    print("\n" + "=" * 80)
    print("Custom Application Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
