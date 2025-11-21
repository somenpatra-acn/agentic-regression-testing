"""Test knowledge retriever using RAG."""

from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from rag.vector_store import VectorStoreManager
from models.test_case import TestCase
from models.test_result import TestResult
from utils.logger import get_logger

logger = get_logger(__name__)


class TestKnowledgeRetriever:
    """Retrieve relevant test knowledge using RAG."""

    def __init__(self, collection_name: str = "test_knowledge"):
        """
        Initialize test knowledge retriever.

        Args:
            collection_name: Vector store collection name
        """
        self.vector_store_manager = VectorStoreManager(collection_name)
        logger.info("TestKnowledgeRetriever initialized")

    def add_test_case(self, test_case: TestCase) -> None:
        """
        Add a test case to the knowledge base.

        Args:
            test_case: Test case to add
        """
        # Create document from test case
        content = self._test_case_to_text(test_case)

        metadata = {
            "type": "test_case",
            "test_id": test_case.id,
            "test_name": test_case.name,
            "test_type": test_case.test_type.value,
            "priority": test_case.priority.value,
            "application": test_case.application,
            "module": test_case.module,
            "feature": test_case.feature,
        }

        self.vector_store_manager.add_texts([content], metadatas=[metadata])

        logger.debug(f"Added test case to knowledge base: {test_case.id}")

    def add_test_cases(self, test_cases: List[TestCase]) -> None:
        """
        Add multiple test cases to the knowledge base.

        Args:
            test_cases: List of test cases
        """
        if not test_cases:
            return

        texts = []
        metadatas = []

        for test_case in test_cases:
            content = self._test_case_to_text(test_case)
            metadata = {
                "type": "test_case",
                "test_id": test_case.id,
                "test_name": test_case.name,
                "test_type": test_case.test_type.value,
                "priority": test_case.priority.value,
                "application": test_case.application,
            }
            texts.append(content)
            metadatas.append(metadata)

        self.vector_store_manager.add_texts(texts, metadatas=metadatas)

        logger.info(f"Added {len(test_cases)} test cases to knowledge base")

    def add_test_result(self, test_result: TestResult) -> None:
        """
        Add a test result to the knowledge base.

        Args:
            test_result: Test result to add
        """
        content = self._test_result_to_text(test_result)

        metadata = {
            "type": "test_result",
            "result_id": test_result.id,
            "test_case_id": test_result.test_case_id,
            "test_name": test_result.test_name,
            "status": test_result.status.value,
            "executed_at": test_result.executed_at.isoformat(),
        }

        self.vector_store_manager.add_texts([content], metadatas=[metadata])

        logger.debug(f"Added test result to knowledge base: {test_result.id}")

    def add_feedback_documents(self, feedback_docs: List[str]) -> None:
        """
        Add feedback documents to the knowledge base.

        Args:
            feedback_docs: List of feedback document strings
        """
        if not feedback_docs:
            return

        metadatas = [{"type": "feedback"} for _ in feedback_docs]

        self.vector_store_manager.add_texts(feedback_docs, metadatas=metadatas)

        logger.info(f"Added {len(feedback_docs)} feedback documents to knowledge base")

    def find_similar_tests(
        self,
        query: str,
        k: int = 5,
        application: Optional[str] = None,
        test_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar test cases based on query.

        Args:
            query: Search query
            k: Number of results
            application: Filter by application
            test_type: Filter by test type

        Returns:
            List of similar test information
        """
        # Build filter
        filter_dict = {"type": "test_case"}
        if application:
            filter_dict["application"] = application
        if test_type:
            filter_dict["test_type"] = test_type

        results = self.vector_store_manager.similarity_search_with_score(
            query,
            k=k,
            filter=filter_dict
        )

        similar_tests = []
        for doc, score in results:
            test_info = {
                "content": doc.page_content,
                "score": score,
                "metadata": doc.metadata
            }
            similar_tests.append(test_info)

        logger.debug(f"Found {len(similar_tests)} similar tests for query: {query}")

        return similar_tests

    def find_relevant_context(
        self,
        query: str,
        k: int = 5,
        doc_type: Optional[str] = None
    ) -> List[Document]:
        """
        Find relevant context documents for query.

        Args:
            query: Search query
            k: Number of results
            doc_type: Filter by document type (test_case, test_result, feedback)

        Returns:
            List of relevant documents
        """
        filter_dict = {}
        if doc_type:
            filter_dict["type"] = doc_type

        results = self.vector_store_manager.similarity_search(
            query,
            k=k,
            filter=filter_dict
        )

        logger.debug(f"Found {len(results)} relevant documents for query: {query}")

        return results

    def get_test_patterns(self, feature: str, k: int = 3) -> List[str]:
        """
        Get test patterns for a specific feature.

        Args:
            feature: Feature name
            k: Number of patterns to retrieve

        Returns:
            List of test pattern descriptions
        """
        query = f"test patterns for {feature}"

        results = self.find_relevant_context(query, k=k, doc_type="test_case")

        patterns = [doc.page_content for doc in results]

        return patterns

    def get_failure_insights(self, error_message: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Get insights from similar historical failures.

        Args:
            error_message: Error message to search for
            k: Number of insights to retrieve

        Returns:
            List of failure insights
        """
        query = f"test failure: {error_message}"

        results = self.vector_store_manager.similarity_search_with_score(
            query,
            k=k,
            filter={"type": "test_result"}
        )

        insights = []
        for doc, score in results:
            insight = {
                "content": doc.page_content,
                "score": score,
                "metadata": doc.metadata
            }
            insights.append(insight)

        return insights

    def _test_case_to_text(self, test_case: TestCase) -> str:
        """Convert test case to text representation for embedding."""
        text = f"""
Test Case: {test_case.name}
ID: {test_case.id}
Type: {test_case.test_type.value}
Priority: {test_case.priority.value}
Description: {test_case.description}

Application: {test_case.application}
Module: {test_case.module or 'N/A'}
Feature: {test_case.feature or 'N/A'}

Test Steps:
"""
        for step in test_case.steps:
            text += f"\n{step.step_number}. {step.action} on {step.target or 'target'}"
            text += f"\n   Expected: {step.expected_result}"

        if test_case.preconditions:
            text += f"\n\nPreconditions: {', '.join(test_case.preconditions)}"

        if test_case.tags:
            text += f"\nTags: {', '.join(test_case.tags)}"

        return text.strip()

    def _test_result_to_text(self, test_result: TestResult) -> str:
        """Convert test result to text representation for embedding."""
        text = f"""
Test Result: {test_result.test_name}
Test Case ID: {test_result.test_case_id}
Status: {test_result.status.value}
Duration: {test_result.metrics.duration_seconds:.2f}s

"""
        if test_result.error_message:
            text += f"Error: {test_result.error_message}\n"

        if test_result.human_comment:
            text += f"Human Comment: {test_result.human_comment}\n"

        if test_result.is_false_positive:
            text += "Classification: False Positive\n"

        # Add step results
        text += "\nStep Results:\n"
        for step_result in test_result.step_results:
            text += f"{step_result.step_number}. Status: {step_result.status.value}"
            if step_result.error_message:
                text += f" - Error: {step_result.error_message}"
            text += "\n"

        return text.strip()

    def save(self) -> None:
        """Save the vector store to disk."""
        self.vector_store_manager.save()
        logger.info("Knowledge base saved")

    def clear(self) -> None:
        """Clear the knowledge base."""
        self.vector_store_manager.delete_collection()
        logger.info("Knowledge base cleared")
