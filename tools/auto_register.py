"""
Auto-registration module for all tools

This module imports and registers all available tools in the ToolRegistry.
Import this module at application startup to ensure all tools are available.
"""

from tools.base import ToolRegistry
from utils.logger import get_logger

logger = get_logger(__name__)


def register_all_tools():
    """Register all available tools"""

    # Validation Tools
    try:
        from tools.validation import (
            InputSanitizerTool,
            PathValidatorTool,
            ScriptValidatorTool,
        )

        ToolRegistry.register(InputSanitizerTool)
        ToolRegistry.register(PathValidatorTool)
        ToolRegistry.register(ScriptValidatorTool)
        logger.debug("Registered validation tools")
    except ImportError as e:
        logger.warning(f"Could not register validation tools: {e}")

    # Discovery Tools
    try:
        from tools.discovery import (
            WebDiscoveryTool,
            APIDiscoveryTool,
        )

        ToolRegistry.register(WebDiscoveryTool)
        ToolRegistry.register(APIDiscoveryTool)
        logger.debug("Registered discovery tools")
    except ImportError as e:
        logger.warning(f"Could not register discovery tools: {e}")

    # RAG Tools
    try:
        from tools.rag import (
            VectorSearchTool,
            TestPatternRetrieverTool,
        )

        ToolRegistry.register(VectorSearchTool)
        ToolRegistry.register(TestPatternRetrieverTool)
        logger.debug("Registered RAG tools")
    except ImportError as e:
        logger.warning(f"Could not register RAG tools: {e}")

    # Planning Tools
    try:
        from tools.planning import (
            TestPlanGeneratorTool,
            TestCaseExtractorTool,
        )

        ToolRegistry.register(TestPlanGeneratorTool)
        ToolRegistry.register(TestCaseExtractorTool)
        logger.debug("Registered planning tools")
    except ImportError as e:
        logger.warning(f"Could not register planning tools: {e}")

    # Generation Tools
    try:
        from tools.generation import (
            ScriptGeneratorTool,
            CodeTemplateManagerTool,
        )

        ToolRegistry.register(ScriptGeneratorTool)
        ToolRegistry.register(CodeTemplateManagerTool)
        logger.debug("Registered generation tools")
    except ImportError as e:
        logger.warning(f"Could not register generation tools: {e}")

    # File Operation Tools
    try:
        from tools.file_operations import (
            TestScriptWriterTool,
        )

        ToolRegistry.register(TestScriptWriterTool)
        logger.debug("Registered file operation tools")
    except ImportError as e:
        logger.warning(f"Could not register file operation tools: {e}")

    # Execution Tools
    try:
        from tools.execution import (
            TestExecutorTool,
            ResultCollectorTool,
        )

        ToolRegistry.register(TestExecutorTool)
        ToolRegistry.register(ResultCollectorTool)
        logger.debug("Registered execution tools")
    except ImportError as e:
        logger.warning(f"Could not register execution tools: {e}")

    # Reporting Tools
    try:
        from tools.reporting import (
            ReportGeneratorTool,
            ReportWriterTool,
        )

        ToolRegistry.register(ReportGeneratorTool)
        ToolRegistry.register(ReportWriterTool)
        logger.debug("Registered reporting tools")
    except ImportError as e:
        logger.warning(f"Could not register reporting tools: {e}")

    # Log summary
    tools = ToolRegistry.list_tools()
    logger.info(f"Registered {len(tools)} tools")


# Auto-register when module is imported
register_all_tools()
