"""
Test Case Extractor Tool

Extracts structured test case information from LLM-generated test plans.
"""

import re
from typing import Dict, Any, List, Optional
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata
from utils.helpers import generate_test_id


class TestCaseExtractorTool(BaseTool):
    """
    Extracts structured test cases from text

    This tool parses LLM-generated test plans and extracts
    structured test case information including:
    - Test case names and descriptions
    - Priorities
    - Test types
    - Preconditions
    - Test steps
    - Expected results

    Features:
    - Regex-based extraction
    - Markdown parsing
    - Structured output
    - Validation and cleanup
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="test_case_extractor",
            description="Extracts structured test cases from LLM-generated test plans",
            version="1.0.0",
            tags=["planning", "extraction", "parsing"],
            requires_auth=False,
            is_safe=True,
            input_schema={
                "llm_response": "string - LLM-generated test plan text",
                "app_name": "string - Application name",
                "feature": "string - Feature name",
            },
            output_schema={
                "test_cases": "list - Extracted test cases with structured data",
                "count": "integer - Number of test cases extracted",
                "raw_sections": "dict - Raw extracted sections",
            }
        )

    def execute(
        self,
        llm_response: str,
        app_name: str,
        feature: str,
    ) -> ToolResult:
        """
        Extract test cases from LLM response

        Args:
            llm_response: LLM-generated test plan text
            app_name: Application name
            feature: Feature name

        Returns:
            ToolResult with extracted test cases
        """
        return self._wrap_execution(
            self._extract,
            llm_response=llm_response,
            app_name=app_name,
            feature=feature,
        )

    def _extract(
        self,
        llm_response: str,
        app_name: str,
        feature: str,
    ) -> ToolResult:
        """Internal extraction logic"""

        if not llm_response or not llm_response.strip():
            return ToolResult(
                status=ToolStatus.FAILURE,
                error="llm_response cannot be empty",
            )

        try:
            # Extract test cases section
            test_cases_section = self._extract_test_cases_section(llm_response)

            # Parse individual test cases
            test_cases = self._parse_test_cases(
                test_cases_section,
                app_name=app_name,
                feature=feature
            )

            # Extract other sections for context
            coverage = self._extract_section(llm_response, "coverage")
            gaps = self._extract_section(llm_response, "gap")
            recommendations = self._extract_section(llm_response, "recommendation")

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "test_cases": test_cases,
                    "count": len(test_cases),
                    "raw_sections": {
                        "coverage": coverage,
                        "gaps": gaps,
                        "recommendations": recommendations,
                    }
                },
                metadata={
                    "app_name": app_name,
                    "feature": feature,
                    "response_length": len(llm_response),
                    "extraction_method": "regex",
                }
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Test case extraction failed: {str(e)}",
                metadata={
                    "app_name": app_name,
                    "feature": feature,
                    "exception_type": type(e).__name__,
                }
            )

    def _extract_test_cases_section(self, text: str) -> str:
        """Extract the test cases section from the response"""
        # Look for test cases section
        patterns = [
            r"(?:##\s*Test Cases|###\s*Test Cases)(.*?)(?=##|\Z)",
            r"(?:Test Cases:)(.*?)(?=\n##|\Z)",
            r"(?:2\.\s*\*\*Test Cases\*\*)(.*?)(?=\n\d+\.|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # If no section found, use the whole text
        return text

    def _parse_test_cases(
        self,
        text: str,
        app_name: str,
        feature: str
    ) -> List[Dict[str, Any]]:
        """Parse individual test cases from text"""
        test_cases = []

        # Try different patterns to find test cases
        # Pattern 1: Numbered list with details
        pattern1 = r"(?:####\s+|###\s+|\d+\.\s+)(.+?)\n(.*?)(?=####|###|\d+\.\s+|\Z)"

        matches = re.finditer(pattern1, text, re.DOTALL)

        for match in matches:
            title = match.group(1).strip()
            content = match.group(2).strip()

            # Skip if this looks like a section header not a test case
            if any(skip in title.lower() for skip in ["coverage", "gap", "recommendation", "strategy"]):
                continue

            test_case = self._parse_single_test_case(
                title=title,
                content=content,
                app_name=app_name,
                feature=feature
            )

            if test_case:
                test_cases.append(test_case)

        # If no test cases found, create default ones
        if not test_cases:
            test_cases = self._create_default_test_cases(app_name, feature)

        return test_cases

    def _parse_single_test_case(
        self,
        title: str,
        content: str,
        app_name: str,
        feature: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a single test case"""
        # Extract priority
        priority = "medium"  # default
        priority_match = re.search(r"priority:\s*(\w+)", content, re.IGNORECASE)
        if priority_match:
            priority = priority_match.group(1).lower()

        # Extract test type
        test_type = "functional"  # default
        type_match = re.search(r"type:\s*(\w+)", content, re.IGNORECASE)
        if type_match:
            test_type = type_match.group(1).lower()

        # Extract description
        description = ""
        desc_match = re.search(r"description:\s*(.+?)(?=\n\w+:|\Z)", content, re.IGNORECASE | re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()
        elif len(content) < 200:
            description = content.strip()
        else:
            description = content[:200].strip() + "..."

        # Extract preconditions
        preconditions = []
        precond_match = re.search(r"preconditions?:\s*(.+?)(?=\n\w+:|\Z)", content, re.IGNORECASE | re.DOTALL)
        if precond_match:
            precond_text = precond_match.group(1).strip()
            preconditions = [p.strip("- ").strip() for p in precond_text.split("\n") if p.strip()]

        # Extract test steps
        steps = []
        steps_match = re.search(r"(?:test\s+)?steps:\s*(.+?)(?=\n\w+:|\Z)", content, re.IGNORECASE | re.DOTALL)
        if steps_match:
            steps_text = steps_match.group(1).strip()
            step_lines = [s.strip("- ").strip() for s in steps_text.split("\n") if s.strip()]
            steps = [{"step_number": i+1, "action": step} for i, step in enumerate(step_lines)]

        return {
            "id": generate_test_id(),
            "name": title.strip("*").strip(),
            "description": description,
            "priority": priority,
            "type": test_type,
            "application": app_name,
            "feature": feature,
            "preconditions": preconditions,
            "steps": steps,
        }

    def _create_default_test_cases(
        self,
        app_name: str,
        feature: str
    ) -> List[Dict[str, Any]]:
        """Create default test cases when parsing fails"""
        return [
            {
                "id": generate_test_id(),
                "name": f"{feature} - Basic Functionality Test",
                "description": f"Verify basic functionality of {feature}",
                "priority": "high",
                "type": "functional",
                "application": app_name,
                "feature": feature,
                "preconditions": [],
                "steps": [],
            },
            {
                "id": generate_test_id(),
                "name": f"{feature} - Error Handling Test",
                "description": f"Verify error handling in {feature}",
                "priority": "medium",
                "type": "negative",
                "application": app_name,
                "feature": feature,
                "preconditions": [],
                "steps": [],
            }
        ]

    def _extract_section(self, text: str, section_keyword: str) -> str:
        """Extract a specific section from the text"""
        patterns = [
            rf"(?:##\s*{section_keyword}.*?)(.*?)(?=##|\Z)",
            rf"(?:\d+\.\s*\*\*{section_keyword}.*?\*\*)(.*?)(?=\n\d+\.|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""
