"""
Agentic AI Regression Testing Framework - Main Entry Point

Usage:
    python main.py --app web_portal --feature "login functionality"
    python main.py --app oracle_ebs --discover-only
    python main.py --config custom_profile.yaml --hitl-mode INTERACTIVE
"""

import argparse
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from config.settings import get_settings
from config.llm_config import get_llm
from models.app_profile import ApplicationProfile
from agents.orchestrator import OrchestratorAgent
from utils.logger import get_logger, setup_logging
from utils.helpers import load_yaml

console = Console()
logger = get_logger(__name__)


def load_application_profile(app_name: str) -> ApplicationProfile:
    """
    Load application profile from config.

    Args:
        app_name: Name of the application profile

    Returns:
        ApplicationProfile object
    """
    profiles_path = Path("config/app_profiles.yaml")

    if not profiles_path.exists():
        raise FileNotFoundError("app_profiles.yaml not found")

    profiles_data = load_yaml(str(profiles_path))

    app_config = profiles_data.get("applications", {}).get(app_name)

    if not app_config:
        available = ", ".join(profiles_data.get("applications", {}).keys())
        raise ValueError(
            f"Application profile '{app_name}' not found. "
            f"Available profiles: {available}"
        )

    return ApplicationProfile(**app_config)


@click.group()
def cli():
    """Agentic AI Regression Testing Framework"""
    pass


@cli.command()
@click.option("--app", required=True, help="Application profile name")
@click.option("--feature", required=True, help="Feature description to test")
@click.option("--hitl-mode", default=None, help="HITL mode (FULL_AUTO, APPROVE_PLAN, etc.)")
@click.option("--output", default="reports", help="Output directory for reports")
def run(app: str, feature: str, hitl_mode: str, output: str):
    """Run complete regression testing workflow."""
    console.print(Panel(
        "[bold cyan]Agentic AI Regression Testing Framework[/bold cyan]\n"
        f"Application: [yellow]{app}[/yellow]\n"
        f"Feature: [yellow]{feature}[/yellow]",
        title="Starting Test Run",
        border_style="cyan"
    ))

    try:
        # Load application profile
        app_profile = load_application_profile(app)

        console.print(f"\n[green]✓[/green] Loaded profile: {app_profile.name}")

        # Initialize orchestrator
        orchestrator = OrchestratorAgent(app_profile, hitl_mode=hitl_mode)

        console.print(f"[green]✓[/green] Orchestrator initialized (HITL: {orchestrator.hitl_mode})\n")

        # Run full workflow
        console.print("[bold]Running full testing workflow...[/bold]\n")

        result = orchestrator.run_full_workflow(feature)

        if result.get("success"):
            console.print("\n[bold green]✓ Workflow completed successfully![/bold green]")
            console.print(f"\nOutput:\n{result.get('output', '')}")
        else:
            console.print("\n[bold red]✗ Workflow failed[/bold red]")
            console.print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)

        # Cleanup
        orchestrator.cleanup()

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}")
        logger.error(f"Execution error: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--app", required=True, help="Application profile name")
