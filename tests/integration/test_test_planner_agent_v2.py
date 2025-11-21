"""
Integration Tests for Test Planner Agent V2

Tests the complete Test Planner workflow with LangGraph and tools.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agents_v2.test_planner_agent_v2 import TestPlannerAgentV2
from tools.base import ToolRegistry
from tools.validation.input_sanitizer import InputSanitizerTool
from tools.rag.vector_search import VectorSearchTool
from tools.rag.test_pattern_retriever import TestPatternRetrieverTool
from tools.planning.test_plan_generator import TestPlanGeneratorTool
from tools.planning.test_case_extractor import TestCaseExtractorTool


@pytest.mark.integration
class TestTestPlannerAgentV2Integration:
    """Integration tests for Test Planner Agent V2"""

    @pytest.fixture(autouse=True)
    def setup_tools(self):
        """Register all required tools before each test"""
        ToolRegistry.clear()
        ToolRegistry.register(InputSanitizerTool)
        ToolRegistry.register(VectorSearchTool)
        ToolRegistry.register(TestPatternRetrieverTool)
        ToolRegistry.register(TestPlanGeneratorTool)
        ToolRegistry.register(TestCaseExtractorTool)
        yield
        ToolRegistry.clear()

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_complete_planning_workflow(
        self,
        mock_pattern_retriever,
        mock_vector_retriever,
        mock_get_llm,
        sample_web_app_profile
    ):
        """Test complete test planning workflow"""
        # Setup mock RAG retriever
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.return_value = [
            {
                "content": "Similar test content",
                "score": 0.9,
                "metadata": {"test_name": "Login Test", "test_type": "functional"}
            }
        ]
        mock_retriever.get_test_patterns.return_value = [
            "Pattern 1: Authentication flow",
            "Pattern 2: Session management"
        ]
        mock_vector_retriever.return_value = mock_retriever
        mock_pattern_retriever.return_value = mock_retriever

        # Setup mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """
# Test Plan for Login Feature

## Test Strategy
Comprehensive authentication testing

## Test Cases

### 1. Valid Login Test
- **Description**: Verify successful login with valid credentials
- **Priority**: critical
- **Type**: functional
- **Preconditions**: User account exists
- **Test Steps**:
  1. Navigate to login page
  2. Enter valid username
  3. Enter valid password
  4. Click login button
- **Expected Result**: User successfully logged in

### 2. Invalid Credentials Test
- **Description**: Verify error message with invalid credentials
- **Priority**: high
- **Type**: negative
- **Test Steps**:
  1. Navigate to login page
  2. Enter invalid credentials
  3. Click login button
- **Expected Result**: Error message displayed

## Coverage Analysis
- Authentication flow
- Error handling
- Session management

## Gaps
- Performance testing under load
- Security penetration testing

