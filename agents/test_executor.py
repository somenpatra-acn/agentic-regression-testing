"""Test Executor Agent - executes test cases and collects results."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from adapters.base_adapter import BaseApplicationAdapter
from models.app_profile import ApplicationProfile
from models.test_case import TestCase
from models.test_result import TestResult
from rag.retriever import TestKnowledgeRetriever
from hitl.feedback_collector import FeedbackCollector
from utils.logger import get_logger

logger = get_logger(__name__)


class TestExecutorAgent:
    """
    Test Executor Agent executes test cases using appropriate frameworks.

    Supports:
    - Sequential and parallel execution
    - Multiple test frameworks (Selenium, Playwright, pytest)
    - Result collection and logging
    - Human feedback collection on failures
    """

    def __init__(
        self,
        adapter: BaseApplicationAdapter,
        app_profile: ApplicationProfile
    ):
        """
        Initialize Test Executor Agent.

        Args:
            adapter: Application adapter
            app_profile: Application profile
        """
        self.adapter = adapter
        self.app_profile = app_profile
        self.knowledge_retriever = TestKnowledgeRetriever()
        self.feedback_collector = FeedbackCollector()

        self.test_results: List[TestResult] = []

        logger.info(f"TestExecutorAgent initialized for {app_profile.name}")

    def execute_tests(
        self,
        test_cases: List[TestCase],
        parallel: bool = None,
        collect_feedback: bool = False
    ) -> List[TestResult]:
        """
        Execute list of test cases.

        Args:
            test_cases: List of test cases to execute
            parallel: Execute in parallel (uses app_profile setting if None)
            collect_feedback: Collect human feedback on failures

        Returns:
            List of TestResult objects
        """
        if parallel is None:
            parallel = self.app_profile.parallel_execution

        logger.info(
            f"Executing {len(test_cases)} test cases "
            f"({'parallel' if parallel else 'sequential'})"
        )

        if parallel:
            results = self._execute_parallel(test_cases)
        else:
            results = self._execute_sequential(test_cases)

        self.test_results.extend(results)

        # Store results in knowledge base
        for result in results:
            self.knowledge_retriever.add_test_result(result)

        # Collect feedback on failures if requested
        if collect_feedback:
            self._collect_feedback_on_failures(results)

        # Log summary
        passed = sum(1 for r in results if r.status.value == "passed")
        failed = sum(1 for r in results if r.status.value == "failed")
        logger.info(f"Execution complete: {passed} passed, {failed} failed")

        return results

    def _execute_sequential(self, test_cases: List[TestCase]) -> List[TestResult]:
        """Execute test cases sequentially."""
        results = []

        for idx, test_case in enumerate(test_cases, 1):
            logger.info(f"Executing test {idx}/{len(test_cases)}: {test_case.name}")
            result = self.adapter.execute_test(test_case)
            results.append(result)

        return results

    def _execute_parallel(self, test_cases: List[TestCase]) -> List[TestResult]:
        """Execute test cases in parallel."""
        results = []
        max_workers = self.app_profile.max_workers

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_test = {
                executor.submit(self.adapter.execute_test, tc): tc
                for tc in test_cases
            }

            for future in as_completed(future_to_test):
                test_case = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed: {test_case.name} - {result.status.value}")
                except Exception as e:
                    logger.error(f"Error executing {test_case.name}: {e}")

        return results

    def _collect_feedback_on_failures(self, results: List[TestResult]) -> None:
        """Collect human feedback on failed tests."""
        failed_results = [r for r in results if r.status.value == "failed"]

        if not failed_results:
            return

        logger.info(f"Collecting feedback on {len(failed_results)} failed tests")

        for result in failed_results:
            try:
                feedback = self.feedback_collector.collect_test_feedback(result)
                if feedback:
                    logger.info(f"Feedback collected for {result.test_name}")
            except Exception as e:
                logger.error(f"Error collecting feedback: {e}")

    def get_test_results(self) -> List[TestResult]:
        """Get all test results."""
        return self.test_results

    def get_summary(self) -> dict:
        """Get execution summary."""
        if not self.test_results:
            return {"message": "No test results available"}

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.status.value == "passed")
        failed = sum(1 for r in self.test_results if r.status.value == "failed")
        skipped = sum(1 for r in self.test_results if r.status.value == "skipped")
        error = sum(1 for r in self.test_results if r.status.value == "error")

        total_duration = sum(r.metrics.duration_seconds for r in self.test_results)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "error": error,
            "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%",
            "total_duration": f"{total_duration:.2f}s"
        }