@click.option("--hitl-mode", default=None, help="HITL mode")
def discover(app: str, hitl_mode: str):
    """Run discovery only."""
    console.print(Panel(
        "[bold cyan]Discovery Mode[/bold cyan]\n"
        f"Application: [yellow]{app}[/yellow]",
        title="Starting Discovery",
        border_style="cyan"
    ))

    try:
        app_profile = load_application_profile(app)
        orchestrator = OrchestratorAgent(app_profile, hitl_mode=hitl_mode)

        result = orchestrator.run("Discover the application elements")

        if result.get("success"):
            console.print("\n[bold green]✓ Discovery completed![/bold green]")
            console.print(f"\n{result.get('output', '')}")
        else:
            console.print(f"\n[bold red]✗ Discovery failed:[/bold red] {result.get('error')}")

        orchestrator.cleanup()

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--app", required=True, help="Application profile name")
@click.option("--feature", required=True, help="Feature description")
@click.option("--hitl-mode", default="APPROVE_PLAN", help="HITL mode")
def plan(app: str, feature: str, hitl_mode: str):
    """Create test plan only."""
    console.print(Panel(
        "[bold cyan]Test Planning Mode[/bold cyan]\n"
        f"Application: [yellow]{app}[/yellow]\n"
        f"Feature: [yellow]{feature}[/yellow]",
        title="Creating Test Plan",
        border_style="cyan"
    ))

    try:
        app_profile = load_application_profile(app)
        orchestrator = OrchestratorAgent(app_profile, hitl_mode=hitl_mode)

        # Discover first
        console.print("\n[bold]Step 1: Discovery[/bold]")
        orchestrator.run("Discover the application")

        # Create plan
        console.print("\n[bold]Step 2: Test Planning[/bold]")
        result = orchestrator.run(f"Create a test plan for: {feature}")

        if result.get("success"):
            console.print("\n[bold green]✓ Test plan created![/bold green]")
            console.print(f"\n{result.get('output', '')}")
        else:
            console.print(f"\n[bold red]✗ Planning failed:[/bold red] {result.get('error')}")

        orchestrator.cleanup()

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
def list_apps():
    """List available application profiles."""
    console.print(Panel(
        "[bold cyan]Available Application Profiles[/bold cyan]",
        border_style="cyan"
    ))

    try:
        profiles_path = Path("config/app_profiles.yaml")

        if not profiles_path.exists():
            console.print("[yellow]No application profiles found[/yellow]")
            return

        profiles_data = load_yaml(str(profiles_path))

        applications = profiles_data.get("applications", {})

        if not applications:
            console.print("[yellow]No application profiles configured[/yellow]")
            return

        for app_name, app_config in applications.items():
            console.print(f"\n[bold cyan]{app_name}[/bold cyan]")
            console.print(f"  Type: {app_config.get('app_type', 'N/A')}")
            console.print(f"  Adapter: {app_config.get('adapter', 'N/A')}")
            console.print(f"  Description: {app_config.get('description', 'N/A')}")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}")


@cli.command()
def check():
    """Check framework configuration and dependencies."""
    console.print(Panel(
        "[bold cyan]Framework Configuration Check[/bold cyan]",
        border_style="cyan"
    ))

    try:
        settings = get_settings()

        console.print("\n[bold]Settings:[/bold]")
        console.print(f"  LLM Provider: [cyan]{settings.llm_provider}[/cyan]")
        console.print(f"  LLM Model: [cyan]{settings.llm_model}[/cyan]")
        console.print(f"  Vector Store: [cyan]{settings.vector_store}[/cyan]")
        console.print(f"  HITL Mode: [cyan]{settings.hitl_mode}[/cyan]")
        console.print(f"  Test Framework: [cyan]{settings.test_framework}[/cyan]")

        # Check API keys
        console.print("\n[bold]API Keys:[/bold]")
        if settings.openai_api_key:
            console.print("  OpenAI: [green]✓ Configured[/green]")
        else:
            console.print("  OpenAI: [yellow]✗ Not configured[/yellow]")

        if settings.anthropic_api_key:
            console.print("  Anthropic: [green]✓ Configured[/green]")
        else:
            console.print("  Anthropic: [yellow]✗ Not configured[/yellow]")

        # Test LLM connection
        console.print("\n[bold]Testing LLM connection...[/bold]")
        try:
            llm = get_llm()
            response = llm.invoke("Hello")
            console.print("  LLM Connection: [green]✓ Working[/green]")
        except Exception as e:
            console.print(f"  LLM Connection: [red]✗ Failed - {str(e)}[/red]")

        console.print("\n[green]✓ Configuration check complete[/green]")

    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    # Setup logging
    setup_logging()

    # Run CLI
    cli()
