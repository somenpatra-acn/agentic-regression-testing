"""
Unit Tests for Planning Tools

Tests TestPlanGeneratorTool and TestCaseExtractorTool with mocked LLMs.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.planning.test_plan_generator import TestPlanGeneratorTool
from tools.planning.test_case_extractor import TestCaseExtractorTool
from tools.base import ToolStatus, ToolRegistry


@pytest.mark.unit
class TestTestPlanGeneratorTool:
    """Test TestPlanGeneratorTool"""

    @pytest.fixture
    def generator_tool(self):
        """Create test plan generator tool"""
        return TestPlanGeneratorTool()

    def test_tool_metadata(self, generator_tool):
        """Test tool metadata"""
        metadata = generator_tool.metadata

        assert metadata.name == "test_plan_generator"
        assert metadata.version == "1.0.0"
        assert "planning" in metadata.tags
        assert "llm" in metadata.tags

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    def test_successful_plan_generation(self, mock_get_llm, generator_tool):
        """Test successful test plan generation"""
        # Setup mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """
# Test Plan

## Test Strategy
Comprehensive testing approach for login feature

## Test Cases
1. Valid Login Test
   - Priority: high
   - Type: functional
   - Description: Verify successful login with valid credentials

2. Invalid Credentials Test
   - Priority: high
   - Type: negative
   - Description: Verify error message with invalid credentials

## Coverage
- Authentication flow
- Session management
- Error handling

## Gaps
- Performance testing
- Security testing

## Recommendations
- Add load testing
- Implement penetration testing
"""
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        # Execute generation
        result = generator_tool.execute(
            feature_description="User login functionality",
            app_name="My App",
            app_type="web"
        )

        # Assertions
        assert result.is_success()
        assert "plan_id" in result.data
        assert "llm_response" in result.data
        assert "summary" in result.data
        assert result.data["llm_response"] == mock_response.content
        assert result.metadata["feature"] == "User login functionality"
        assert mock_llm.invoke.called

    def test_empty_feature_description(self, generator_tool):
        """Test with empty feature description"""
        result = generator_tool.execute(
            feature_description="",
            app_name="App",
            app_type="web"
        )

        assert result.is_failure()
        assert "cannot be empty" in result.error.lower()

    def test_empty_app_name(self, generator_tool):
        """Test with empty app name"""
        result = generator_tool.execute(
            feature_description="Feature",
            app_name="",
            app_type="web"
        )

        assert result.is_failure()
        assert "cannot be empty" in result.error.lower()

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    def test_with_discovery_info(self, mock_get_llm, generator_tool):
        """Test plan generation with discovery information"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test plan with discovery context"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        discovery_info = {
            "total_elements": 10,
            "total_pages": 5,
            "element_types": {"button": 3, "input": 5}
        }

        result = generator_tool.execute(
            feature_description="Feature",
            app_name="App",
            discovery_info=discovery_info
        )

        assert result.is_success()
        assert result.metadata["has_discovery_info"] is True

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    def test_with_similar_tests(self, mock_get_llm, generator_tool):
        """Test with similar tests context"""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test plan with similar tests"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        similar_tests = [
            {
                "content": "Similar test 1",
                "metadata": {"test_name": "Test 1"},
                "score": 0.9
            }
        ]

        result = generator_tool.execute(
            feature_description="Feature",
            app_name="App",
            similar_tests=similar_tests
        )

        assert result.is_success()
        assert result.metadata["similar_tests_count"] == 1

    @patch('tools.planning.test_plan_generator.get_smart_llm')
    def test_llm_exception(self, mock_get_llm, generator_tool):
        """Test LLM exception handling"""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("LLM API error")
        mock_get_llm.return_value = mock_llm

        result = generator_tool.execute(
            feature_description="Feature",
            app_name="App"
        )

        assert result.is_failure()
        assert result.status == ToolStatus.ERROR
        assert "Test plan generation failed" in result.error


