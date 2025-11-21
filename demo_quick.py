"""
Quick Demo: Orchestrator V2 - Minimal Example

This is a simplified demo showing the bare minimum to run the complete workflow.
Perfect for quick testing and understanding the basic API.
"""

import sys
import os
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    # Set console to UTF-8
    os.system("chcp 65001 > nul")
    # Reconfigure stdout to UTF-8
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
    """Run quick demo"""

    print("=" * 80)
    print("🚀 QUICK DEMO: Orchestrator Agent V2")
    print("=" * 80)

    # 1. Create application profile
    print("\n📋 Step 1: Creating application profile...")
    app_profile = ApplicationProfile(
        name="Demo App",
        base_url="https://example.com",
        app_type=ApplicationType.WEB,
        test_framework=TestFramework.PLAYWRIGHT,
        adapter="web",
    )
    print(f"✅ Created profile for: {app_profile.name}")

    # 2. Initialize orchestrator
    print("\n🤖 Step 2: Initializing orchestrator...")
    orchestrator = OrchestratorAgentV2(
        app_profile=app_profile,
        output_dir="generated_tests",
        reports_dir="reports",
        enable_hitl=False,
    )
    print("✅ Orchestrator initialized with all 5 sub-agents")

    # 3. Run workflow
    print("\n⚙️  Step 3: Running complete workflow...")
    print("   (Discovery → Planning → Generation → Execution → Reporting)")

    final_state = orchestrator.run_full_workflow(
        feature_description="User login and authentication",
    )

    # 4. Show results
    print("\n📊 Step 4: Results")
    summary = orchestrator.get_workflow_summary(final_state)

    status = summary.get('status', 'unknown')
    print(f"   Status: {status.upper()}")
    print(f"   Completed: {', '.join(summary.get('completed_stages', []))}")

    duration = summary.get('total_execution_time')
    if duration is not None:
        print(f"   Duration: {duration:.2f}s")
    else:
        print(f"   Duration: N/A")

    if 'execution' in summary:
        exec_summary = summary['execution']
        print(f"   Tests Passed: {exec_summary.get('passed', 0)}")
        print(f"   Tests Failed: {exec_summary.get('failed', 0)}")

    if 'reporting' in summary:
        report_summary = summary['reporting']
        print(f"   Reports: {', '.join(report_summary.get('formats', []))}")

    print("\n" + "=" * 80)
    if status == 'completed':
        print("🎉 SUCCESS! Workflow completed successfully!")
    else:
        print("⚠️  Workflow completed with issues")
        if summary.get('error'):
            print(f"   Error: {summary['error']}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
