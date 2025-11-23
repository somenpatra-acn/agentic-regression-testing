"""
Interactive Test: GitHub Login Process

Tests the discovery and analysis of GitHub's login workflow.
"""

import sys
import os
from pathlib import Path
import json

# Fix Windows console encoding
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
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from models.app_profile import ApplicationProfile, TestFramework, ApplicationType

def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)

def print_section(title):
    """Print a section header"""
    print(f"\n{title}")
    print("-" * len(title))

def analyze_login_elements(elements):
    """Analyze discovered elements for login-related components"""

    login_related = {
        'inputs': [],
        'buttons': [],
        'links': [],
        'forms': [],
        'other': []
    }

    # Keywords that indicate login-related elements
    login_keywords = ['login', 'sign', 'user', 'email', 'password', 'auth', 'account']

    for element in elements:
        elem_type = element.get('type', '').lower()
        elem_text = element.get('text', '').lower()
        elem_selector = element.get('selector', '').lower()
        elem_attrs = str(element.get('attributes', {})).lower()

        # Check if element is login-related
        is_login_related = any(keyword in elem_text or keyword in elem_selector or keyword in elem_attrs
                               for keyword in login_keywords)

        if is_login_related:
            if 'input' in elem_type:
                login_related['inputs'].append(element)
            elif 'button' in elem_type:
                login_related['buttons'].append(element)
            elif 'link' in elem_type or 'a' in elem_type:
                login_related['links'].append(element)
            elif 'form' in elem_type:
                login_related['forms'].append(element)
            else:
                login_related['other'].append(element)

    return login_related

