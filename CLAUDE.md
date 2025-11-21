# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Agentic AI Regression Testing Framework** that uses LangChain/LangGraph to autonomously discover, plan, generate, execute, and report on test cases. The framework is application-agnostic and supports web apps (Playwright/Selenium), APIs (REST/OpenAPI), and enterprise applications (Oracle EBS).

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test types
pytest tests/unit/ -m unit                    # Unit tests only
pytest tests/integration/ -m integration      # Integration tests only

# Run specific test file
pytest tests/unit/test_tool_framework.py
```

### Running the Framework

```bash
# Check configuration
python main.py check

# List available application profiles
python main.py list-apps

# Run discovery only
python main.py discover --app web_portal

# Run full workflow
python main.py run --app web_portal --feature "user login functionality" --hitl-mode APPROVE_PLAN

# Run test planning only
python main.py plan --app web_portal --feature "checkout flow"
```

### Demo Scripts

```bash
# Quick demo (minimal output)
python demo_quick.py

# Complete orchestrator workflow (detailed output)
python demo_orchestrator_v2.py

# Individual agents demo (shows standalone usage)
python demo_individual_agents.py
```

### Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web testing)
playwright install
```

## Architecture

### Dual Architecture (V1 and V2)

The codebase is **in transition** between two architectures:

- **V1 (Legacy)**: In `agents/` directory - LangChain-based agents with embedded tools
- **V2 (Current)**: In `agents_v2/` and `tools/` directories - LangGraph state machines with separated, reusable tools

**Important**: When adding new features, use the V2 architecture. The V1 agents are being phased out.

### V2 Architecture Principles

1. **Tool Separation**: All functionality is implemented as reusable tools in `tools/` directory
   - Tools inherit from `BaseTool` (in `tools/base.py`)
   - Tools are registered in `ToolRegistry` for discovery
   - Agents use tools, never implement logic directly

2. **LangGraph Agents**: All agents in `agents_v2/` use LangGraph state machines
   - State schemas defined in `agents_v2/state.py` using TypedDict
   - Nodes are pure functions that take state and return updated state
   - Conditional routing between nodes
   - Built-in checkpointing support

3. **Type Safety**: Extensive use of TypedDict for state management and Pydantic for models

### Agent Workflow

```
Orchestrator (coordinates everything)
  ↓
Discovery Agent → Test Planner Agent → Test Generator Agent → Test Executor Agent → Reporting Agent
```

Each agent:
- Has a state schema in `agents_v2/state.py`
- Uses tools from `tools/` directory
- Returns standardized results
- Can be used independently or orchestrated

### Key Directories

- **`agents_v2/`**: LangGraph-based agents (NEW - use this)
- **`agents/`**: LangChain-based agents (LEGACY - being phased out)
- **`tools/`**: Reusable tools organized by category
  - `tools/validation/`: Input sanitization, path validation
  - `tools/discovery/`: Web and API discovery
  - `tools/planning/`: Test plan generation, test case extraction
  - `tools/generation/`: Script generation, code templates
  - `tools/execution/`: Test execution, result collection
  - `tools/reporting/`: Report generation and writing
  - `tools/rag/`: Vector search and pattern retrieval
- **`adapters/`**: Application-specific adapters (Web, API, Oracle EBS, custom)
- **`models/`**: Pydantic data models (TestCase, TestResult, ApplicationProfile, etc.)
- **`config/`**: Configuration (settings.py, llm_config.py, app_profiles.yaml)
- **`hitl/`**: Human-in-the-loop approval workflows
- **`rag/`**: RAG system for test knowledge base (FAISS/Chroma)
- **`utils/`**: Utilities (logger, helpers)

## Creating New Tools

Tools are the primary extension point. Always create a tool for new functionality:

```python
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata

class MyCustomTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_custom_tool",
            description="What this tool does",
            version="1.0.0",
            tags=["category"],
            is_safe=True,
        )

    def execute(self, param: str) -> ToolResult:
        # Use _wrap_execution for automatic error handling and timing
        return self._wrap_execution(self._process, param=param)

    def _process(self, param: str) -> ToolResult:
        # Your logic here
        result_data = {"output": param.upper()}

        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=result_data,
            metadata={"operation": "process"}
        )

# Register the tool
from tools.registry import register_tool
register_tool(MyCustomTool)
```

**Key Points**:
- Keep tools stateless - all data via parameters
- Use `_wrap_execution` for consistent error handling
- Return `ToolResult` with standardized format
- Add comprehensive metadata
- Write tests in `tests/unit/` using mocks

## Security Considerations

The framework has specific security tools that MUST be used:

1. **Input Sanitization**: Use `InputSanitizerTool` before processing user input
   - Prevents prompt injection
   - Removes SQL/command injection patterns
   - Located in `tools/validation/input_sanitizer.py`

2. **Path Validation**: Use `PathValidatorTool` before file operations
   - Prevents path traversal attacks
   - Validates against forbidden paths
   - Located in `tools/validation/path_validator.py`

3. **FAISS Security**: Current implementation uses pickle (insecure) - be cautious with vector store files

