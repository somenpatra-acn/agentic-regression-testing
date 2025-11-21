"""API adapter for REST/GraphQL API testing."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import requests
from requests.auth import HTTPBasicAuth

from adapters.base_adapter import BaseApplicationAdapter, Element, DiscoveryResult
from models.test_case import TestCase, TestStep
from models.test_result import TestResult, TestStatus, TestMetrics
from utils.logger import get_logger
from utils.helpers import generate_result_id

logger = get_logger(__name__)


class APIAdapter(BaseApplicationAdapter):
    """Adapter for API testing."""

    def __init__(self, app_profile):
        """Initialize API adapter."""
        super().__init__(app_profile)
        self.session = requests.Session()
        self._setup_auth()

    def _setup_auth(self) -> None:
        """Set up authentication for API requests."""
        auth = self.app_profile.auth

        if auth.auth_type == "basic":
            self.session.auth = HTTPBasicAuth(auth.username, auth.password)
        elif auth.auth_type == "bearer":
            self.session.headers["Authorization"] = f"Bearer {auth.token}"
        elif auth.auth_type == "api_key":
            self.session.headers["X-API-Key"] = auth.api_key

        # Add custom headers
        self.session.headers.update(auth.custom_headers)

    def authenticate(self) -> bool:
        """Authenticate with the API."""
        try:
            # Test authentication with a simple GET request
            response = self.session.get(self.app_profile.base_url, timeout=10)
            return response.status_code != 401

        except Exception as e:
            logger.error(f"API authentication failed: {e}")
            return False

    def discover_elements(self) -> DiscoveryResult:
        """Discover API endpoints from OpenAPI spec or exploration."""
        logger.info(f"Starting API discovery for {self.name}")

        result = DiscoveryResult()
        config = self.app_profile.discovery

        if not config.enabled:
            return result

        # Try to load OpenAPI spec
        if config.openapi_spec:
            try:
                response = self.session.get(config.openapi_spec, timeout=30)
                if response.status_code == 200:
                    openapi_data = response.json()
                    result = self._parse_openapi(openapi_data)
                    logger.info(f"Discovered {len(result.apis)} API endpoints from OpenAPI spec")
            except Exception as e:
                logger.warning(f"Failed to load OpenAPI spec: {e}")

        # Fallback: try common endpoints
        if not result.apis:
            result = self._discover_common_endpoints()

        return result

    def _parse_openapi(self, openapi_data: Dict) -> DiscoveryResult:
        """Parse OpenAPI specification to discover endpoints."""
        result = DiscoveryResult()

        paths = openapi_data.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue

                api_info = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "parameters": details.get("parameters", []),
                    "request_body": details.get("requestBody", {}),
                    "responses": details.get("responses", {}),
                }

                result.apis.append(api_info)

                # Create element for each endpoint
                element = Element(
                    id=f"{method}_{path.replace('/', '_')}",
                    type="api_endpoint",
                    name=f"{method.upper()} {path}",
                    endpoint=path,
                    attributes={
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                    }
                )
                result.elements.append(element)

        return result

    def _discover_common_endpoints(self) -> DiscoveryResult:
        """Discover common REST API endpoints by testing."""
        result = DiscoveryResult()

        common_paths = [
            "/health", "/status", "/version",
            "/api/v1", "/api/v2",
            "/users", "/products", "/orders",
        ]

        for path in common_paths:
            try:
                url = f"{self.app_profile.base_url}{path}"
                response = self.session.get(url, timeout=5)

                if response.status_code < 500:  # Not a server error
                    result.apis.append({
                        "path": path,
                        "method": "GET",
                        "status_code": response.status_code
                    })

                    element = Element(
                        id=f"get_{path.replace('/', '_')}",
                        type="api_endpoint",
                        name=f"GET {path}",
                        endpoint=path,
                        attributes={"method": "GET"}
                    )
                    result.elements.append(element)

            except requests.exceptions.Timeout:
                logger.debug(f"Timeout discovering {path}")
            except Exception as e:
                logger.debug(f"Error discovering {path}: {e}")

        return result

    def execute_test(self, test_case: TestCase) -> TestResult:
        """Execute API test case."""
        logger.info(f"Executing API test: {test_case.name}")

        start_time = datetime.utcnow()

        result = TestResult(
            id=generate_result_id(),
            test_case_id=test_case.id,
            test_name=test_case.name,
            status=TestStatus.RUNNING,
            metrics=TestMetrics(
                duration_seconds=0,
                start_time=start_time,
                end_time=start_time
            )
        )

        try:
            for step in test_case.steps:
                step_result = self._execute_api_step(step)

                result.add_step_result(
                    step_number=step.step_number,
                    status=step_result["status"],
                    actual_result=step_result["actual"],
                    duration_seconds=step_result["duration"],
                )

                if step_result["status"] == TestStatus.FAILED:
                    result.status = TestStatus.FAILED
                    result.error_message = step_result.get("error")
                    break

            if result.status == TestStatus.RUNNING:
                result.status = TestStatus.PASSED

        except Exception as e:
            logger.error(f"API test execution failed: {e}")
            result.status = TestStatus.ERROR
            result.error_message = str(e)

        end_time = datetime.utcnow()
        result.metrics.end_time = end_time
        result.metrics.duration_seconds = (end_time - start_time).total_seconds()

        return result

    def _execute_api_step(self, step: TestStep) -> Dict[str, Any]:
        """Execute a single API test step."""
        step_start = datetime.utcnow()

        try:
            action = step.action.lower()
            endpoint = step.target

            if not endpoint.startswith("http"):
                endpoint = f"{self.app_profile.base_url}{endpoint}"

            # Extract HTTP method and data
            method = "GET"
            if action in ["get", "post", "put", "delete", "patch"]:
                method = action.upper()

            data = step.input_data or {}
            json_data = data.get("json", data.get("body"))
            params = data.get("params", {})

            # Make API request
            response = self.session.request(
                method=method,
                url=endpoint,
                json=json_data,
                params=params,
                timeout=30
            )

            # Check expected result
            expected_status = data.get("expected_status", 200)

            if response.status_code == expected_status:
                actual = f"{method} {endpoint} returned {response.status_code}"
                status = TestStatus.PASSED
            else:
                actual = f"{method} {endpoint} returned {response.status_code}, expected {expected_status}"
                status = TestStatus.FAILED

            duration = (datetime.utcnow() - step_start).total_seconds()

            return {
                "status": status,
                "actual": actual,
                "duration": duration,
                "response": response.json() if response.content else None
            }

        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            return {
                "status": TestStatus.FAILED,
                "actual": f"API call failed: {str(e)}",
                "error": str(e),
                "duration": duration
            }

    def validate_state(self) -> bool:
        """Validate API is accessible."""
        try:
            response = self.session.get(self.app_profile.base_url, timeout=10)
            return response.status_code < 500
        except Exception as e:
            logger.error(f"API state validation failed: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up session."""
        self.session.close()
        logger.info(f"API adapter cleanup complete for {self.name}")

    def get_capabilities(self) -> Dict[str, bool]:
        """Get adapter capabilities."""
        return {
            "ui_testing": False,
            "api_testing": True,
            "database_testing": False,
            "screenshot_capture": False,
            "video_recording": False,
            "log_capture": True,
        }
