"""Feedback collector for gathering human feedback on tests."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.approval import Feedback
from models.test_result import TestResult, TestStatus
from utils.logger import get_logger
from utils.helpers import generate_id, save_json, load_json

logger = get_logger(__name__)


class FeedbackCollector:
    """Collect and manage human feedback on test execution and generation."""

    def __init__(self):
        """Initialize feedback collector."""
        self.feedback_dir = Path("feedback")
        self.feedback_dir.mkdir(exist_ok=True)

        logger.info("FeedbackCollector initialized")

    def collect_test_feedback(
        self,
        test_result: TestResult,
        prompt: Optional[str] = None
    ) -> Optional[Feedback]:
        """
        Collect feedback on a test result.

        Args:
            test_result: Test result to get feedback on
            prompt: Optional custom prompt

        Returns:
            Feedback object or None if skipped
        """
        # Default prompt based on test status
        if prompt is None:
            if test_result.status == TestStatus.FAILED:
                prompt = f"Test '{test_result.test_name}' failed. Is this expected?"
            elif test_result.status == TestStatus.PASSED:
                prompt = f"Test '{test_result.test_name}' passed. Any concerns?"
            else:
                prompt = f"Provide feedback on test '{test_result.test_name}'"

        logger.info(f"Collecting feedback for test result: {test_result.id}")

        # Use CLI interface to collect feedback
        from hitl.review_interface import CLIReviewer

        reviewer = CLIReviewer()
        feedback_data = reviewer.collect_feedback(test_result, prompt)

        if not feedback_data:
            return None

        # Create feedback object
        feedback = Feedback(
            id=generate_id("FB"),
            item_id=test_result.id,
            item_type="test_result",
            rating=feedback_data.get("rating"),
            comment=feedback_data.get("comment", ""),
            is_false_positive=feedback_data.get("is_false_positive", False),
            is_false_negative=feedback_data.get("is_false_negative", False),
            is_known_issue=feedback_data.get("is_known_issue", False),
            needs_investigation=feedback_data.get("needs_investigation", False),
            corrections=feedback_data.get("corrections"),
            provided_by=feedback_data.get("provided_by", "human"),
            provided_at=datetime.utcnow()
        )

        # Save feedback
        self._save_feedback(feedback)

        # Update test result with feedback
        test_result.human_comment = feedback.comment
        test_result.is_false_positive = feedback.is_false_positive
        test_result.is_false_negative = feedback.is_false_negative
        test_result.validated_by_human = True

        logger.info(f"Feedback collected: {feedback.id}")

        return feedback

    def collect_generation_feedback(
        self,
        item_id: str,
        item_type: str,
        item_data: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> Optional[Feedback]:
        """
        Collect feedback on generated items (test cases, scripts, etc.).

        Args:
            item_id: ID of generated item
            item_type: Type of item (test_case, script, etc.)
            item_data: Item data
            prompt: Optional custom prompt

        Returns:
            Feedback object or None if skipped
        """
        if prompt is None:
            prompt = f"Review generated {item_type}: {item_id}"

        logger.info(f"Collecting feedback for {item_type}: {item_id}")

        from hitl.review_interface import CLIReviewer

        reviewer = CLIReviewer()
        feedback_data = reviewer.collect_generation_feedback(
            item_id, item_type, item_data, prompt
        )

        if not feedback_data:
            return None

        feedback = Feedback(
            id=generate_id("FB"),
            item_id=item_id,
            item_type=item_type,
            rating=feedback_data.get("rating"),
            comment=feedback_data.get("comment", ""),
            corrections=feedback_data.get("corrections"),
            provided_by=feedback_data.get("provided_by", "human"),
            provided_at=datetime.utcnow()
        )

        self._save_feedback(feedback)

        logger.info(f"Generation feedback collected: {feedback.id}")

        return feedback

    def _save_feedback(self, feedback: Feedback) -> None:
        """Save feedback to file."""
        filepath = self.feedback_dir / f"{feedback.id}.json"
        save_json(feedback.model_dump(), str(filepath))

    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """
        Load feedback from file.

        Args:
            feedback_id: Feedback ID

        Returns:
            Feedback object or None
        """
        filepath = self.feedback_dir / f"{feedback_id}.json"
        if filepath.exists():
            data = load_json(str(filepath))
            return Feedback(**data)
        return None

    def get_feedback_for_item(self, item_id: str) -> List[Feedback]:
        """
        Get all feedback for a specific item.

        Args:
            item_id: Item ID

        Returns:
            List of Feedback objects
        """
        feedback_list = []
        for filepath in self.feedback_dir.glob("*.json"):
            try:
                feedback = Feedback(**load_json(str(filepath)))
                if feedback.item_id == item_id:
                    feedback_list.append(feedback)
            except Exception as e:
                logger.error(f"Error loading feedback {filepath}: {e}")

        return feedback_list

    def get_all_feedback(self, item_type: Optional[str] = None) -> List[Feedback]:
        """
        Get all feedback, optionally filtered by type.

        Args:
            item_type: Optional item type filter

        Returns:
            List of Feedback objects
        """
        feedback_list = []
        for filepath in self.feedback_dir.glob("*.json"):
            try:
                feedback = Feedback(**load_json(str(filepath)))
                if item_type is None or feedback.item_type == item_type:
                    feedback_list.append(feedback)
            except Exception as e:
                logger.error(f"Error loading feedback {filepath}: {e}")

        return feedback_list

    def get_false_positives(self) -> List[Feedback]:
        """Get all feedback marked as false positives."""
        return [fb for fb in self.get_all_feedback() if fb.is_false_positive]

    def get_false_negatives(self) -> List[Feedback]:
        """Get all feedback marked as false negatives."""
        return [fb for fb in self.get_all_feedback() if fb.is_false_negative]

    def get_known_issues(self) -> List[Feedback]:
        """Get all feedback marked as known issues."""
        return [fb for fb in self.get_all_feedback() if fb.is_known_issue]

    def export_feedback_for_rag(self) -> List[str]:
        """
        Export all feedback as documents for RAG storage.

        Returns:
            List of feedback documents
        """
        feedback_list = self.get_all_feedback()
        return [fb.to_document() for fb in feedback_list]

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about collected feedback.

        Returns:
            Dictionary of statistics
        """
        all_feedback = self.get_all_feedback()

        stats = {
            "total_feedback": len(all_feedback),
            "by_type": {},
            "false_positives": len(self.get_false_positives()),
            "false_negatives": len(self.get_false_negatives()),
            "known_issues": len(self.get_known_issues()),
            "average_rating": 0.0
        }

        # Count by type
        for fb in all_feedback:
            stats["by_type"][fb.item_type] = stats["by_type"].get(fb.item_type, 0) + 1

        # Calculate average rating
        rated_feedback = [fb for fb in all_feedback if fb.rating is not None]
        if rated_feedback:
            stats["average_rating"] = sum(fb.rating for fb in rated_feedback) / len(rated_feedback)

        return stats