@pytest.mark.unit
class TestTestCaseExtractorTool:
    """Test TestCaseExtractorTool"""

    @pytest.fixture
    def extractor_tool(self):
        """Create test case extractor tool"""
        return TestCaseExtractorTool()

    @pytest.fixture
    def sample_llm_response(self):
        """Sample LLM response"""
        return """
# Test Plan

## Test Cases

### 1. Valid Login Test
- **Description**: Verify successful login with valid credentials
- **Priority**: high
- **Type**: functional
- **Preconditions**: User exists in system
- **Test Steps**:
  1. Navigate to login page
  2. Enter valid username
  3. Enter valid password
  4. Click login button
- **Expected Result**: User is logged in successfully

### 2. Invalid Login Test
- **Description**: Verify error message with invalid credentials
- **Priority**: medium
- **Type**: negative
- **Preconditions**: None
- **Test Steps**:
  1. Navigate to login page
  2. Enter invalid credentials
  3. Click login button
- **Expected Result**: Error message displayed

## Coverage
- Authentication
- Error handling

## Gaps
- Performance testing

## Recommendations
- Add load tests
"""

    def test_tool_metadata(self, extractor_tool):
        """Test tool metadata"""
        metadata = extractor_tool.metadata

        assert metadata.name == "test_case_extractor"
        assert metadata.version == "1.0.0"
        assert "extraction" in metadata.tags
        assert metadata.is_safe is True

    def test_successful_extraction(self, extractor_tool, sample_llm_response):
        """Test successful test case extraction"""
        result = extractor_tool.execute(
            llm_response=sample_llm_response,
            app_name="My App",
            feature="Login"
        )

        assert result.is_success()
        assert "test_cases" in result.data
        assert result.data["count"] >= 2
        assert len(result.data["test_cases"]) >= 2

        # Check first test case structure
        test_case = result.data["test_cases"][0]
        assert "id" in test_case
        assert "name" in test_case
        assert "description" in test_case
        assert "priority" in test_case
        assert "type" in test_case
        assert test_case["application"] == "My App"
        assert test_case["feature"] == "Login"

    def test_empty_llm_response(self, extractor_tool):
        """Test with empty LLM response"""
        result = extractor_tool.execute(
            llm_response="",
            app_name="App",
            feature="Feature"
        )

        assert result.is_failure()
        assert "cannot be empty" in result.error.lower()

    def test_extraction_with_no_test_cases(self, extractor_tool):
        """Test extraction when no test cases found"""
        result = extractor_tool.execute(
            llm_response="This is a test plan with no clear test cases.",
            app_name="App",
            feature="Feature"
        )

        assert result.is_success()
        # Should create default test cases
        assert result.data["count"] >= 2
        assert len(result.data["test_cases"]) >= 2

    def test_section_extraction(self, extractor_tool, sample_llm_response):
        """Test extraction of sections"""
        result = extractor_tool.execute(
            llm_response=sample_llm_response,
            app_name="App",
            feature="Feature"
        )

        assert result.is_success()
        raw_sections = result.data["raw_sections"]
        assert "coverage" in raw_sections
        assert "gaps" in raw_sections
        assert "recommendations" in raw_sections

    def test_test_case_with_priority(self, extractor_tool):
        """Test extracting test case with priority"""
        llm_response = """
### Test Case 1: Critical Login Test
- Priority: critical
- Description: Test critical login path
"""
        result = extractor_tool.execute(
            llm_response=llm_response,
            app_name="App",
            feature="Login"
        )

        assert result.is_success()
        if result.data["count"] > 0:
            test_case = result.data["test_cases"][0]
            assert test_case["priority"] == "critical"

    def test_test_case_with_steps(self, extractor_tool):
        """Test extracting test case with steps"""
        llm_response = """
### Login Test
- Steps:
  1. Open browser
  2. Navigate to login page
  3. Enter credentials
"""
        result = extractor_tool.execute(
            llm_response=llm_response,
            app_name="App",
            feature="Login"
        )

        assert result.is_success()


@pytest.mark.unit
class TestPlanningToolsIntegration:
    """Integration tests for planning tools"""

    def test_register_plan_generator_tool(self):
        """Test registering TestPlanGeneratorTool"""
        ToolRegistry.register(TestPlanGeneratorTool)

        metadata = ToolRegistry.get_metadata("test_plan_generator")
        assert metadata.name == "test_plan_generator"
        assert "planning" in metadata.tags

    def test_register_test_case_extractor_tool(self):
        """Test registering TestCaseExtractorTool"""
        ToolRegistry.register(TestCaseExtractorTool)

        metadata = ToolRegistry.get_metadata("test_case_extractor")
        assert metadata.name == "test_case_extractor"
        assert "extraction" in metadata.tags

    def test_list_planning_tools(self):
        """Test listing planning tools by tag"""
        ToolRegistry.register(TestPlanGeneratorTool)
        ToolRegistry.register(TestCaseExtractorTool)

        planning_tools = ToolRegistry.list_tools(tags=["planning"])

        assert len(planning_tools) == 2
        tool_names = [t.name for t in planning_tools]
        assert "test_plan_generator" in tool_names
        assert "test_case_extractor" in tool_names
