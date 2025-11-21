"""
Demo Script: Complete Orchestrator V2 Workflow

This script demonstrates the complete end-to-end testing workflow using
the Orchestrator Agent V2, which coordinates all sub-agents:

1. Discovery Agent - Discovers application elements
2. Test Planner Agent - Creates comprehensive test plan
3. Test Generator Agent - Generates executable test scripts
4. Test Executor Agent - Executes tests and collects results
5. Reporting Agent - Generates beautiful test reports

Run this script to see the complete Agentic AI Testing Framework in action!
"""

import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
import tools.auto_register  # Auto-registers all 18 tools
from agents_v2 import OrchestratorAgentV2
from models.app_profile import ApplicationProfile, TestFramework, ApplicationType
from utils.logger import get_logger

logger = get_logger(__name__)


def print_banner(text: str, char: str = "="):
    """Print a formatted banner"""
    width = 80
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")


def print_section(text: str):
    """Print a section header"""
    print(f"\n{'─' * 80}")
    print(f"▶ {text}")
    print(f"{'─' * 80}")


def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"⚠️  {text}")


def create_demo_app_profile() -> ApplicationProfile:
    """Create a demo application profile"""
    print_section("Creating Application Profile")

    app_profile = ApplicationProfile(
        name="E-commerce Demo Application",
        base_url="https://demo-shop.example.com",
        app_type=ApplicationType.WEB,
        test_framework=TestFramework.PLAYWRIGHT,
        adapter="web",
        description="Demo e-commerce application for testing",
        parallel_execution=False,
        max_workers=2,
    )

    print_info(f"Application: {app_profile.name}")
    print_info(f"Base URL: {app_profile.base_url}")
    print_info(f"Framework: {app_profile.test_framework.value}")
    print_success("Application profile created")

    return app_profile


