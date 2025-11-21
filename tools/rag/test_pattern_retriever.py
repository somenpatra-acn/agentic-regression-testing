"""
Test Pattern Retriever Tool

Retrieves test patterns and historical test information from knowledge base.
"""

from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata
from rag.retriever import TestKnowledgeRetriever


class TestPatternRetrieverTool(BaseTool):
    """
    Retrieves test patterns from knowledge base

    This tool provides specialized retrieval for test patterns,
    failure insights, and historical test information.

    Features:
    - Get test patterns for specific features
    - Retrieve failure insights from historical data
    - Find similar test implementations
    - Extract test design patterns
    """

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        pass

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="test_pattern_retriever",
            description="Retrieves test patterns and historical test information from knowledge base",
            version="1.0.0",
            tags=["rag", "patterns", "knowledge", "history"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "feature": "string - Feature name to get patterns for",
                "error_message": "string - Error message to get failure insights for",
                "pattern_type": "string - Type of patterns (feature, failure, similar)",
                "k": "integer - Number of patterns to retrieve (default: 3)",
            },
            output_schema={
                "patterns": "list - Retrieved test patterns or insights",
                "count": "integer - Number of patterns retrieved",
            }
        )

    def execute(
        self,
        pattern_type: str = "feature",
        feature: Optional[str] = None,
        error_message: Optional[str] = None,
        k: int = 3,
    ) -> ToolResult:
        """
        Retrieve test patterns from knowledge base

        Args:
            pattern_type: Type of patterns to retrieve ("feature", "failure", "similar")
            feature: Feature name (for pattern_type="feature")
            error_message: Error message (for pattern_type="failure")
            k: Number of patterns to retrieve

        Returns:
            ToolResult containing retrieved patterns
        """
        return self._wrap_execution(
            self._retrieve,
            pattern_type=pattern_type,
            feature=feature,
            error_message=error_message,
            k=k,
        )

    def _retrieve(
        self,
        pattern_type: str,
        feature: Optional[str],
        error_message: Optional[str],
        k: int,
    ) -> ToolResult:
        """Internal retrieval logic"""

        # Validate inputs based on pattern type
        if pattern_type == "feature" and not feature:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="feature parameter is required for pattern_type='feature'",
            )

        if pattern_type == "failure" and not error_message:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="error_message parameter is required for pattern_type='failure'",
            )

        if pattern_type not in ["feature", "failure", "similar"]:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Invalid pattern_type: {pattern_type}. Must be 'feature', 'failure', or 'similar'",
            )

        if k < 1 or k > 20:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"k must be between 1 and 20, got {k}",
            )

        try:
            # Get collection name from config or use default
            collection_name = self.config.get("collection_name", "test_knowledge")

            # Initialize retriever
            retriever = TestKnowledgeRetriever(collection_name=collection_name)

            # Retrieve patterns based on type
            if pattern_type == "feature":
                patterns = retriever.get_test_patterns(feature=feature, k=k)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "patterns": patterns,
                        "count": len(patterns),
                        "pattern_type": "feature",
                    },
                    metadata={
                        "feature": feature,
                        "k": k,
                    }
                )

            elif pattern_type == "failure":
                insights = retriever.get_failure_insights(
                    error_message=error_message,
                    k=k
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "patterns": insights,
                        "count": len(insights),
                        "pattern_type": "failure",
                    },
                    metadata={
                        "error_message": error_message[:100],  # Truncate for metadata
                        "k": k,
                    }
                )

            elif pattern_type == "similar":
                # Use vector search for similar tests
                query = feature or error_message or "test patterns"
                similar_tests = retriever.find_similar_tests(
                    query=query,
                    k=k,
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "patterns": similar_tests,
                        "count": len(similar_tests),
                        "pattern_type": "similar",
                    },
                    metadata={
                        "query": query,
                        "k": k,
                    }
                )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Pattern retrieval failed: {str(e)}",
                metadata={
                    "pattern_type": pattern_type,
                    "exception_type": type(e).__name__,
                }
            )
