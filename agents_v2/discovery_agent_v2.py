"""
Discovery Agent V2 - LangGraph Implementation

This agent discovers application elements using reusable tools
and LangGraph for workflow orchestration.

Key improvements over V1:
- Uses reusable tools instead of embedded logic
- LangGraph for state management and workflow
- Better error handling and validation
- HITL integration with graph interrupts
- Fully testable with mocked tools
"""

from datetime import datetime
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents_v2.state import DiscoveryState
from tools import get_tool
from tools.base import ToolStatus
from models.app_profile import ApplicationProfile, ApplicationType
from utils.logger import get_logger

logger = get_logger(__name__)


class DiscoveryAgentV2:
    """
    Discovery Agent using LangGraph and reusable tools

    Workflow:
    1. Initialize state
    2. Validate and sanitize inputs
    3. Determine discovery type (Web, API, Database)
    4. Execute discovery using appropriate tool
    5. Process and validate results
    6. Return structured discovery result
    """

    def __init__(
        self,
        app_profile: ApplicationProfile,
        enable_hitl: bool = False,
    ):
        """
        Initialize Discovery Agent

        Args:
            app_profile: Application profile configuration
            enable_hitl: Enable human-in-the-loop for approvals
        """
        self.app_profile = app_profile
        self.enable_hitl = enable_hitl
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow

        Graph structure:
            START
              ↓
           initialize
              ↓
           validate_input
              ↓
           determine_discovery_type
              ↓
          /    |    \\
        web   api   database
          \\    |    /
              ↓
         process_results
              ↓
            END
        """
        workflow = StateGraph(DiscoveryState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("determine_type", self._determine_type_node)
        workflow.add_node("discover_web", self._discover_web_node)
        workflow.add_node("discover_api", self._discover_api_node)
        workflow.add_node("process_results", self._process_results_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Set entry point
        workflow.set_entry_point("initialize")

        # Add edges
        workflow.add_edge("initialize", "validate_input")
        workflow.add_edge("validate_input", "determine_type")

        # Conditional routing based on app type
        workflow.add_conditional_edges(
            "determine_type",
            self._route_by_type,
            {
                "web": "discover_web",
                "api": "discover_api",
                "error": "handle_error",
            }
        )

        workflow.add_edge("discover_web", "process_results")
        workflow.add_edge("discover_api", "process_results")
        workflow.add_edge("process_results", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=MemorySaver())

    # ========== Graph Nodes ==========

    def _initialize_node(self, state: DiscoveryState) -> DiscoveryState:
        """Initialize workflow state"""
        logger.info(f"Initializing discovery for {self.app_profile.name}")

        state["start_time"] = datetime.now()
        state["status"] = "in_progress"
        state["app_profile"] = self.app_profile
        state["elements"] = []
        state["pages"] = []
        state["apis"] = []
        state["validation_warnings"] = []
        state["total_elements"] = 0
        state["total_pages"] = 0
        state["element_types"] = {}
        state["requires_approval"] = self.enable_hitl

        return state

    def _validate_input_node(self, state: DiscoveryState) -> DiscoveryState:
        """Validate and sanitize inputs using InputSanitizerTool"""
        logger.info("Validating inputs")

        try:
            # Get input sanitizer tool
            sanitizer = get_tool("input_sanitizer", config={
                "strict_mode": False,
                "max_length": 10000,
            })

            # Sanitize feature description if provided
            discovery_params = state.get("discovery_params", {})
            feature_description = discovery_params.get("feature_description", "")

            if feature_description:
                result = sanitizer.execute(
                    text=feature_description,
                    check_prompt_injection=True,
                    check_sql_injection=True,
                    check_command_injection=True,
                )

                if result.is_success():
                    state["sanitized_input"] = result.data
                    if result.metadata.get("warnings"):
                        state["validation_warnings"].extend(result.metadata["warnings"])
                        logger.warning(f"Input validation warnings: {result.metadata['warnings']}")
                else:
                    state["error"] = f"Input validation failed: {result.error}"
                    state["status"] = "failed"
                    return state

        except Exception as e:
            logger.error(f"Validation error: {e}")
            state["validation_warnings"].append(f"Validation tool error: {str(e)}")

        return state

    def _determine_type_node(self, state: DiscoveryState) -> DiscoveryState:
        """Determine the type of discovery needed"""
        app_profile: ApplicationProfile = state["app_profile"]

        logger.info(f"Discovery type: {app_profile.app_type}")
        state["discovery_type"] = app_profile.app_type.value

        return state

    def _discover_web_node(self, state: DiscoveryState) -> DiscoveryState:
        """Discover web application elements using WebDiscoveryTool"""
        logger.info("Starting web discovery")

        try:
            # Get web discovery tool
            web_tool = get_tool("web_discovery", config={
                "app_profile": state["app_profile"]
            })

            # Get discovery parameters
            discovery_params = state.get("discovery_params", {})

            # Execute discovery
            result = web_tool.execute(
                url=discovery_params.get("url"),
                max_depth=discovery_params.get("max_depth"),
                max_pages=discovery_params.get("max_pages"),
            )

            if result.is_success():
                state["discovery_result"] = result.data
                state["elements"] = result.data.get("elements", [])
                state["pages"] = result.data.get("pages", [])
                state["total_elements"] = result.metadata.get("total_elements", 0)
                state["total_pages"] = result.metadata.get("total_pages", 0)
                state["element_types"] = result.metadata.get("element_types", {})

                logger.info(
                    f"Discovery completed: {state['total_elements']} elements, "
                    f"{state['total_pages']} pages"
                )
            else:
                state["error"] = result.error
                state["status"] = "failed"
                logger.error(f"Web discovery failed: {result.error}")

        except Exception as e:
            state["error"] = f"Web discovery error: {str(e)}"
            state["status"] = "failed"
            logger.error(f"Web discovery exception: {e}")

        return state

    def _discover_api_node(self, state: DiscoveryState) -> DiscoveryState:
        """Discover API endpoints using APIDiscoveryTool"""
        logger.info("Starting API discovery")

        try:
            # Get API discovery tool
            api_tool = get_tool("api_discovery", config={
                "app_profile": state["app_profile"]
            })

            # Get discovery parameters
            discovery_params = state.get("discovery_params", {})

            # Execute discovery
            result = api_tool.execute(
                spec_url=discovery_params.get("spec_url"),
                include_deprecated=discovery_params.get("include_deprecated", False),
                methods=discovery_params.get("methods"),
            )

            if result.is_success():
                state["discovery_result"] = result.data
                state["apis"] = result.data.get("apis", [])
                state["total_elements"] = result.metadata.get("total_endpoints", 0)

                logger.info(
                    f"API discovery completed: {state['total_elements']} endpoints"
                )
            else:
                state["error"] = result.error
                state["status"] = "failed"
                logger.error(f"API discovery failed: {result.error}")

        except Exception as e:
            state["error"] = f"API discovery error: {str(e)}"
            state["status"] = "failed"
            logger.error(f"API discovery exception: {e}")

        return state

    def _process_results_node(self, state: DiscoveryState) -> DiscoveryState:
        """Process and finalize discovery results"""
        logger.info("Processing discovery results")

        state["end_time"] = datetime.now()
        state["status"] = "completed"

        # Calculate execution time
        if state.get("start_time") and state.get("end_time"):
            execution_time = (state["end_time"] - state["start_time"]).total_seconds()
            logger.info(f"Discovery completed in {execution_time:.2f} seconds")

        return state

    def _handle_error_node(self, state: DiscoveryState) -> DiscoveryState:
        """Handle errors and cleanup"""
        logger.error(f"Discovery failed: {state.get('error', 'Unknown error')}")

        state["end_time"] = datetime.now()
        state["status"] = "failed"

        return state

    # ========== Routing Functions ==========

    def _route_by_type(self, state: DiscoveryState) -> str:
        """Route to appropriate discovery node based on app type"""
        if state.get("error"):
            return "error"

        app_type = state.get("discovery_type", "").lower()

        if app_type == "web":
            return "web"
        elif app_type == "api":
            return "api"
        else:
            state["error"] = f"Unsupported application type: {app_type}"
            return "error"

    # ========== Public Methods ==========

    def discover(
        self,
        url: Optional[str] = None,
        max_depth: Optional[int] = None,
        max_pages: Optional[int] = None,
        **kwargs
    ) -> DiscoveryState:
        """
        Execute discovery workflow

        Args:
            url: Starting URL for web discovery
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl
            **kwargs: Additional discovery parameters

        Returns:
            Final state with discovery results
        """
        # Prepare initial state
        initial_state: DiscoveryState = {
            "app_profile": self.app_profile,
            "discovery_params": {
                "url": url,
                "max_depth": max_depth,
                "max_pages": max_pages,
                **kwargs
            }
        }

        # Execute graph
        try:
            final_state = self.graph.invoke(
                initial_state,
                config={"configurable": {"thread_id": "discovery_session"}}
            )
            return final_state
        except Exception as e:
            logger.error(f"Discovery workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now(),
            }

    def get_discovery_result(self, state: DiscoveryState) -> Dict[str, Any]:
        """
        Extract formatted discovery result from state

        Args:
            state: Final workflow state

        Returns:
            Formatted discovery result
        """
        return {
            "status": state.get("status"),
            "elements": state.get("elements", []),
            "pages": state.get("pages", []),
            "apis": state.get("apis", []),
            "statistics": {
                "total_elements": state.get("total_elements", 0),
                "total_pages": state.get("total_pages", 0),
                "element_types": state.get("element_types", {}),
            },
            "metadata": {
                "app_name": self.app_profile.name,
                "app_type": self.app_profile.app_type.value,
                "validation_warnings": state.get("validation_warnings", []),
                "execution_time": (
                    (state["end_time"] - state["start_time"]).total_seconds()
                    if state.get("end_time") and state.get("start_time")
                    else None
                ),
            },
            "error": state.get("error"),
        }
