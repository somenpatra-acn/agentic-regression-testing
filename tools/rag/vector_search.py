"""
Vector Search Tool

Performs similarity search in the test knowledge base vector store.
"""

from typing import Dict, Any, Optional, List
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata
from rag.retriever import TestKnowledgeRetriever


class VectorSearchTool(BaseTool):
    """
    Performs vector similarity search in test knowledge base

    This tool wraps the TestKnowledgeRetriever to provide RAG capabilities
    as a reusable tool for agents.

    Features:
    - Similarity search with filtering
    - Retrieves test cases, results, and feedback
    - Supports metadata filtering (application, test_type)
    - Returns scored results
    """

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        # collection_name is optional, defaults to "test_knowledge"
        pass

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="vector_search",
            description="Performs similarity search in test knowledge base using vector embeddings",
            version="1.0.0",
            tags=["rag", "vector", "search", "knowledge"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "query": "string - Search query",
                "k": "integer - Number of results to return (default: 5)",
                "doc_type": "string - Filter by document type (test_case, test_result, feedback)",
                "application": "string - Filter by application name",
                "test_type": "string - Filter by test type",
            },
            output_schema={
                "results": "list - Similar documents with content, score, and metadata",
                "count": "integer - Number of results returned",
            }
        )

    def execute(
        self,
        query: str,
        k: int = 5,
        doc_type: Optional[str] = None,
        application: Optional[str] = None,
        test_type: Optional[str] = None,
    ) -> ToolResult:
        """
        Perform similarity search in vector store

        Args:
            query: Search query string
            k: Number of results to return
            doc_type: Filter by document type (test_case, test_result, feedback)
            application: Filter by application name
            test_type: Filter by test type

        Returns:
            ToolResult containing similar documents
        """
        return self._wrap_execution(
            self._search,
            query=query,
            k=k,
            doc_type=doc_type,
            application=application,
            test_type=test_type,
        )

    def _search(
        self,
        query: str,
        k: int,
        doc_type: Optional[str],
        application: Optional[str],
        test_type: Optional[str],
    ) -> ToolResult:
        """Internal search logic"""

        if not query or not query.strip():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="Query cannot be empty",
            )

        if k < 1 or k > 100:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"k must be between 1 and 100, got {k}",
            )

        try:
            # Get collection name from config or use default
            collection_name = self.config.get("collection_name", "test_knowledge")

            # Initialize retriever
            retriever = TestKnowledgeRetriever(collection_name=collection_name)

            # Perform search based on doc_type
            if doc_type == "test_case" or (not doc_type and (application or test_type)):
                # Use find_similar_tests for test cases with filtering
                results = retriever.find_similar_tests(
                    query=query,
                    k=k,
                    application=application,
                    test_type=test_type
                )
            else:
                # Use find_relevant_context for general search
                docs = retriever.find_relevant_context(
                    query=query,
                    k=k,
                    doc_type=doc_type
                )

                # Convert to same format as find_similar_tests
                results = [
                    {
                        "content": doc.page_content,
                        "score": 0.0,  # find_relevant_context doesn't return scores
                        "metadata": doc.metadata
                    }
                    for doc in docs
                ]

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "results": results,
                    "count": len(results),
                },
                metadata={
                    "query": query,
                    "k": k,
                    "doc_type": doc_type,
                    "filters_applied": {
                        "application": application,
                        "test_type": test_type,
                    }
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Vector search failed: {str(e)}",
                metadata={
                    "query": query,
                    "exception_type": type(e).__name__,
                }
            )
