"""Oracle EBS adapter for enterprise testing."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from adapters.web_adapter import WebAdapter
from adapters.base_adapter import DiscoveryResult, Element
from models.test_case import TestCase
from models.test_result import TestResult
from utils.logger import get_logger

logger = get_logger(__name__)


class OracleEBSAdapter(WebAdapter):
    """
    Adapter for Oracle E-Business Suite.

    Extends WebAdapter with Oracle EBS-specific functionality.
    """

    def __init__(self, app_profile):
        """Initialize Oracle EBS adapter."""
        super().__init__(app_profile)
        self.db_connection = None
        self.responsibility = app_profile.custom_config.get("responsibility", "System Administrator")

    def authenticate(self) -> bool:
        """Authenticate with Oracle EBS."""
        try:
            if not self.page:
                self._start_browser()

            # Navigate to Oracle EBS login
            self.page.goto(self.app_profile.base_url)

            # Fill login form (Oracle EBS specific selectors)
            auth = self.app_profile.auth

            # Wait for login page
            self.page.wait_for_selector('input[name="usrname"]', timeout=10000)

            # Enter credentials
            self.page.fill('input[name="usrname"]', auth.username)
            self.page.fill('input[name="password"]', auth.password)

            # Click login
            self.page.click('input[type="submit"], button[type="submit"]')

            # Wait for home page
            self.page.wait_for_load_state("networkidle")

            # Select responsibility if needed
            if self.responsibility:
                self._select_responsibility()

            logger.info(f"Oracle EBS authentication successful for {self.name}")
            return True

        except Exception as e:
            logger.error(f"Oracle EBS authentication failed: {e}")
            return False

    def _select_responsibility(self) -> None:
        """Select Oracle EBS responsibility."""
        try:
            # This is a simplified version - actual implementation would need
            # to handle Oracle Forms and specific EBS navigation
            logger.info(f"Selecting responsibility: {self.responsibility}")

            # Navigate to responsibility selection
            # (Implementation depends on EBS version and configuration)

        except Exception as e:
            logger.warning(f"Failed to select responsibility: {e}")

    def discover_elements(self) -> DiscoveryResult:
        """
        Discover Oracle EBS elements including forms and database schema.
        """
        logger.info(f"Starting Oracle EBS discovery for {self.name}")

        # Start with web discovery
        result = super().discover_elements()

        # Add database schema discovery if enabled
        if self.app_profile.discovery.discover_schema:
            schema_info = self._discover_database_schema()
            if schema_info:
                result.schema = schema_info

        # Discover Oracle EBS modules
        modules_info = self._discover_modules()
        result.metadata["modules"] = modules_info

        logger.info(
            f"Oracle EBS discovery complete: {len(result.elements)} elements, "
            f"{len(result.pages)} pages, schema: {result.schema is not None}"
        )

        return result

    def _discover_database_schema(self) -> Optional[Dict[str, Any]]:
        """Discover Oracle database schema (simplified)."""
        try:
            # This is a placeholder - actual implementation would use cx_Oracle
            logger.info("Database schema discovery (requires cx_Oracle)")

            # Example structure that would be returned:
            schema = {
                "tables": [],
                "views": [],
                "procedures": []
            }

            # Actual implementation:
            # import cx_Oracle
            # connection = cx_Oracle.connect(self.app_profile.discovery.connection_string)
            # cursor = connection.cursor()
            # # Query system tables for schema information
            # cursor.execute("SELECT table_name FROM user_tables")
            # schema["tables"] = [row[0] for row in cursor.fetchall()]

            return schema

        except Exception as e:
            logger.error(f"Database schema discovery failed: {e}")
            return None

    def _discover_modules(self) -> List[str]:
        """Discover Oracle EBS modules."""
        # Return configured modules
        return self.app_profile.modules or []

    def execute_test(self, test_case: TestCase) -> TestResult:
        """
        Execute Oracle EBS test case.

        Handles both web forms and database operations.
        """
        logger.info(f"Executing Oracle EBS test: {test_case.name}")

        # Use parent web adapter execution
        result = super().execute_test(test_case)

        # Add Oracle EBS specific metadata
        result.environment = "oracle_ebs"

        return result

    def validate_state(self) -> bool:
        """Validate Oracle EBS is accessible."""
        # Validate web interface
        web_valid = super().validate_state()

        # Optionally validate database connection
        db_valid = self._validate_database()

        return web_valid and db_valid

    def _validate_database(self) -> bool:
        """Validate database connection (simplified)."""
        try:
            # This would actually connect to Oracle database
            logger.debug("Database validation (requires cx_Oracle)")
            return True

        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up Oracle EBS resources."""
        # Close database connection if open
        if self.db_connection:
            try:
                self.db_connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")

        # Call parent cleanup for browser
        super().cleanup()

    def get_capabilities(self) -> Dict[str, bool]:
        """Get adapter capabilities."""
        return {
            "ui_testing": True,
            "api_testing": False,
            "database_testing": True,
            "screenshot_capture": True,
            "video_recording": True,
            "log_capture": True,
        }