## Recommendations
- Add automated load testing
- Implement security scanning
"""
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        # Create agent
        agent = TestPlannerAgentV2(
            app_profile=sample_web_app_profile,
            enable_hitl=False
        )

        # Execute planning
        final_state = agent.create_plan(
            feature_description="User login functionality",
            discovery_result=None
        )

        # Assertions on state
        assert final_state["status"] == "completed"
        assert len(final_state["similar_tests"]) > 0
        assert len(final_state["test_patterns"]) > 0
        assert final_state["test_plan"] is not None
        assert len(final_state["test_cases"]) >= 2
        assert final_state["error"] is None

        # Get formatted result
        result = agent.get_test_plan(final_state)

        assert result["status"] == "completed"
        assert result["test_plan"]["plan_id"] is not None
        assert len(result["test_cases"]) >= 2
        assert result["statistics"]["similar_tests_found"] > 0
        assert result["metadata"]["execution_time"] is not None

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_planning_with_discovery_results(
        self,
        mock_pattern_retriever,
        mock_vector_retriever,
        mock_get_llm,
        sample_web_app_profile
    ):
        """Test planning with discovery results"""
        # Setup mocks
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.return_value = []
        mock_retriever.get_test_patterns.return_value = []
        mock_vector_retriever.return_value = mock_retriever
        mock_pattern_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test plan with discovery context"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        # Prepare discovery results
        discovery_result = {
            "elements": [{"id": "el1", "type": "button"}],
            "pages": ["/login", "/dashboard"],
            "metadata": {"element_types": {"button": 5, "input": 3}}
        }

        agent = TestPlannerAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.create_plan(
            feature_description="Dashboard functionality",
            discovery_result=discovery_result
        )

        assert final_state["status"] == "completed"
        assert final_state["discovery_result"] == discovery_result

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_input_validation_in_workflow(
        self,
        mock_pattern_retriever,
        mock_vector_retriever,
        mock_get_llm,
        sample_web_app_profile
    ):
        """Test that input validation occurs"""
        # Setup mocks
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.return_value = []
        mock_retriever.get_test_patterns.return_value = []
        mock_vector_retriever.return_value = mock_retriever
        mock_pattern_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test plan"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        agent = TestPlannerAgentV2(app_profile=sample_web_app_profile)

        # Test with potentially malicious input
        final_state = agent.create_plan(
            feature_description="Test <script>alert('xss')</script> feature"
        )

        # Input should be sanitized
        assert final_state["status"] == "completed"
        # Sanitized input should not contain HTML
        assert "<script>" not in final_state["feature_description"]

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    def test_rag_retrieval_failure_handling(
        self,
        mock_vector_retriever,
        mock_get_llm,
        sample_web_app_profile
    ):
        """Test handling of RAG retrieval failures"""
        # Make RAG fail
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.side_effect = Exception("Vector store error")
        mock_retriever.get_test_patterns.side_effect = Exception("Vector store error")
        mock_vector_retriever.return_value = mock_retriever

        # LLM should still work
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test plan without RAG context"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        agent = TestPlannerAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.create_plan(
            feature_description="Feature without RAG"
        )

        # Should complete even without RAG
        assert final_state["status"] == "completed"
        assert len(final_state["similar_tests"]) == 0
        assert len(final_state["test_patterns"]) == 0

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    def test_llm_generation_failure(
        self,
        mock_get_llm,
        sample_web_app_profile
    ):
        """Test handling of LLM generation failures"""
        # Make LLM fail
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("LLM API error")
        mock_get_llm.return_value = mock_llm

        agent = TestPlannerAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.create_plan(
            feature_description="Feature"
        )

        # Should fail gracefully
        assert final_state["status"] == "failed"
        assert final_state["error"] is not None
        assert "Plan generation error" in final_state["error"]

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_execution_timing(
        self,
        mock_pattern_retriever,
        mock_vector_retriever,
        mock_get_llm,
        sample_web_app_profile
    ):
        """Test that execution time is tracked"""
        # Setup mocks
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.return_value = []
        mock_retriever.get_test_patterns.return_value = []
        mock_vector_retriever.return_value = mock_retriever
        mock_pattern_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test plan"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        agent = TestPlannerAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.create_plan(
            feature_description="Feature"
        )

        # Should have timing information
        assert "start_time" in final_state
        assert "end_time" in final_state
        assert final_state["start_time"] < final_state["end_time"]

        # Formatted result should include execution time
        result = agent.get_test_plan(final_state)
        assert result["metadata"]["execution_time"] is not None
        assert result["metadata"]["execution_time"] > 0

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_state_tracking_through_workflow(
        self,
        mock_pattern_retriever,
        mock_vector_retriever,
        mock_get_llm,
        sample_web_app_profile
    ):
        """Test that state is properly tracked"""
        # Setup mocks
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.return_value = [{"content": "test", "score": 0.9, "metadata": {}}]
        mock_retriever.get_test_patterns.return_value = ["pattern1"]
        mock_vector_retriever.return_value = mock_retriever
        mock_pattern_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """
### Test Case 1
- Description: Test
- Priority: high
"""
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        agent = TestPlannerAgentV2(app_profile=sample_web_app_profile)

        final_state = agent.create_plan(
            feature_description="Feature"
        )

        # Verify all state fields
        assert final_state["app_profile"] == sample_web_app_profile
        assert final_state["feature_description"] == "Feature"
        assert final_state["status"] == "completed"
        assert isinstance(final_state["similar_tests"], list)
        assert isinstance(final_state["test_patterns"], list)
        assert isinstance(final_state["test_cases"], list)
        assert final_state["test_plan"] is not None


@pytest.mark.integration
@pytest.mark.slow
class TestTestPlannerAgentV2Performance:
    """Performance tests for Test Planner Agent V2"""

    @pytest.fixture(autouse=True)
    def setup_tools(self):
        """Register all required tools"""
        ToolRegistry.clear()
        ToolRegistry.register(InputSanitizerTool)
        ToolRegistry.register(VectorSearchTool)
        ToolRegistry.register(TestPatternRetrieverTool)
        ToolRegistry.register(TestPlanGeneratorTool)
        ToolRegistry.register(TestCaseExtractorTool)
        yield
        ToolRegistry.clear()

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    @patch('tools.rag.vector_search.TestKnowledgeRetriever')
    @patch('tools.rag.test_pattern_retriever.TestKnowledgeRetriever')
    def test_planning_completes_in_reasonable_time(
        self,
        mock_pattern_retriever,
        mock_vector_retriever,
        mock_get_llm,
        sample_web_app_profile
    ):
        """Test that planning completes in reasonable time"""
        import time

        # Setup mocks
        mock_retriever = Mock()
        mock_retriever.find_similar_tests.return_value = [
            {"content": f"Test {i}", "score": 0.9, "metadata": {}}
            for i in range(10)
        ]
        mock_retriever.get_test_patterns.return_value = [f"Pattern {i}" for i in range(5)]
        mock_vector_retriever.return_value = mock_retriever
        mock_pattern_retriever.return_value = mock_retriever

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Large test plan with many test cases" * 100
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        agent = TestPlannerAgentV2(app_profile=sample_web_app_profile)

        start = time.time()
        final_state = agent.create_plan(feature_description="Complex feature")
        elapsed = time.time() - start

        # Should complete quickly even with large dataset
        assert elapsed < 10.0  # 10 seconds max
        assert final_state["status"] == "completed"
