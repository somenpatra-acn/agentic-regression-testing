"""Review interfaces for human interaction."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.syntax import Syntax
from rich.table import Table

from models.approval import Approval
from models.test_result import TestResult
from utils.logger import get_logger

logger = get_logger(__name__)


class ReviewInterface(ABC):
    """Base interface for human review."""

    @abstractmethod
    def review_approval(self, approval: Approval) -> Dict[str, Any]:
        """
        Review an approval request.

        Args:
            approval: Approval to review

        Returns:
            Dictionary with decision details
        """
        pass

    @abstractmethod
    def collect_feedback(
        self,
        test_result: TestResult,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        Collect feedback on a test result.

        Args:
            test_result: Test result
            prompt: Feedback prompt

        Returns:
            Feedback data dictionary or None
        """
        pass


class CLIReviewer(ReviewInterface):
    """CLI-based review interface using Rich."""

    def __init__(self):
        """Initialize CLI reviewer."""
        self.console = Console()

    def review_approval(self, approval: Approval) -> Dict[str, Any]:
        """Review an approval request via CLI."""
        self.console.print("\n" + "="*80)
        self.console.print(
            Panel(
                f"[bold cyan]Approval Request[/bold cyan]\n\n"
                f"Type: [yellow]{approval.approval_type.value}[/yellow]\n"
                f"Item: [yellow]{approval.item_id}[/yellow]\n"
                f"Timeout: [yellow]{approval.time_remaining()}s remaining[/yellow]",
                title="Human Review Required",
                border_style="cyan"
            )
        )

        # Display summary
        self.console.print(f"\n[bold]Summary:[/bold] {approval.item_summary}\n")

        # Display item data
        if approval.item_data:
            self._display_item_data(approval.item_data, approval.approval_type.value)

        # Get decision
        self.console.print("\n[bold]Options:[/bold]")
        self.console.print("  1. Approve")
        self.console.print("  2. Reject")
        self.console.print("  3. Approve with modifications")

        choice = IntPrompt.ask(
            "Your decision",
            choices=["1", "2", "3"],
            default="1"
        )

        decision = {"approver": Prompt.ask("Your name", default="human")}

        if choice == 1:
            decision["action"] = "approve"
            comments = Prompt.ask("Comments (optional)", default="")
            if comments:
                decision["comments"] = comments

        elif choice == 2:
            decision["action"] = "reject"
            reason = Prompt.ask("Reason for rejection", default="Not approved")
            decision["reason"] = reason

        elif choice == 3:
            decision["action"] = "modify"
            self.console.print("\n[yellow]Modification mode not fully implemented in CLI.[/yellow]")
            self.console.print("[yellow]Please edit the JSON file directly or approve/reject.[/yellow]")

            # For now, just collect comments
            modifications = Prompt.ask("Describe modifications", default="")
            decision["modifications"] = {"notes": modifications}
            decision["modified_item"] = approval.item_data

        self.console.print("\n[green]✓ Decision recorded[/green]\n")

        return decision

    def _display_item_data(self, item_data: Dict[str, Any], item_type: str) -> None:
        """Display item data in a readable format."""
        if item_type == "test_plan":
            self._display_test_plan(item_data)
        elif item_type == "test_case":
            self._display_test_case(item_data)
        else:
            # Generic JSON display
            json_str = json.dumps(item_data, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            self.console.print(Panel(syntax, title="Item Data", border_style="blue"))

    def _display_test_plan(self, plan: Dict[str, Any]) -> None:
        """Display test plan details."""
        table = Table(title="Test Plan Details", show_header=True, header_style="bold magenta")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        for key, value in plan.items():
            if key == "tests" and isinstance(value, list):
                table.add_row("Number of Tests", str(len(value)))
            elif not isinstance(value, (dict, list)):
                table.add_row(key, str(value))

        self.console.print(table)

        # Display test cases if available
        if "tests" in plan and isinstance(plan["tests"], list):
            self.console.print(f"\n[bold]Test Cases ({len(plan['tests'])}):[/bold]")
            for idx, test in enumerate(plan["tests"][:5], 1):  # Show first 5
                test_name = test.get("name", "Unknown")
                test_desc = test.get("description", "")
                self.console.print(f"  {idx}. {test_name}")
                if test_desc:
                    self.console.print(f"     {test_desc}")

            if len(plan["tests"]) > 5:
                self.console.print(f"  ... and {len(plan['tests']) - 5} more")

    def _display_test_case(self, test_case: Dict[str, Any]) -> None:
        """Display test case details."""
        self.console.print(Panel(
            f"[bold]Name:[/bold] {test_case.get('name', 'Unknown')}\n"
            f"[bold]Description:[/bold] {test_case.get('description', 'N/A')}\n"
            f"[bold]Type:[/bold] {test_case.get('test_type', 'N/A')}\n"
            f"[bold]Priority:[/bold] {test_case.get('priority', 'N/A')}",
            title="Test Case",
            border_style="blue"
        ))

        # Display steps
        steps = test_case.get("steps", [])
        if steps:
            table = Table(title="Test Steps", show_header=True, header_style="bold magenta")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Action", style="yellow")
            table.add_column("Target", style="green")
            table.add_column("Expected Result", style="white")

            for step in steps:
                table.add_row(
                    str(step.get("step_number", "")),
                    step.get("action", ""),
                    step.get("target", "")[:30],
                    step.get("expected_result", "")[:40]
                )

            self.console.print(table)

    def collect_feedback(
        self,
        test_result: TestResult,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Collect feedback on a test result."""
        self.console.print("\n" + "="*80)
        self.console.print(
            Panel(
                f"[bold cyan]Feedback Request[/bold cyan]\n\n"
                f"Test: [yellow]{test_result.test_name}[/yellow]\n"
                f"Status: [yellow]{test_result.status.value}[/yellow]\n"
                f"Duration: [yellow]{test_result.metrics.duration_seconds:.2f}s[/yellow]",
                title="Feedback Required",
                border_style="cyan"
            )
        )

        self.console.print(f"\n[bold]{prompt}[/bold]\n")

        # Ask if user wants to provide feedback
        if not Confirm.ask("Provide feedback?", default=True):
            return None

        feedback = {
            "provided_by": Prompt.ask("Your name", default="human")
        }

        # Rating
        rating = IntPrompt.ask(
            "Rating (1-5)",
            choices=["1", "2", "3", "4", "5"],
            default="3"
        )
        feedback["rating"] = rating

        # Comment
        comment = Prompt.ask("Comment", default="")
        feedback["comment"] = comment

        # Classification for failed tests
        if test_result.status.value == "failed":
            feedback["is_false_positive"] = Confirm.ask(
                "Is this a false positive (test failed incorrectly)?",
                default=False
            )

            feedback["is_known_issue"] = Confirm.ask(
                "Is this a known issue?",
                default=False
            )

            feedback["needs_investigation"] = Confirm.ask(
                "Does this need investigation?",
                default=not feedback["is_known_issue"]
            )

        self.console.print("\n[green]✓ Feedback recorded[/green]\n")

        return feedback

    def collect_generation_feedback(
        self,
        item_id: str,
        item_type: str,
        item_data: Dict[str, Any],
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Collect feedback on generated items."""
        self.console.print("\n" + "="*80)
        self.console.print(
            Panel(
                f"[bold cyan]Generation Feedback[/bold cyan]\n\n"
                f"Type: [yellow]{item_type}[/yellow]\n"
                f"ID: [yellow]{item_id}[/yellow]",
                title="Review Generated Item",
                border_style="cyan"
            )
        )

        self.console.print(f"\n[bold]{prompt}[/bold]\n")

        # Display generated item
        self._display_item_data(item_data, item_type)

        # Ask if user wants to provide feedback
        if not Confirm.ask("Provide feedback?", default=True):
            return None

        feedback = {
            "provided_by": Prompt.ask("Your name", default="human")
        }

        # Rating
        rating = IntPrompt.ask(
            "Quality rating (1-5)",
            choices=["1", "2", "3", "4", "5"],
            default="3"
        )
        feedback["rating"] = rating

        # Comment
        comment = Prompt.ask("Comment", default="")
        feedback["comment"] = comment

        # Corrections
        has_corrections = Confirm.ask(
            "Do you have corrections/improvements?",
            default=False
        )

        if has_corrections:
            corrections_note = Prompt.ask("Describe corrections", default="")
            feedback["corrections"] = {"notes": corrections_note}

        self.console.print("\n[green]✓ Feedback recorded[/green]\n")

        return feedback


# Web-based reviewer implementation
class WebReviewer(ReviewInterface):
    """
    Web-based review interface.

    This reviewer saves approval requests to files that the web UI polls.
    It waits for the web UI user to approve/reject by watching for file updates.
    """

    def __init__(self, port: int = 5000, poll_interval: float = 1.0):
        """
        Initialize web reviewer.

        Args:
            port: Port for web UI (informational only)
            poll_interval: How often to check for approval decisions (seconds)
        """
        self.port = port
        self.poll_interval = poll_interval
        logger.info(f"WebReviewer initialized (web UI on port {port})")

    def review_approval(self, approval: Approval) -> Dict[str, Any]:
        """
        Review approval via web interface.

        This method:
        1. Saves the approval to a file
        2. Logs that approval is needed (web UI will pick it up)
        3. Polls the file waiting for web UI to update it
        4. Returns the decision once made

        Args:
            approval: Approval request

        Returns:
            Decision dictionary with action, approver, etc.
        """
        import time
        from pathlib import Path
        from utils.helpers import save_json, load_json
        from models.approval import ApprovalStatus

        # Ensure approvals directory exists
        approvals_dir = Path("approvals")
        approvals_dir.mkdir(exist_ok=True)

        # Save approval to file
        approval_file = approvals_dir / f"{approval.id}.json"
        save_json(str(approval_file), approval.dict())

        logger.info(
            f"Approval request saved for web UI: {approval.id} "
            f"(type: {approval.approval_type.value})"
        )
        logger.info(f"Waiting for web UI user to review approval {approval.id}...")

        # Poll for approval decision
        start_time = time.time()
        timeout = approval.timeout_seconds

        while True:
            # Check if timeout exceeded
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.warning(f"Approval {approval.id} timed out after {timeout}s")
                return {
                    "action": "timeout",
                    "approver": "system",
                    "reason": "Approval request timed out"
                }

            # Load current approval state
            try:
                approval_data = load_json(str(approval_file))
                current_approval = Approval(**approval_data)

                # Check if approval has been processed
                if current_approval.status != ApprovalStatus.PENDING:
                    logger.info(
                        f"Approval {approval.id} {current_approval.status.value} "
                        f"by {current_approval.approved_by}"
                    )

                    # Build decision based on status
                    decision = {
                        "approver": current_approval.approved_by or "unknown"
                    }

                    if current_approval.status == ApprovalStatus.APPROVED:
                        decision["action"] = "approve"
                        if current_approval.comments:
                            decision["comments"] = current_approval.comments

                    elif current_approval.status == ApprovalStatus.REJECTED:
                        decision["action"] = "reject"
                        decision["reason"] = current_approval.rejection_reason or "No reason provided"

                    elif current_approval.status == ApprovalStatus.MODIFIED:
                        decision["action"] = "modify"
                        decision["modifications"] = current_approval.modifications or {}
                        decision["modified_item"] = current_approval.modified_item or approval.item_data
                        if current_approval.comments:
                            decision["comments"] = current_approval.comments

                    elif current_approval.status == ApprovalStatus.TIMEOUT:
                        decision["action"] = "timeout"
                        decision["reason"] = "Timed out"

                    return decision

            except Exception as e:
                logger.error(f"Error checking approval status: {e}")

            # Wait before next poll
            time.sleep(self.poll_interval)

    def collect_feedback(
        self,
        test_result: TestResult,
        prompt: str
    ) -> Optional[Dict[str, Any]]:
        """
        Collect feedback via web interface.

        Note: For web UI, feedback is submitted asynchronously via the API.
        This method is not actively used in web mode.

        Args:
            test_result: Test result
            prompt: Feedback prompt

        Returns:
            None (feedback submitted via web API)
        """
        logger.info(
            f"Feedback request for test {test_result.test_name}. "
            f"Users can submit feedback via web UI."
        )

        # For web mode, we don't block waiting for feedback
        # Users submit feedback asynchronously via the web API
        return None