def main():
    """Run GitHub login test"""

    print_separator()
    print("🔐 INTERACTIVE TEST: GitHub Login Process")
    print_separator()

    print("\n📋 Test Configuration:")
    print("   Target: https://github.com/")
    print("   Focus: Login workflow discovery and analysis")
    print("   Method: Interactive discovery with detailed element analysis")

    # Create application profile for GitHub
    print("\n🎯 Step 1: Creating GitHub application profile...")

    app_profile = ApplicationProfile(
        name="GitHub",
        base_url="https://github.com/",
        app_type=ApplicationType.WEB,
        test_framework=TestFramework.PLAYWRIGHT,
        adapter="web",
    )

    # Configure discovery to focus on login areas
    app_profile.discovery.enabled = True
    app_profile.discovery.max_depth = 2
    app_profile.discovery.max_pages = 10

    print(f"✅ Profile created for: {app_profile.name}")
    print(f"   Base URL: {app_profile.base_url}")
    print(f"   Discovery depth: {app_profile.discovery.max_depth}")
    print(f"   Max pages: {app_profile.discovery.max_pages}")

    # Phase 1: Discovery
    print("\n" + "=" * 80)
    print("🔍 PHASE 1: DISCOVERY")
    print("=" * 80)
    print("\nDiscovering GitHub homepage and login elements...")
    print("This will:")
    print("  • Launch headless Chromium browser")
    print("  • Navigate to github.com")
    print("  • Extract all interactive elements")
    print("  • Follow links to discover login page")
    print("  • Identify form fields, buttons, and links")
    print()

    try:
        # Initialize discovery agent
        discovery_agent = DiscoveryAgentV2(app_profile=app_profile, enable_hitl=False)

        # Run discovery
        discovery_result = discovery_agent.discover(
            url="https://github.com/",
            max_depth=2,
            max_pages=10
        )

        status = discovery_result.get('status', 'unknown')
        elements = discovery_result.get('elements', [])
        pages = discovery_result.get('pages', [])

        print_section("📊 Discovery Results")
        print(f"Status: {status.upper()}")
        print(f"Total elements discovered: {len(elements)}")
        print(f"Pages crawled: {len(pages)}")

        if pages:
            print(f"\n📄 Pages Discovered:")
            for i, page in enumerate(pages[:10], 1):
                print(f"   {i}. {page}")
            if len(pages) > 10:
                print(f"   ... and {len(pages) - 10} more pages")

        if elements:
            # Analyze elements for login-related components
            print_section("🔐 Login-Related Element Analysis")

            login_elements = analyze_login_elements(elements)

            # Display input fields
            if login_elements['inputs']:
                print(f"\n📝 Input Fields ({len(login_elements['inputs'])}):")
                for inp in login_elements['inputs'][:5]:
                    elem_type = inp.get('attributes', {}).get('type', 'text')
                    elem_name = inp.get('attributes', {}).get('name', 'unnamed')
                    elem_id = inp.get('attributes', {}).get('id', '')
                    placeholder = inp.get('attributes', {}).get('placeholder', '')
                    print(f"   • Type: {elem_type}")
                    print(f"     Name: {elem_name}")
                    if elem_id:
                        print(f"     ID: {elem_id}")
                    if placeholder:
                        print(f"     Placeholder: {placeholder}")
                    print(f"     Selector: {inp.get('selector', 'N/A')[:60]}")
                    print()

            # Display buttons
            if login_elements['buttons']:
                print(f"🔘 Buttons ({len(login_elements['buttons'])}):")
                for btn in login_elements['buttons'][:5]:
                    text = btn.get('text', 'No text')
                    print(f"   • {text}")
                    print(f"     Selector: {btn.get('selector', 'N/A')[:60]}")
                    print()

            # Display links
            if login_elements['links']:
                print(f"🔗 Links ({len(login_elements['links'])}):")
                for link in login_elements['links'][:5]:
                    text = link.get('text', 'No text')
                    href = link.get('attributes', {}).get('href', '')
                    print(f"   • {text}")
                    if href:
                        print(f"     URL: {href[:60]}")
                    print()

            # Element type summary
            print_section("📈 Element Type Summary")
            element_types = {}
            for elem in elements:
                elem_type = elem.get('type', 'unknown')
                element_types[elem_type] = element_types.get(elem_type, 0) + 1

            for elem_type, count in sorted(element_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {elem_type}: {count}")

            # Generate test scenario suggestions
            print_section("🧪 Suggested Test Scenarios")

            has_email_input = any('email' in str(e.get('attributes', {})).lower() or
                                 'login' in str(e.get('attributes', {})).lower()
                                 for e in login_elements['inputs'])
            has_password_input = any('password' in str(e.get('attributes', {})).lower()
                                    for e in login_elements['inputs'])
            has_submit_button = any('sign' in e.get('text', '').lower() or
                                   'login' in e.get('text', '').lower()
                                   for e in login_elements['buttons'])

            scenarios = []
            if has_email_input and has_password_input and has_submit_button:
                scenarios.append("✅ Login with valid credentials")
                scenarios.append("✅ Login with invalid credentials")
                scenarios.append("✅ Login with empty fields")
                scenarios.append("✅ Password visibility toggle")
                scenarios.append("✅ Remember me functionality")

            if any('forgot' in e.get('text', '').lower() for e in login_elements['links']):
                scenarios.append("✅ Forgot password flow")

            if any('sign up' in e.get('text', '').lower() or 'create' in e.get('text', '').lower()
                   for e in login_elements['links'] + login_elements['buttons']):
                scenarios.append("✅ Sign up flow")

            if scenarios:
                print("\nBased on discovered elements, these test scenarios are recommended:")
                for scenario in scenarios:
                    print(f"   {scenario}")
            else:
                print("\n⚠️  Unable to identify complete login flow elements")
                print("   Discovery may need to navigate to /login page directly")

        else:
            print("\n⚠️  No elements discovered. Check if the page loaded correctly.")

        # Save detailed results
        print_section("💾 Saving Results")

        output_dir = Path("test_results")
        output_dir.mkdir(exist_ok=True)

        # Save full discovery data
        output_file = output_dir / "github_login_discovery.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'status': status,
                'total_elements': len(elements),
                'total_pages': len(pages),
                'pages': pages,
                'elements': elements,
                'login_elements': {
                    'inputs': login_elements['inputs'],
                    'buttons': login_elements['buttons'],
                    'links': login_elements['links'],
                }
            }, f, indent=2, default=str)

        print(f"✅ Full results saved to: {output_file}")

        # Phase 2: Try full workflow (will likely fail on API key)
        print("\n" + "=" * 80)
        print("🤖 PHASE 2: ATTEMPTING FULL WORKFLOW")
        print("=" * 80)
        print("\nAttempting to generate test plan with LLM...")
        print("(This may fail if Anthropic API key is not configured)")
        print()

        orchestrator = OrchestratorAgentV2(
            app_profile=app_profile,
            output_dir="generated_tests/github",
            reports_dir="reports/github",
            enable_hitl=False,
        )

        final_state = orchestrator.run_full_workflow(
            feature_description="GitHub login functionality - test login form, validation, and authentication flow"
        )

        summary = orchestrator.get_workflow_summary(final_state)

        print_section("📊 Workflow Summary")
        print(f"Status: {summary.get('status', 'unknown').upper()}")
        print(f"Completed stages: {', '.join(summary.get('completed_stages', []))}")

        if summary.get('error'):
            print(f"\n⚠️  Error: {summary['error']}")
            print("\nℹ️  Note: If you see authentication errors, add a valid Anthropic API key to .env")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return 1

    # Final summary
    print("\n" + "=" * 80)
    print("✅ INTERACTIVE TEST COMPLETE")
    print("=" * 80)
    print("\n📝 Summary:")
    print(f"   • Discovered {len(elements)} elements from GitHub")
    print(f"   • Identified {len(login_elements['inputs'])} login-related input fields")
    print(f"   • Found {len(login_elements['buttons'])} interactive buttons")
    print(f"   • Detected {len(login_elements['links'])} navigation links")
    print(f"\n✅ Discovery phase completed successfully!")
    print(f"📄 Detailed results saved to: test_results/github_login_discovery.json")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
