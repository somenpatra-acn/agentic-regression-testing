"""
Test Plan Generator Tool

Generates comprehensive test plans using LLM based on feature descriptions and context.
"""

from typing import Dict, Any, Optional, List
from langchain_core.prompts import PromptTemplate

from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata
from config.llm_config import get_smart_llm
from utils.helpers import generate_test_id


class TestPlanGeneratorTool(BaseTool):
    """
    Generates test plans using LLM

    This tool uses a smart LLM (GPT-4/Claude Opus) to generate
    comprehensive test plans based on:
    - Feature descriptions
    - Discovery results
    - Similar historical tests
    - Application context

    Features:
    - Uses smart LLM for complex reasoning
    - Structured prompt engineering
    - Context-aware generation
    - Includes coverage and gap analysis
    """

    def _validate_config(self) -> None:
        """Validate tool configuration"""
        # app_profile is optional but helpful for context
        pass

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="test_plan_generator",
            description="Generates comprehensive test plans using LLM with RAG context",
            version="1.0.0",
            tags=["planning", "llm", "generation"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "feature_description": "string - Description of feature to test",
                "app_name": "string - Application name",
                "app_type": "string - Application type (web, api, etc)",
                "discovery_info": "dict - Discovery results summary",
                "similar_tests": "list - Similar historical tests for context",
                "additional_context": "string - Any additional context",
            },
            output_schema={
                "plan_id": "string - Generated plan ID",
                "llm_response": "string - Full LLM response",
                "summary": "dict - Plan summary with key information",
            }
        )

    def execute(
        self,
        feature_description: str,
        app_name: str,
        app_type: str = "web",
        discovery_info: Optional[Dict[str, Any]] = None,
        similar_tests: Optional[List[Dict[str, Any]]] = None,
        additional_context: Optional[str] = None,
    ) -> ToolResult:
        """
        Generate a test plan using LLM

        Args:
            feature_description: Feature to test
            app_name: Application name
            app_type: Type of application
            discovery_info: Discovery results summary
            similar_tests: Similar historical tests
            additional_context: Additional context

        Returns:
            ToolResult with generated test plan
        """
        return self._wrap_execution(
            self._generate,
            feature_description=feature_description,
            app_name=app_name,
            app_type=app_type,
            discovery_info=discovery_info,
            similar_tests=similar_tests,
            additional_context=additional_context,
        )

    def _generate(
        self,
        feature_description: str,
        app_name: str,
        app_type: str,
        discovery_info: Optional[Dict[str, Any]],
        similar_tests: Optional[List[Dict[str, Any]]],
        additional_context: Optional[str],
    ) -> ToolResult:
        """Internal generation logic"""

        if not feature_description or not feature_description.strip():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="feature_description cannot be empty",
            )

        if not app_name or not app_name.strip():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="app_name cannot be empty",
            )

        try:
            # Get smart LLM for complex reasoning
            llm = get_smart_llm()

            # Build prompt
            prompt = self._build_prompt(
                feature_description=feature_description,
                app_name=app_name,
                app_type=app_type,
                discovery_info=discovery_info,
                similar_tests=similar_tests,
                additional_context=additional_context,
            )

            # Generate plan with LLM
            response = llm.invoke(prompt)

            # Generate plan ID
            plan_id = generate_test_id()

            # Extract summary information from response
            summary = self._extract_summary(response.content)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "plan_id": plan_id,
                    "llm_response": response.content,
                    "summary": summary,
                },
                metadata={
                    "feature": feature_description,
                    "app_name": app_name,
                    "app_type": app_type,
                    "has_discovery_info": discovery_info is not None,
                    "similar_tests_count": len(similar_tests) if similar_tests else 0,
                    "llm_model": getattr(llm, "model_name", "unknown"),
                    "response_length": len(response.content),
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Test plan generation failed: {str(e)}",
                metadata={
                    "feature": feature_description,
                    "app_name": app_name,
                    "exception_type": type(e).__name__,
                }
            )

    def _build_prompt(
        self,
        feature_description: str,
        app_name: str,
        app_type: str,
        discovery_info: Optional[Dict[str, Any]],
        similar_tests: Optional[List[Dict[str, Any]]],
        additional_context: Optional[str],
    ) -> str:
        """Build the LLM prompt for test plan generation"""

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

{additional_context}

Create a comprehensive test plan that includes:

1. **Test Strategy**: Overall approach and methodology

2. **Test Cases**: List of test cases with:
   - Test case name
   - Description
   - Priority (critical, high, medium, low)
   - Type (functional, negative, boundary, security, performance)
   - Preconditions
   - Test steps
   - Expected results

3. **Coverage Analysis**: Areas covered by the tests

4. **Gap Analysis**: Identified gaps in testing coverage

5. **Recommendations**: Suggestions for additional testing

6. **Test Data Requirements**: Data needed for testing

7. **Environment Requirements**: Testing environment needs

Format your response with clear sections and structured information.
Use markdown formatting for readability.
""")

        # Format discovery info
        discovery_info_str = "No discovery data available"
        if discovery_info:
            parts = []
            if "total_elements" in discovery_info:
                parts.append(f"- Elements: {discovery_info['total_elements']}")
            if "total_pages" in discovery_info:
                parts.append(f"- Pages: {discovery_info['total_pages']}")
            if "total_endpoints" in discovery_info:
                parts.append(f"- API Endpoints: {discovery_info['total_endpoints']}")
            if "element_types" in discovery_info:
                parts.append(f"- Element Types: {discovery_info['element_types']}")

            discovery_info_str = "\n".join(parts) if parts else "Discovery completed"

        # Format similar tests
        similar_tests_str = "No similar tests found"
        if similar_tests:
            similar_tests_list = []
            for test in similar_tests[:3]:  # Limit to top 3
                test_name = test.get("metadata", {}).get("test_name", "Unknown")
                content = test.get("content", "")[:150]  # Truncate
                score = test.get("score", 0.0)
                similar_tests_list.append(
                    f"- **{test_name}** (similarity: {score:.2f}):\n  {content}..."
                )
            similar_tests_str = "\n".join(similar_tests_list)

        # Format additional context
        additional_context_str = ""
        if additional_context:
            additional_context_str = f"\nAdditional Context:\n{additional_context}"

        # Generate prompt
        prompt = prompt_template.format(
            feature_description=feature_description,
            app_name=app_name,
            app_type=app_type,
            discovery_info=discovery_info_str,
            similar_tests=similar_tests_str,
            additional_context=additional_context_str,
        )

        return prompt

    def _extract_summary(self, llm_response: str) -> Dict[str, Any]:
        """Extract summary information from LLM response"""
        # Simple extraction - in production, use structured output or parsing
        summary = {
            "has_test_strategy": "test strategy" in llm_response.lower(),
            "has_test_cases": "test case" in llm_response.lower(),
            "has_coverage": "coverage" in llm_response.lower(),
            "has_gaps": "gap" in llm_response.lower(),
            "has_recommendations": "recommendation" in llm_response.lower(),
            "response_length": len(llm_response),
            "estimated_test_cases": llm_response.lower().count("test case"),
        }

        return summary
