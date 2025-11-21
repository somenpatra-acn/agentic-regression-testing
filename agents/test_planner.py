"""Test Planner Agent - creates comprehensive test plans."""

from typing import Any, Dict, List, Optional

from langchain_core.prompts import PromptTemplate

from config.llm_config import get_smart_llm
from models.app_profile import ApplicationProfile
from models.test_case import TestCase, TestPriority, TestType
from adapters.base_adapter import DiscoveryResult
from rag.retriever import TestKnowledgeRetriever
from utils.logger import get_logger
from utils.helpers import generate_test_id

logger = get_logger(__name__)


class TestPlannerAgent:
    """
    Test Planner Agent creates comprehensive test plans by:
    - Analyzing discovery results
    - Retrieving similar tests from knowledge base
    - Identifying test coverage gaps
    - Prioritizing test cases
    """

    def __init__(self, app_profile: ApplicationProfile):
        """
        Initialize Test Planner Agent.

        Args:
            app_profile: Application profile
        """
        self.app_profile = app_profile
        self.llm = get_smart_llm()
        self.knowledge_retriever = TestKnowledgeRetriever()

        self.last_plan: Optional[Dict[str, Any]] = None

        logger.info(f"TestPlannerAgent initialized for {app_profile.name}")

    def create_plan(
        self,
        feature_description: str,
        discovery_result: Optional[DiscoveryResult] = None
    ) -> Dict[str, Any]:
        """
        Create a comprehensive test plan.

        Args:
            feature_description: Description of feature to test
            discovery_result: Optional discovery results

        Returns:
            Test plan dictionary
        """
        logger.info(f"Creating test plan for: {feature_description}")

        # Get similar tests from knowledge base
        similar_tests = self.knowledge_retriever.find_similar_tests(
            query=feature_description,
            k=5,
            application=self.app_profile.name
        )

        # Create test plan using LLM
        test_plan = self._generate_plan_with_llm(
            feature_description,
            discovery_result,
            similar_tests
        )

        # Store plan
        self.last_plan = test_plan

        logger.info(f"Test plan created with {len(test_plan.get('test_cases', []))} test cases")

        return test_plan

    def _generate_plan_with_llm(
        self,
        feature_description: str,
        discovery_result: Optional[DiscoveryResult],
        similar_tests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate test plan using LLM."""
        prompt_template = PromptTemplate.from_template("""
You are a test planning expert. Create a comprehensive test plan for the following feature.

Feature Description:
{feature_description}

Application: {app_name}
Application Type: {app_type}

Discovery Information:
{discovery_info}

Similar Historical Tests:
{similar_tests}

Create a test plan that includes:
1. List of test cases with names and descriptions
2. Test priorities (critical, high, medium, low)
3. Coverage areas
4. Identified gaps
5. Recommendations

Format your response as a structured plan with clear sections.
""")

        discovery_info = "No discovery data available"
        if discovery_result:
            discovery_info = f"""
- Elements: {len(discovery_result.elements)}
- Pages: {len(discovery_result.pages)}
- APIs: {len(discovery_result.apis)}
"""

        similar_tests_info = "No similar tests found"
        if similar_tests:
            similar_tests_info = "\n".join([
                f"- {test['metadata'].get('test_name', 'Unknown')}: {test['content'][:100]}..."
                for test in similar_tests[:3]
            ])

        prompt = prompt_template.format(
            feature_description=feature_description,
            app_name=self.app_profile.name,
            app_type=self.app_profile.app_type.value,
            discovery_info=discovery_info,
            similar_tests=similar_tests_info
        )

        response = self.llm.invoke(prompt)

        # Parse LLM response into structured plan
        # (In production, would use structured output or JSON mode)
        plan = {
            "id": generate_test_id(),
            "feature": feature_description,
            "application": self.app_profile.name,
            "llm_response": response.content,
            "test_cases": self._extract_test_cases(response.content),
            "coverage": ["authentication", "functional", "error_handling"],
            "gaps": ["performance testing", "security testing"],
            "recommendations": ["Add load testing", "Implement E2E scenarios"]
        }

        return plan

    def _extract_test_cases(self, llm_response: str) -> List[Dict[str, Any]]:
        """Extract test cases from LLM response (simplified)."""
        # In production, this would parse the LLM response properly
        # For now, create sample test cases
        test_cases = [
            {
                "id": generate_test_id(),
                "name": "Test Case 1",
                "description": "Verify basic functionality",
                "priority": "high",
                "type": "functional"
            },
            {
                "id": generate_test_id(),
                "name": "Test Case 2",
                "description": "Verify error handling",
                "priority": "medium",
                "type": "negative"
            }
        ]

        return test_cases

    def get_last_plan(self) -> Optional[Dict[str, Any]]:
        """Get the last created test plan."""
        return self.last_plan