## Application Profiles

Applications are configured in `config/app_profiles.yaml`. Each profile defines:
- Application type (WEB, API, ENTERPRISE, DATABASE)
- Adapter to use (web_adapter, api_adapter, oracle_ebs_adapter, custom)
- Authentication configuration
- Test framework (PLAYWRIGHT, SELENIUM, PYTEST, ROBOT)
- Discovery settings (max_depth, max_pages, exclude patterns)

Create new profiles by adding entries to the YAML file or programmatically with `ApplicationProfile` Pydantic model.

## Custom Adapters

To support a new application type, create an adapter:

1. Inherit from `BaseApplicationAdapter` in `adapters/base_adapter.py`
2. Implement required methods:
   - `discover_elements()` - Discover UI/API elements
   - `execute_test(test_case)` - Execute a test case
   - `validate_state()` - Check application is ready
   - `cleanup()` - Clean up resources
3. Register with `register_adapter("name", YourAdapter)`
4. Reference in application profile

## Human-in-the-Loop (HITL)

HITL modes control approval workflows:
- **FULL_AUTO**: No human intervention (CI/CD)
- **APPROVE_PLAN**: Approve test plans only
- **APPROVE_TESTS**: Approve generated tests only
- **APPROVE_ALL**: Approve everything
- **INTERACTIVE**: Step-by-step guidance

Configure via `.env` file (`HITL_MODE`) or command-line (`--hitl-mode`).

## Environment Configuration

Copy `.env.example` to `.env` and configure:

**Required**:
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - LLM provider API key
- `LLM_PROVIDER` - "openai" or "anthropic"
- `LLM_MODEL` - Model name (e.g., "gpt-4-turbo-preview")

**Optional but Recommended**:
- `VECTOR_STORE` - "faiss" or "chroma"
- `HITL_MODE` - Human approval mode
- `TEST_FRAMEWORK` - Default test framework
- `PARALLEL_EXECUTION` - Enable parallel test execution
- `MAX_WORKERS` - Number of parallel workers

## Common Patterns

### Running Complete Workflow Programmatically

```python
from models.app_profile import ApplicationProfile, ApplicationType, TestFramework
from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2

app_profile = ApplicationProfile(
    name="my_app",
    app_type=ApplicationType.WEB,
    adapter="web",
    base_url="https://myapp.com",
    test_framework=TestFramework.PLAYWRIGHT,
)

orchestrator = OrchestratorAgentV2(
    app_profile=app_profile,
    output_dir="generated_tests",
    reports_dir="reports",
    enable_hitl=False,
)

final_state = orchestrator.run_full_workflow(
    feature_description="User login and authentication"
)
```

### Using Individual Agents

```python
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2

discovery_agent = DiscoveryAgentV2(app_profile=app_profile)
discovery_state = discovery_agent.discover(
    app_profile=app_profile,
    max_depth=3,
    max_pages=50
)

elements = discovery_state["elements"]
pages = discovery_state["pages"]
```

### Using Tools Directly

```python
from tools.registry import get_tool

# Get a tool instance
sanitizer = get_tool("input_sanitizer", config={"strict_mode": True})

# Execute tool
result = sanitizer.execute(text=user_input, check_prompt_injection=True)

if result.is_success():
    clean_text = result.data
else:
    print(f"Validation failed: {result.error}")
```

## RAG Knowledge Base

The framework uses RAG to store and retrieve test patterns:
- Historical test cases stored in vector database
- Test execution results fed back into knowledge base
- Similar test patterns retrieved during generation
- Located in `rag/` directory

Add to knowledge base:
```python
from rag.retriever import TestKnowledgeRetriever

retriever = TestKnowledgeRetriever()
retriever.add_test_cases(test_cases)
retriever.add_test_result(test_result)

# Search for similar tests
similar = retriever.find_similar_tests(query="login test", k=5)
```

## Testing Guidelines

- **Unit tests** in `tests/unit/`: Test individual tools and components with mocks
- **Integration tests** in `tests/integration/`: Test agents end-to-end with real adapters
- Use `conftest.py` fixtures for common test setup
- Mock external dependencies (LLMs, web browsers) in unit tests
- Tag tests with `@pytest.mark.unit` or `@pytest.mark.integration`

## Migration Notes

If modifying V1 agents:
1. Check if V2 equivalent exists in `agents_v2/`
2. If yes, modify V2 instead
3. If no, consider creating V2 version before adding features
4. See `docs/MIGRATION_GUIDE.md` for detailed migration instructions

The V1 agents (`agents/orchestrator.py`, `agents/discovery.py`, etc.) are maintained for backward compatibility but should not receive new features.

## Important Files

- **README.md**: User-facing documentation
- **docs/ARCHITECTURE_V2.md**: Detailed V2 architecture documentation
- **COMPLETE_REFACTORING_SUMMARY.md**: Refactoring history and decisions
- **DEMO_GUIDE.md**: Demo script documentation
- **main.py**: CLI entry point
- **pyproject.toml**: Project metadata and dependencies
- **requirements.txt**: Python dependencies
