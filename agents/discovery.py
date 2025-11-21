"""Discovery Agent - explores applications to find testable elements."""

from typing import Optional

from adapters.base_adapter import BaseApplicationAdapter, DiscoveryResult
from models.app_profile import ApplicationProfile
from rag.retriever import TestKnowledgeRetriever
from utils.logger import get_logger

logger = get_logger(__name__)


class DiscoveryAgent:
    """
    Discovery Agent explores the application to identify:
    - UI elements (buttons, forms, inputs)
    - API endpoints
    - Database schemas
    - Application features and modules
    """

    def __init__(
        self,
        adapter: BaseApplicationAdapter,
        app_profile: ApplicationProfile
    ):
        """
        Initialize Discovery Agent.

        Args:
            adapter: Application adapter
            app_profile: Application profile
        """
        self.adapter = adapter
        self.app_profile = app_profile
        self.knowledge_retriever = TestKnowledgeRetriever()

        self.last_discovery: Optional[DiscoveryResult] = None

        logger.info(f"DiscoveryAgent initialized for {app_profile.name}")

    def discover(self) -> DiscoveryResult:
        """
        Discover application elements.

        Returns:
            DiscoveryResult: Discovery results
        """
        logger.info(f"Starting discovery for {self.app_profile.name}")

        # Validate application is accessible
        if not self.adapter.validate_state():
            raise RuntimeError("Application is not accessible")

        # Authenticate if needed
        if not self.adapter.authenticate():
            raise RuntimeError("Authentication failed")

        # Perform discovery
        discovery_result = self.adapter.discover_elements()

        # Store discovery result
        self.last_discovery = discovery_result

        # Log summary
        logger.info(
            f"Discovery complete: {len(discovery_result.elements)} elements, "
            f"{len(discovery_result.pages)} pages, "
            f"{len(discovery_result.apis)} APIs"
        )

        return discovery_result

    def get_last_discovery(self) -> Optional[DiscoveryResult]:
        """
        Get the last discovery result.

        Returns:
            Last DiscoveryResult or None
        """
        return self.last_discovery

    def get_elements_by_type(self, element_type: str) -> list:
        """
        Get discovered elements filtered by type.

        Args:
            element_type: Element type to filter

        Returns:
            List of elements
        """
        if not self.last_discovery:
            return []

        return [
            elem for elem in self.last_discovery.elements
            if elem.type == element_type
        ]

    def get_summary(self) -> str:
        """
        Get a human-readable summary of discovery.

        Returns:
            Summary string
        """
        if not self.last_discovery:
            return "No discovery results available"

        result = self.last_discovery

        summary = f"""
Discovery Summary for {self.app_profile.name}:
- Elements discovered: {len(result.elements)}
- Pages crawled: {len(result.pages)}
- APIs found: {len(result.apis)}
"""

        # Break down elements by type
        element_types = {}
        for elem in result.elements:
            element_types[elem.type] = element_types.get(elem.type, 0) + 1

        if element_types:
            summary += "\nElements by type:\n"
            for elem_type, count in sorted(element_types.items()):
                summary += f"  - {elem_type}: {count}\n"

        return summary.strip()
