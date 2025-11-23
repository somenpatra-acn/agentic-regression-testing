"""
Live Test: Complete Workflow with Real Website

This tests the entire framework with a real publicly accessible website.
"""

import sys
import os
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Auto-register all tools
import tools.auto_register

from agents_v2 import OrchestratorAgentV2
from models.app_profile import ApplicationProfile, TestFramework, ApplicationType

def main():
    """Run live test with real website"""

    print("=" * 80)
    print("🧪 LIVE TEST: Complete Workflow with Real Website")
    print("=" * 80)

    # Use a simple, publicly accessible demo website
    print("\n📋 Step 1: Creating application profile for demo site...")
    app_profile = ApplicationProfile(
        name="Demo TodoMVC App",
        base_url="https://todomvc.com/examples/react/dist/",
        app_type=ApplicationType.WEB,
        test_framework=TestFramework.PLAYWRIGHT,
        adapter="web",
    )

    # Configure discovery settings (limit crawling to be respectful)
    app_profile.discovery.enabled = True
    app_profile.discovery.max_depth = 2
    app_profile.discovery.max_pages = 5

    print(f"✅ Created profile for: {app_profile.name}")
    print(f"   URL: {app_profile.base_url}")
    print(f"   Max depth: {app_profile.discovery.max_depth}")
    print(f"   Max pages: {app_profile.discovery.max_pages}")

    # Initialize orchestrator
    print("\n🤖 Step 2: Initializing orchestrator...")
    orchestrator = OrchestratorAgentV2(
        app_profile=app_profile,
        output_dir="generated_tests",
        reports_dir="reports",
        enable_hitl=False,
    )
    print("✅ Orchestrator initialized with all 5 sub-agents")

    # Run workflow
    print("\n⚙️  Step 3: Running complete workflow...")
    print("   This will:")
    print("   1. 🔍 Discover UI elements from the TodoMVC app")
    print("   2. 📋 Generate test plan based on discovered elements")
    print("   3. 📝 Generate test scripts using Playwright")
    print("   4. 🧪 Execute the generated tests")
    print("   5. 📊 Generate test reports")
    print()

    try:
        final_state = orchestrator.run_full_workflow(
            feature_description="Todo list functionality - add, complete, and delete todos"
        )

        # Show detailed results
        print("\n" + "=" * 80)
        print("📊 RESULTS")
        print("=" * 80)

        summary = orchestrator.get_workflow_summary(final_state)

        status = summary.get('status', 'unknown')
        print(f"\n✨ Overall Status: {status.upper()}")

        # Completed stages
        completed = summary.get('completed_stages', [])
        if completed:
            print(f"\n✅ Completed Stages: {', '.join(completed)}")

        # Duration
        duration = summary.get('total_execution_time')
        if duration is not None:
            print(f"⏱️  Total Duration: {duration:.2f}s")

        # Discovery results
        if 'discovery' in summary:
            disc = summary['discovery']
            print(f"\n🔍 Discovery:")
            print(f"   - Elements found: {disc.get('total_elements', 0)}")
            print(f"   - Pages crawled: {disc.get('total_pages', 0)}")
            if disc.get('element_types'):
                print(f"   - Element types: {disc['element_types']}")

        # Planning results
        if 'planning' in summary:
            plan = summary['planning']
            print(f"\n📋 Test Planning:")
            print(f"   - Test cases created: {plan.get('test_cases_count', 0)}")
            if plan.get('test_cases'):
                print(f"   - Test case details:")
                for i, tc in enumerate(plan['test_cases'][:3], 1):
                    print(f"      {i}. {tc.get('name', 'Unnamed test')}")
                if len(plan['test_cases']) > 3:
                    print(f"      ... and {len(plan['test_cases']) - 3} more")

        # Generation results
        if 'generation' in summary:
            gen = summary['generation']
            print(f"\n📝 Test Generation:")
            print(f"   - Scripts generated: {gen.get('scripts_generated', 0)}")
            if gen.get('scripts'):
                print(f"   - Generated files:")
                for script in gen['scripts'][:3]:
                    print(f"      - {script.get('filename', 'unknown')}")

        # Execution results
        if 'execution' in summary:
            exec_summary = summary['execution']
            print(f"\n🧪 Test Execution:")
            print(f"   - Tests Passed: {exec_summary.get('passed', 0)}")
            print(f"   - Tests Failed: {exec_summary.get('failed', 0)}")
            print(f"   - Tests Skipped: {exec_summary.get('skipped', 0)}")
            if exec_summary.get('execution_time'):
                print(f"   - Execution time: {exec_summary['execution_time']:.2f}s")

        # Reporting results
        if 'reporting' in summary:
            report_summary = summary['reporting']
            print(f"\n📊 Reports Generated:")
            formats = report_summary.get('formats', [])
            if formats:
                print(f"   - Formats: {', '.join(formats)}")
            if report_summary.get('report_paths'):
                print(f"   - Report locations:")
                for path in report_summary['report_paths']:
                    print(f"      - {path}")

        # Errors
        if summary.get('error'):
            print(f"\n⚠️  Error occurred: {summary['error']}")

        print("\n" + "=" * 80)
        if status == 'completed':
            print("🎉 SUCCESS! Complete workflow executed successfully!")
        else:
            print("⚠️  Workflow completed with some issues (see details above)")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