def run_orchestrator_demo():
    """Run the complete orchestrator workflow demo"""

    print_banner("🤖 ORCHESTRATOR AGENT V2 - COMPLETE WORKFLOW DEMO 🤖")

    print_info("This demo showcases the complete end-to-end testing workflow")
    print_info("coordinated by the Orchestrator Agent V2")
    print()

    # Step 1: Create Application Profile
    app_profile = create_demo_app_profile()

    # Step 2: Initialize Orchestrator
    print_section("Initializing Orchestrator Agent V2")

    try:
        orchestrator = OrchestratorAgentV2(
            app_profile=app_profile,
            output_dir="generated_tests",
            reports_dir="reports",
            enable_hitl=False,  # Disable HITL for automated demo
        )
        print_success("Orchestrator initialized successfully")
        print_info("Sub-agents loaded: Discovery, Planner, Generator, Executor, Reporter")
    except Exception as e:
        print_error(f"Failed to initialize orchestrator: {e}")
        return

    # Step 3: Run Complete Workflow
    print_section("Running Complete Workflow")

    feature_description = """
    User Authentication and Checkout Flow:
    - User registration and login
    - Browse product catalog
    - Add items to shopping cart
    - Checkout process
    - Payment processing
    - Order confirmation
    """

    print_info("Feature to test:")
    for line in feature_description.strip().split('\n'):
        print(f"  {line}")

    print()
    print_info("Starting workflow execution...")
    print_info("This will run all 5 sub-agents in sequence:")
    print_info("  1️⃣  Discovery Agent - Discover UI elements")
    print_info("  2️⃣  Test Planner Agent - Create test plan")
    print_info("  3️⃣  Test Generator Agent - Generate test scripts")
    print_info("  4️⃣  Test Executor Agent - Execute tests")
    print_info("  5️⃣  Reporting Agent - Generate reports")
    print()

    start_time = datetime.now()

    try:
        # Run the complete workflow
        final_state = orchestrator.run_full_workflow(
            feature_description=feature_description.strip(),
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Get workflow summary
        summary = orchestrator.get_workflow_summary(final_state)

        # Display Results
        print_section("Workflow Results")

        # Overall Status
        status = summary.get('status', 'unknown')
        if status == 'completed':
            print_success(f"Workflow Status: {status.upper()}")
        else:
            print_error(f"Workflow Status: {status.upper()}")
            if summary.get('error'):
                print_error(f"Error: {summary['error']}")

        print_info(f"Total Execution Time: {duration:.2f} seconds")

        completed_stages = summary.get('completed_stages', [])
        print_info(f"Completed Stages: {', '.join(completed_stages) if completed_stages else 'None'}")

        # Stage-by-Stage Results
        print_section("Stage-by-Stage Results")

        # 1. Discovery Results
        if 'discovery' in summary:
            print("\n1️⃣  DISCOVERY AGENT")
            discovery = summary['discovery']
            print_success(f"Elements Found: {discovery.get('elements_found', 0)}")
            print_success(f"Pages Found: {discovery.get('pages_found', 0)}")
        else:
            print("\n1️⃣  DISCOVERY AGENT")
            print_warning("Discovery stage not completed or no data available")

        # 2. Planning Results
        if 'planning' in summary:
            print("\n2️⃣  TEST PLANNER AGENT")
            planning = summary['planning']
            print_success(f"Test Cases Created: {planning.get('test_cases_created', 0)}")
        else:
            print("\n2️⃣  TEST PLANNER AGENT")
            print_warning("Planning stage not completed or no data available")

        # 3. Generation Results
        if 'generation' in summary:
            print("\n3️⃣  TEST GENERATOR AGENT")
            generation = summary['generation']
            print_success(f"Scripts Generated: {generation.get('scripts_generated', 0)}")
            print_success(f"Passed Validation: {generation.get('passed_validation', 0)}")
        else:
            print("\n3️⃣  TEST GENERATOR AGENT")
            print_warning("Generation stage not completed or no data available")

        # 4. Execution Results
        if 'execution' in summary:
            print("\n4️⃣  TEST EXECUTOR AGENT")
            execution = summary['execution']
            total = execution.get('total_tests', 0)
            passed = execution.get('passed', 0)
            failed = execution.get('failed', 0)

            print_success(f"Total Tests Executed: {total}")
            print_success(f"Tests Passed: {passed} ✅")

            if failed > 0:
                print_error(f"Tests Failed: {failed} ❌")
            else:
                print_success(f"Tests Failed: {failed}")

            if total > 0:
                pass_rate = (passed / total) * 100
                print_info(f"Pass Rate: {pass_rate:.1f}%")
        else:
            print("\n4️⃣  TEST EXECUTOR AGENT")
            print_warning("Execution stage not completed or no data available")

        # 5. Reporting Results
        if 'reporting' in summary:
            print("\n5️⃣  REPORTING AGENT")
            reporting = summary['reporting']
            reports_count = reporting.get('reports_generated', 0)
            formats = reporting.get('formats', [])

            print_success(f"Reports Generated: {reports_count}")
            if formats:
                print_info(f"Formats: {', '.join(formats)}")
        else:
            print("\n5️⃣  REPORTING AGENT")
            print_warning("Reporting stage not completed or no data available")

        # Detailed State Information
        print_section("Detailed State Information")

        # Show file locations
        if 'generation' in summary:
            print_info("Generated test scripts location: ./generated_tests/")

        if 'reporting' in summary:
            print_info("Test reports location: ./reports/")

        # Show final report if available
        final_report = final_state.get('final_report')
        if final_report and final_report.get('generated_reports'):
            print("\n📊 Generated Report Files:")
            for report in final_report['generated_reports']:
                if 'file_path' in report:
                    print(f"  • {report.get('format', 'unknown').upper()}: {report['file_path']}")

        # Success Summary
        print_section("Summary")

        if status == 'completed' and completed_stages:
            print_success("🎉 WORKFLOW COMPLETED SUCCESSFULLY! 🎉")
            print()
            print_info("The Orchestrator Agent V2 successfully coordinated all sub-agents")
            print_info("to discover, plan, generate, execute, and report on tests.")
            print()
            print_info("Key Achievements:")
            print(f"  ✅ {len(completed_stages)}/5 stages completed")
            print(f"  ✅ Executed in {duration:.2f} seconds")
            if 'execution' in summary:
                exec_summary = summary['execution']
                print(f"  ✅ {exec_summary.get('passed', 0)} tests passed")
            if 'reporting' in summary:
                report_summary = summary['reporting']
                print(f"  ✅ {report_summary.get('reports_generated', 0)} reports generated")
        else:
            print_warning("Workflow completed with issues")
            if summary.get('error'):
                print_error(f"Error: {summary['error']}")

        print()

    except Exception as e:
        print_error(f"Workflow execution failed: {e}")
        import traceback
        print(traceback.format_exc())
        return

    # Footer
    print_banner("🎊 DEMO COMPLETE 🎊", "=")
    print_info("Thank you for trying the Orchestrator Agent V2!")
    print_info("For more information, see: COMPLETE_REFACTORING_SUMMARY.md")
    print()


def show_tool_info():
    """Show information about registered tools"""
    print_section("Registered Tools Information")

    from tools.base import ToolRegistry

    tools = ToolRegistry.list_tools()
    print_info(f"Total Tools Registered: {len(tools)}")
    print()

    # Group tools by category
    categories = {}
    for tool in tools:
        tags = tool.tags
        category = tags[0] if tags else "other"
        if category not in categories:
            categories[category] = []
        categories[category].append(tool.name)

    for category, tool_names in sorted(categories.items()):
        print(f"📦 {category.upper()}: {len(tool_names)} tools")
        for name in sorted(tool_names):
            print(f"   • {name}")

    print()


def main():
    """Main entry point"""

    # Show tool information
    show_tool_info()

    # Run the demo
    run_orchestrator_demo()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
