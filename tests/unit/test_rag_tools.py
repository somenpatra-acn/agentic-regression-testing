"""
Unit Tests for RAG Tools

Tests VectorSearchTool and TestPatternRetrieverTool with mocked retriever.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.rag.vector_search import VectorSearchTool
from tools.rag.test_pattern_retriever import TestPatternRetrieverTool
from tools.base import ToolStatus, ToolRegistry


@pytest.mark.unit
class TestVectorSearchTool:
    """Test VectorSearchTool"""

    @pytest.fixture
    def search_tool(self):
        """Create vector search tool"""
        return VectorSearchTool(config={"collection_name": "test_knowledge"})

    def test_tool_metadata(self, search_tool):
        """Test tool metadata"""
        metadata = search_tool.metadata

        assert metadata.name == "vector_search"
        assert metadata.version == "1.0.0"
        assert "rag" in metadata.tags
        assert "vector" in metadata.tags
        assert metadata.is_safe is True

    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    def test_successful_search(self, mock_retriever_class, search_tool):
        """Test successful vector search"""
        # Setup mock
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.return_value = [
            {
                "content": "Test case 1 content",
                "score": 0.95,
                "metadata": {"test_name": "Test 1", "test_type": "functional"}
            },
            {
                "content": "Test case 2 content",
                "score": 0.85,
                "metadata": {"test_name": "Test 2", "test_type": "negative"}
            }
        ]
        mock_retriever_class.return_value = mock_retriever

        # Execute search
        result = search_tool.execute(
            query="login functionality",
            k=5,
            application="my_app",
            test_type="functional"
        )

        # Assertions
        assert result.is_success()
        assert result.data["count"] == 2
        assert len(result.data["results"]) == 2
        assert result.data["results"][0]["content"] == "Test case 1 content"
        assert result.metadata["query"] == "login functionality"
        assert mock_retriever.find_similar_tests.called

    def test_empty_query(self, search_tool):
        """Test with empty query"""
        result = search_tool.execute(query="", k=5)

        assert result.is_failure()
        assert "cannot be empty" in result.error.lower()

    def test_invalid_k_value(self, search_tool):
        """Test with invalid k value"""
        # Too small
        result = search_tool.execute(query="test", k=0)
        assert result.is_failure()
        assert "must be between" in result.error.lower()

        # Too large
        result = search_tool.execute(query="test", k=101)
        assert result.is_failure()

    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    def test_search_with_doc_type_filter(self, mock_retriever_class, search_tool):
        """Test search with document type filtering"""
        mock_retriever = Mock()
        mock_doc = Mock()
        mock_doc.page_content = "Test result content"
        mock_doc.metadata = {"type": "test_result"}
        mock_retriever.find_relevant_context.return_value = [mock_doc]
        mock_retriever_class.return_value = mock_retriever

        result = search_tool.execute(
            query="test results",
            k=3,
            doc_type="test_result"
        )

        assert result.is_success()
        assert mock_retriever.find_relevant_context.called

    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    def test_search_exception_handling(self, mock_retriever_class, search_tool):
        """Test exception handling"""
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.side_effect = Exception("Vector store error")
        mock_retriever_class.return_value = mock_retriever

        result = search_tool.execute(query="test query", k=5)

        assert result.is_failure()
        assert result.status == ToolStatus.ERROR
        assert "Vector search failed" in result.error


@pytest.mark.unit
class TestTestPatternRetrieverTool:
    """Test TestPatternRetrieverTool"""

    @pytest.fixture
    def pattern_tool(self):
        """Create test pattern retriever tool"""
        return TestPatternRetrieverTool()

    def test_tool_metadata(self, pattern_tool):
        """Test tool metadata"""
        metadata = pattern_tool.metadata

        assert metadata.name == "test_pattern_retriever"
        assert metadata.version == "1.0.0"
        assert "patterns" in metadata.tags
        assert metadata.is_safe is True

    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_retrieve_feature_patterns(self, mock_retriever_class, pattern_tool):
        """Test retrieving feature patterns"""
        mock_retriever = Mock()
        mock_retriever.get_test_patterns.return_value = [
            "Pattern 1: Login test pattern",
            "Pattern 2: Authentication pattern",
            "Pattern 3: Session management pattern"
        ]
        mock_retriever_class.return_value = mock_retriever

        result = pattern_tool.execute(
            pattern_type="feature",
            feature="login",
            k=3
        )

        assert result.is_success()
        assert result.data["count"] == 3
        assert result.data["pattern_type"] == "feature"
        assert len(result.data["patterns"]) == 3
        assert mock_retriever.get_test_patterns.called_with(feature="login", k=3)

    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_retrieve_failure_patterns(self, mock_retriever_class, pattern_tool):
        """Test retrieving failure insights"""
        mock_retriever = Mock()
        mock_retriever.get_failure_insights.return_value = [
            {
                "content": "Similar failure case",
                "score": 0.9,
                "metadata": {"test_name": "Failed test"}
            }
        ]
        mock_retriever_class.return_value = mock_retriever

        result = pattern_tool.execute(
            pattern_type="failure",
            error_message="Connection timeout",
            k=3
        )

        assert result.is_success()
        assert result.data["pattern_type"] == "failure"
        assert result.data["count"] == 1
        assert mock_retriever.get_failure_insights.called

    def test_feature_pattern_without_feature(self, pattern_tool):
        """Test feature pattern retrieval without feature parameter"""
        result = pattern_tool.execute(
            pattern_type="feature",
            k=3
        )

        assert result.is_failure()
        assert "feature parameter is required" in result.error

    def test_failure_pattern_without_error_message(self, pattern_tool):
        """Test failure pattern without error message"""
        result = pattern_tool.execute(
            pattern_type="failure",
            k=3
        )

        assert result.is_failure()
        assert "error_message parameter is required" in result.error

    def test_invalid_pattern_type(self, pattern_tool):
        """Test with invalid pattern type"""
        result = pattern_tool.execute(
            pattern_type="invalid_type",
            feature="test",
            k=3
        )

        assert result.is_failure()
        assert "Invalid pattern_type" in result.error

    def test_invalid_k_value(self, pattern_tool):
        """Test with invalid k values"""
        result = pattern_tool.execute(
            pattern_type="feature",
            feature="test",
            k=0
        )
        assert result.is_failure()

        result = pattern_tool.execute(
            pattern_type="feature",
            feature="test",
            k=21
        )
        assert result.is_failure()

    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_similar_pattern_retrieval(self, mock_retriever_class, pattern_tool):
        """Test retrieving similar test patterns"""
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.return_value = [
            {"content": "Similar test", "score": 0.8, "metadata": {}}
        ]
        mock_retriever_class.return_value = mock_retriever

        result = pattern_tool.execute(
            pattern_type="similar",
            feature="authentication",
            k=5
        )

        assert result.is_success()
        assert result.data["pattern_type"] == "similar"
        assert mock_retriever.find_similar_tests.called


@pytest.mark.unit
class TestRAGToolsIntegration:
    """Integration tests for RAG tools"""

    def test_register_vector_search_tool(self):
        """Test registering VectorSearchTool"""
        ToolRegistry.register(VectorSearchTool)

        metadata = ToolRegistry.get_metadata("vector_search")
        assert metadata.name == "vector_search"
        assert "rag" in metadata.tags

    def test_register_pattern_retriever_tool(self):
        """Test registering TestPatternRetrieverTool"""
        ToolRegistry.register(TestPatternRetrieverTool)

        metadata = ToolRegistry.get_metadata("test_pattern_retriever")
        assert metadata.name == "test_pattern_retriever"
        assert "patterns" in metadata.tags

    def test_list_rag_tools(self):
        """Test listing RAG tools by tag"""
        ToolRegistry.register(VectorSearchTool)
        ToolRegistry.register(TestPatternRetrieverTool)

        rag_tools = ToolRegistry.list_tools(tags=["rag"])

        assert len(rag_tools) == 2
        tool_names = [t.name for t in rag_tools]
        assert "vector_search" in tool_names
        assert "test_pattern_retriever" in tool_names
