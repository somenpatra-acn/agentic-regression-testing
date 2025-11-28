# Copilot Instructions for Agentic AI Regression Testing Framework

## Project Overview

This is an **Agentic AI Regression Testing Framework** that autonomously discovers, plans, generates, executes, and reports on test cases using LangChain/LangGraph. It's application-agnostic with support for web apps (Playwright/Selenium), APIs (REST/OpenAPI), and enterprise systems (Oracle EBS).

**Key insight**: The codebase is in transition from V1 (legacy LangChain agents) to V2 (LangGraph + separate tools). Always use V2 for new work.

---

## Critical Architecture: V1 vs V2

### Use V2 for ALL new features

- **V1** (Legacy): `agents/` directory - LangChain agents with embedded tools, being phased out
- **V2** (Current): `agents_v2/` + `tools/` - LangGraph state machines with reusable tools

**Why V2 matters**: V1 agents are tightly coupled and hard to test. V2 separates concerns—tools are pure, reusable functions; agents orchestrate via LangGraph state machines.

---

## Architecture Patterns (Study These)

### 1. Tool System (Primary Extension Point)

All functionality lives in reusable tools (`tools/` directory). This is the core pattern.

**Structure**: Every tool inherits from `BaseTool` in `tools/base.py`:

```python
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata

class MyTool(BaseTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_tool",
            description="What it does",
            tags=["category"],
            is_safe=True
        )

    def execute(self, param: str) -> ToolResult:
        return self._wrap_execution(self._process, param=param)

    def _process(self, param: str) -> ToolResult:
        # Your logic
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={"output": param},
            metadata={}
        )
```

**Key principles**:
- Tools are **stateless** (all data via parameters)
- Use `_wrap_execution()` for automatic error handling + timing
- Return standardized `ToolResult` with status/data/error
- Register in `tools/auto_register.py` or `ToolRegistry`

**Tool categories** (examine existing for patterns):
- `tools/validation/` - Input sanitization, path validation (MUST use before processing user input)
- `tools/discovery/` - Element discovery (WebDiscoveryTool, APIDiscoveryTool)
- `tools/planning/` - Test plan generation (TestPlanGeneratorTool, TestCaseExtractorTool)
- `tools/generation/` - Code generation (ScriptGeneratorTool, CodeTemplateManagerTool)
- `tools/execution/` - Test running (TestExecutorTool, ResultCollectorTool)
- `tools/reporting/` - Report generation (ReportGeneratorTool, ReportWriterTool)
- `tools/rag/` - Vector search (VectorSearchTool, TestPatternRetrieverTool)

### 2. LangGraph Agents (V2)

Agents use LangGraph state machines. Each agent:
1. Defines a **TypedDict state** in `agents_v2/state.py` (see DiscoveryState, TestPlanningState, etc.)
2. Implements **node functions** that take state → updated state
3. Uses **tools** to perform work, never implements logic directly
4. Is **independently testable** by mocking tools

**Example orchestration** (`agents_v2/orchestrator_agent_v2.py`):
- Builds a StateGraph with conditional edges
- Calls discovery → planning → generation → execution → reporting
- Passes state through pipeline

**State management patterns**:
- Use `TypedDict` with `total=False` for optional fields
- Include input params, intermediate results, metadata, errors, HITL status
- State is immutable between node calls—return updated copy

### 3. Application Adapters

Adapters implement `BaseApplicationAdapter` in `adapters/base_adapter.py`. Required methods:
- `discover_elements()` → DiscoveryResult with elements/pages/apis
- `execute_test(test_case)` → TestResult
- `validate_state()` → bool (app ready?)
- `cleanup()`

**Built-in adapters**:
- `WebAdapter` - Playwright-based web testing
- `APIAdapter` - REST/OpenAPI testing
- `OracleEBSAdapter` - Enterprise Oracle EBS
- `CustomAdapter` - Template for new app types

Register in `config/app_profiles.yaml` and reference via ApplicationProfile.

### 4. HITL Integration

Human-in-the-loop is deeply integrated. ApprovalManager in `hitl/approval_manager.py` checks HITL mode:
- `FULL_AUTO` - No approvals (CI/CD)
- `APPROVE_PLAN` - Approve test plans only
- `APPROVE_TESTS` - Approve generated tests
- `APPROVE_ALL` - Approve everything
- `INTERACTIVE` - Step-by-step

Agents check `is_approval_required()` at decision points. Web UI (`streamlit_ui/app.py`) provides frontend.

---

## Critical Security Practices

**Always use validation tools before processing user input**:

1. **InputSanitizerTool** (`tools/validation/input_sanitizer.py`) - Prevents prompt injection
2. **PathValidatorTool** (`tools/validation/path_validator.py`) - Prevents path traversal

Example:
```python
sanitizer = ToolRegistry.get("input_sanitizer")
result = sanitizer.execute(text=user_input, check_prompt_injection=True)
if result.is_failure():
    raise ValueError(result.error)
```

---

## Development Workflows

### Quick Testing During Development

```bash
# Unit tests (fast, isolated)
pytest tests/unit/ -xvs

# Integration tests (slower, real components)
pytest tests/integration/ -xvs

# Coverage report
pytest --cov=. --cov-report=html

# Run specific test class/function
pytest tests/unit/test_tool_xyz.py::TestClass::test_method -xvs
```

### Running Framework

```bash
# CLI entry point (main.py)
python main.py run --app web_portal --feature "login" --hitl-mode APPROVE_PLAN

# Available commands:
python main.py check              # Validate config
python main.py list-apps          # List profiles
python main.py discover --app NAME
python main.py plan --app NAME --feature "DESC"

# Demo scripts (good for understanding flow)
python demo_quick.py              # Minimal output
python demo_orchestrator_v2.py    # Detailed orchestrator
python demo_individual_agents.py  # Standalone agent usage
```

### Complete Orchestrator Workflow (Full Pipeline)

The orchestrator coordinates all agents in sequence (see `agents_v2/orchestrator_agent_v2.py`):

```python
from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2
from models.app_profile import ApplicationProfile, ApplicationType, TestFramework

# 1. Create app profile
app_profile = ApplicationProfile(
    name="my_app",
    base_url="https://myapp.com",
    app_type=ApplicationType.WEB,
    test_framework=TestFramework.PLAYWRIGHT,
    adapter="web_adapter",
)

# 2. Initialize orchestrator (coordinates all 5 agents)
orchestrator = OrchestratorAgentV2(
    app_profile=app_profile,
    output_dir="generated_tests",
    reports_dir="reports",
    enable_hitl=False,  # Set True for approval workflows
)

# 3. Run complete pipeline: Discovery → Planning → Generation → Execution → Reporting
final_state = orchestrator.run_full_workflow(
    feature_description="User login and authentication"
)

# 4. Inspect results
summary = orchestrator.get_workflow_summary(final_state)
print(f"Status: {summary['status']}")  # 'completed', 'failed', 'pending_approval'
print(f"Completed stages: {summary['completed_stages']}")
print(f"Execution time: {summary['total_execution_time']}s")
```

**Workflow stages in order:**
1. `discovery_state` - Finds UI elements, pages, APIs
2. `planning_state` - Creates test plan + test cases
3. `generation_state` - Generates executable test scripts
4. `execution_state` - Runs tests, collects results
5. `reporting_state` - Generates HTML/JSON/Markdown reports

### Individual Agent Usage (Isolated Workflows)

When you only need specific stages, use agents independently (see `demo_individual_agents.py`):

```python
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from agents_v2.test_planner_agent_v2 import TestPlannerAgentV2

# Stage 1: Discovery only
discovery_agent = DiscoveryAgentV2(app_profile=app_profile)
discovery_state = discovery_agent.discover(app_profile=app_profile)
elements = discovery_state['elements']
pages = discovery_state['pages']

# Stage 2: Planning only
planner = TestPlannerAgentV2(app_profile=app_profile)
planning_state = planner.create_plan(
    app_profile=app_profile,
    feature_description="login feature",
    discovery_result=discovery_state['discovery_result'],
)
test_cases = planning_state['test_cases']  # List of TestCase objects

# Stage 3: Generation only
generator = TestGeneratorAgentV2(
    app_profile=app_profile,
    output_dir="tests",
)
generation_state = generator.generate_tests(test_cases=test_cases)
scripts = generation_state['generated_scripts']  # Script metadata + file paths

# Stage 4: Execution only
executor = TestExecutorAgentV2(framework="pytest")
execution_state = executor.execute_tests(test_scripts=scripts)
results = execution_state['test_results']  # Pass/fail/error for each test

# Stage 5: Reporting only
reporter = ReportingAgentV2(output_dir="reports")
reporting_state = reporter.generate_reports(
    test_results=results,
    app_name=app_profile.name,
    report_formats=["html", "json"]
)
reports = reporting_state['generated_reports']  # {format, content, file_path}
```

### LangGraph State Patterns

Each agent uses a state machine with immutable state updates (from `agents_v2/state.py`):

```python
# State flows through nodes in a StateGraph
# Each node receives state dict and returns updated state (new dict, not mutated)

def my_node(state: DiscoveryState) -> DiscoveryState:
    """Node function - pure transformation of state"""
    # WRONG: state['elements'].append(...)  # Mutating!
    
    # RIGHT: Return new state
    updated_state = dict(state)  # Shallow copy
    updated_state['elements'] = state['elements'] + [new_element]
    updated_state['status'] = 'processing'
    return updated_state
```

**Common state patterns:**
- `status` field: tracks "pending" → "in_progress" → "completed"/"failed"
- `error` field: stores exception/error message if node fails
- `requires_approval` + `approval_status`: HITL workflow tracking
- `start_time`/`end_time`: Execution timing
- Immutability: Always return new dict, never mutate input state

### Tool Registry Usage Patterns

Tools are registered and retrieved via `ToolRegistry` (see `tools/registry.py`):

```python
from tools.base import ToolRegistry, ToolResult

# Pattern 1: Get tool with config
sanitizer = ToolRegistry.get("input_sanitizer", config={"strict_mode": True})
result = sanitizer.execute(text=user_input, check_prompt_injection=True)

if result.is_failure():
    print(f"Error: {result.error}")
    raise ValueError(result.error)

# Pattern 2: Chain tool results
validator = ToolRegistry.get("path_validator")
result = validator.execute(path=file_path)
if result.is_success():
    validated_path = result.data

# Pattern 3: Check execution time
print(f"Tool took {result.execution_time}ms")

# Pattern 4: Access tool metadata
tool = ToolRegistry.get("web_discovery")
print(f"Tool: {tool.metadata.name} - {tool.metadata.description}")
print(f"Safe: {tool.metadata.is_safe}, Tags: {tool.metadata.tags}")
```

### HITL (Human-in-the-Loop) Integration Patterns

HITL is integrated at decision points using `ApprovalManager` (see `hitl/approval_manager.py`):

```python
from hitl.approval_manager import ApprovalManager, ApprovalType
from models.approval import ApprovalStatus

# Initialize with mode from settings
approval_mgr = ApprovalManager(
    hitl_mode="APPROVE_PLAN",  # Or FULL_AUTO, APPROVE_TESTS, APPROVE_ALL, INTERACTIVE
    timeout=3600  # seconds
)

# Check if approval needed
if approval_mgr.is_approval_required(ApprovalType.TEST_PLAN):
    # Request human approval
    approval = await approval_mgr.request_approval(
        approval_type=ApprovalType.TEST_PLAN,
        item_id="PLAN-ABC123",
        summary="Test plan with 12 test cases",
        details=test_plan_dict,
    )
    
    if approval.status == ApprovalStatus.REJECTED:
        # Handle rejection - get modifications
        feedback = approval.feedback
        # Regenerate plan with feedback
    elif approval.status == ApprovalStatus.APPROVED:
        # Continue workflow
        pass
```

**Integration in agents**: Each V2 agent checks HITL mode before completion and can interrupt workflow for approval.

### Adapter Implementation Patterns

Create new application adapters for custom app types (see `adapters/web_adapter.py` example):

```python
from adapters.base_adapter import BaseApplicationAdapter, DiscoveryResult, Element
from models.test_case import TestCase
from models.test_result import TestResult

class MyCustomAdapter(BaseApplicationAdapter):
    """Adapter for custom application type"""
    
    def __init__(self, app_profile):
        super().__init__(app_profile)
        # Initialize application-specific clients
        self.client = MyAppClient(
            base_url=app_profile.base_url,
            auth=app_profile.auth,
        )
    
    def discover_elements(self) -> DiscoveryResult:
        """Discover pages, elements, and APIs"""
        result = DiscoveryResult()
        
        # Use tools to discover
        discovery_tool = ToolRegistry.get("my_discovery_tool")
        discovery_result = discovery_tool.execute(
            base_url=self.app_profile.base_url,
            auth_config=self.app_profile.auth
        )
        
        if discovery_result.is_success():
            result.elements = discovery_result.data['elements']
            result.pages = discovery_result.data['pages']
            result.apis = discovery_result.data.get('apis', [])
        
        return result
    
    def execute_test(self, test_case: TestCase) -> TestResult:
        """Execute a test case - implement your test logic here"""
        # Test execution logic specific to your app
        # Return TestResult with status, duration, output, error
        pass
    
    def validate_state(self) -> bool:
        """Check if app is ready for testing"""
        return self.client.is_healthy()
    
    def cleanup(self) -> None:
        """Close connections, cleanup resources"""
        self.client.close()

# Register adapter
from adapters import register_adapter
register_adapter("my_custom_adapter", MyCustomAdapter)

# Use in profile
# config/app_profiles.yaml:
# my_app:
#   adapter: "my_custom_adapter"
#   base_url: "https://myapp.com"
```

### RAG Integration Patterns

Add discovered elements and test results to knowledge base (see `rag/retriever.py`):

```python
from rag.retriever import TestKnowledgeRetriever

retriever = TestKnowledgeRetriever()

# Pattern 1: Add test cases to knowledge base
retriever.add_test_cases([
    {
        "app": "my_app",
        "feature": "login",
        "description": "Test login with valid credentials",
        "steps": [...],
        "expected_result": "User authenticated"
    },
    # ... more test cases
])

# Pattern 2: Search for similar tests (used during planning)
similar_tests = retriever.find_similar_tests(
    query="login with email",
    k=5,  # Top 5 similar tests
    app="my_app",
    doc_type="test_case"
)

# Pattern 3: Add test results for learning
test_result = {
    "test_id": "TEST-001",
    "status": "passed",
    "duration": 4.2,
    "app": "my_app",
    "feature": "login"
}
retriever.add_test_result(test_result)

# Pattern 4: Find failure patterns
failure_patterns = retriever.find_similar_tests(
    query="timeout error",
    k=3,
    doc_type="failure_pattern"
)
```

### Creating New Tools

1. **Create file** in appropriate `tools/` subdirectory
2. **Inherit from BaseTool**, implement execute() + metadata
3. **Add unit tests** in `tests/unit/test_your_tool.py` (mock external dependencies)
4. **Register** in `tools/auto_register.py` or let ToolRegistry auto-discover
5. **Use in agent** by calling `ToolRegistry.get("tool_name")`

**Example tool implementation:**
```python
# tools/my_category/my_new_tool.py
from tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata

class MyNewTool(BaseTool):
    """Tool description"""
    
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="my_new_tool",
            description="What this tool does",
            version="1.0.0",
            tags=["category", "subcategory"],
            is_safe=True,  # False if tool executes untrusted code
            requires_auth=False,
        )
    
    def execute(self, input_param: str, **kwargs) -> ToolResult:
        """
        Execute tool functionality
        
        Args:
            input_param: Main input parameter
            
        Returns:
            ToolResult with status, data, error, and metadata
        """
        # Use _wrap_execution for automatic error handling + timing
        return self._wrap_execution(self._process, input_param=input_param)
    
    def _process(self, input_param: str) -> ToolResult:
        """Internal processing logic"""
        try:
            # Your processing logic
            output = process_input(input_param)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={"result": output},
                metadata={"input_length": len(input_param)}
            )
        except ValueError as e:
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=str(e)
            )

# tools/auto_register.py - Register tool
# Add this line to auto_register.py:
# from tools.my_category.my_new_tool import MyNewTool
```

**Example test pattern** (see `conftest.py` for fixtures):
```python
# tests/unit/test_my_new_tool.py
import pytest
from tools.base import ToolRegistry
from unittest.mock import patch

class TestMyNewTool:
    @pytest.fixture
    def my_tool(self):
        """Get tool instance"""
        return ToolRegistry.get("my_new_tool", config={})
    
    def test_successful_execution(self, my_tool):
        """Test successful tool execution"""
        result = my_tool.execute(input_param="valid_input")
        
        assert result.is_success()
        assert result.data["result"] == expected_value
        assert result.execution_time > 0
    
    def test_invalid_input(self, my_tool):
        """Test error handling"""
        result = my_tool.execute(input_param="")
        
        assert result.is_failure()
        assert "required" in result.error.lower()
    
    def test_metadata(self, my_tool):
        """Test tool metadata"""
        metadata = my_tool.metadata
        
        assert metadata.name == "my_new_tool"
        assert metadata.is_safe == True
        assert "category" in metadata.tags
```

**Using your new tool in agents:**
```python
from tools.base import ToolRegistry

# In agent node function
def my_agent_node(state: MyState) -> MyState:
    # Get tool instance
    tool = ToolRegistry.get("my_new_tool")
    
    # Execute tool
    result = tool.execute(input_param=state['input'])
    
    # Handle result
    updated_state = dict(state)
    if result.is_success():
        updated_state['result'] = result.data
        updated_state['status'] = 'completed'
    else:
        updated_state['error'] = result.error
        updated_state['status'] = 'failed'
    
    return updated_state
```

---

## Common Development Scenarios

### Scenario 1: Add Support for New Application Type

1. Create adapter inheriting from `BaseApplicationAdapter` (see above)
2. Implement discovery, execution, validation, cleanup methods
3. Create application profile in `config/app_profiles.yaml`
4. Test with `python main.py discover --app your_app_name`

### Scenario 2: Improve Test Plan Quality

Test plan generation uses:
- `TestPlanGeneratorTool` - Creates plan with LLM
- `TestCaseExtractorTool` - Extracts test cases from plan
- `VectorSearchTool` + `TestPatternRetrieverTool` - Retrieves similar test patterns

To improve quality, enhance RAG knowledge base:
```python
from rag.retriever import TestKnowledgeRetriever

retriever = TestKnowledgeRetriever()
# Add your test cases and execution results
retriever.add_test_cases(your_test_cases)
retriever.add_test_result(your_test_result)
```

### Scenario 3: Add Custom Validation Logic

Create validation tools in `tools/validation/`:
```python
from tools.base import BaseTool, ToolResult, ToolStatus

class CustomValidatorTool(BaseTool):
    @property
    def metadata(self):
        return ToolMetadata(name="custom_validator", ...)
    
    def execute(self, data: dict) -> ToolResult:
        return self._wrap_execution(self._validate, data=data)
    
    def _validate(self, data: dict) -> ToolResult:
        # Your custom validation
        if is_valid(data):
            return ToolResult(status=ToolStatus.SUCCESS, data=data)
        else:
            return ToolResult(status=ToolStatus.FAILURE, error="Invalid data")
```

### Scenario 4: Enable HITL Approval Workflows

```python
from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2
from config.settings import get_settings

# Load settings from .env
settings = get_settings()  # HITL_MODE=APPROVE_PLAN

# Initialize with HITL enabled
orchestrator = OrchestratorAgentV2(
    app_profile=app_profile,
    enable_hitl=True,  # Enables approval workflow
)

# Run workflow - will pause at approval checkpoints
final_state = orchestrator.run_full_workflow(
    feature_description="Feature to test"
)

# Check approval status
summary = orchestrator.get_workflow_summary(final_state)
print(f"Pending approvals: {summary['pending_approvals']}")
```

### Scenario 5: Extend Discovery to Find Custom Elements

Create discovery tool for your app type:
```python
from tools.discovery.base import BaseDiscoveryTool

class MyCustomDiscoveryTool(BaseDiscoveryTool):
    def discover(self, app_profile) -> DiscoveryResult:
        result = DiscoveryResult()
        
        # Use app-specific client to discover
        client = MyAppClient(app_profile.base_url)
        
        # Discover elements
        elements = client.get_all_interactive_elements()
        result.elements = [Element(**elem) for elem in elements]
        
        # Discover pages
        pages = client.get_all_pages()
        result.pages = pages
        
        return result
```

### Scenario 6: Debug Agent Workflows

Enable debug logging to see node execution:
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run agent - will print detailed logs
discovery_state = discovery_agent.discover(app_profile)

# Inspect state at each step
print(f"Status: {discovery_state['status']}")
print(f"Elements: {discovery_state['elements']}")
print(f"Error: {discovery_state.get('error')}")
```

Or use the state checkpoint mechanism:
```python
from langgraph.checkpoint.memory import MemorySaver

# Create agent with checkpointing
orchestrator = OrchestratorAgentV2(
    app_profile=app_profile,
    enable_hitl=True,  # Enables checkpoints
)

# Workflow pauses at HITL points, allowing inspection
final_state = orchestrator.run_full_workflow(feature_description)

# Access intermediate states
print(f"Discovery state: {final_state['discovery_state']}")
print(f"Planning state: {final_state['planning_state']}")
```

---

Key Pydantic models in `models/`:
- **ApplicationProfile** - App configuration (type, adapter, auth, discovery params)
- **TestCase** - Test definition (description, steps, expected result)
- **TestResult** - Execution result (status, duration, output, failure reason)
- **Element** - Discovered UI element or API endpoint
- **DiscoveryResult** - Elements + pages + APIs from discovery
- **Approval** - HITL approval with status and human feedback

Always use these instead of creating custom dicts. They provide type safety + validation.

---

## Configuration & Profiles

**Application profiles** live in `config/app_profiles.yaml`:
```yaml
my_web_app:
  app_type: "web"
  adapter: "web_adapter"
  base_url: "https://myapp.com"
  test_framework: "playwright"
  discovery:
    max_depth: 3
    max_pages: 50
    exclude_patterns: ["/logout"]
  auth:
    auth_type: "basic"
    username: "${APP_USERNAME}"  # Supports env vars
    password: "${APP_PASSWORD}"
```

**Settings** from `.env` via `config/settings.py`:
- LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY/ANTHROPIC_API_KEY
- HITL_MODE, VECTOR_STORE
- TEST_FRAMEWORK, PARALLEL_EXECUTION, MAX_WORKERS

---

## RAG Knowledge Base

Vector-based retrieval stores test patterns. Located in `rag/`:
- `TestKnowledgeRetriever` - Main retrieval interface
- Uses FAISS or Chroma for embedding search
- Stores historical test cases and execution results

Usage:
```python
from rag.retriever import TestKnowledgeRetriever

retriever = TestKnowledgeRetriever()
similar = retriever.find_similar_tests(query="login", k=5, app="my_app")
```

---

## Testing Best Practices

**Unit tests** (`tests/unit/`) - Mock everything, test tool logic in isolation
- Mock ToolRegistry.get() to control tool behavior
- Use conftest.py fixtures: sample_web_app_profile, mock_playwright_page, etc.
- Tag with `@pytest.mark.unit`

**Integration tests** (`tests/integration/`) - Use real agents + mocked external services
- Test agent state flow end-to-end
- Mock LLM calls, not tools
- Tag with `@pytest.mark.integration`

**Test markers**: unit, integration, slow, security

---

## Common Gotchas & Patterns

1. **Don't embed logic in agents** - Extract to tools. Agents orchestrate, tools execute.

2. **State is immutable** - Return new dicts/objects from node functions, don't mutate input state.

3. **Tool registry needs reset** - Use `reset_tool_registry` fixture in tests (auto-clears registry before/after each test).

4. **V1 is legacy** - If modifying existing V1 agents, consider migrating to V2 first (see `docs/MIGRATION_GUIDE.md`).

5. **FAISS is insecure** - Current vector store uses pickle (insecure deserialization). Be careful with untrusted vector store files.

6. **Use ApplicationProfile, not dicts** - Pydantic validation catches config errors early.

7. **LangGraph checkpoints** - Agent workflows support resumption via MemorySaver (stateful).

---

## Key Files Reference

- **`main.py`** - CLI entry point, command routing
- **`agents_v2/orchestrator_agent_v2.py`** - Master workflow coordinator
- **`agents_v2/state.py`** - All state schemas (TypedDict definitions)
- **`tools/base.py`** - BaseTool + ToolRegistry definitions
- **`tools/registry.py`** - Tool discovery and management
- **`adapters/base_adapter.py`** - Adapter interface + DiscoveryResult
- **`models/app_profile.py`** - ApplicationProfile Pydantic model
- **`config/settings.py`** - Settings from .env
- **`config/app_profiles.yaml`** - Application configurations
- **`hitl/approval_manager.py`** - HITL workflow logic
- **`docs/ARCHITECTURE_V2.md`** - Detailed V2 documentation

---

## Streamlit Web UI (Frontend)

Short summary: the Streamlit UI is a lightweight front-end used for user sign-in, interactive conversations, and orchestration of agent workflows. It both invokes V2 agents directly from pages and uses the `StateManager`/`RedisManager` to cache workflow state and session data for visibility and approval handoffs.

Files to know:
- `streamlit_ui/app.py` — entry point and session bootstrap (calls `AuthManager`, `StateManager`, sets session vars)
- `streamlit_ui/config.py` — page, redis, LLM and auth defaults (environment-backed)
- `streamlit_ui/auth.py` — `AuthManager` with streamlit-authenticator and default users
- `streamlit_ui/pages/*` — multi-page UI; important pages:
  - `02_🔍_Discovery.py` — calls `DiscoveryAgentV2` (autonomous + interactive)
  - `03_📋_Test_Planning.py` — calls `TestPlannerAgentV2` / conversational orchestrator
  - `07_🔄_Full_Workflow.py` — wizard for running full workflows (currently simulates stages; real implementation should call `OrchestratorAgentV2.run_full_workflow`)
  - `08_📊_Monitor.py` — shows session + orchestrator status from `StateManager`

How the UI orchestrates agents (practical notes):
- Pages call V2 agents directly (e.g., `DiscoveryAgentV2`, `TestPlannerAgentV2`, `ConversationalOrchestratorAgent`). Look at `streamlit_ui/pages/02_🔍_Discovery.py` and `03_📋_Test_Planning.py` for examples where agents are instantiated and their `discover()` / `create_plan()` methods are invoked.
- Results are cached using `StateManager` (in `memory/state_manager.py`) and optionally persisted in Redis via `RedisManager`. The UI uses `state_manager.cache_*` helpers to store discovery/planning/generation results for the session.
- For interactive flows, the UI stores a conversational orchestrator instance in `st.session_state.orchestrator` so subsequent pages can continue the conversation and resume context.

HITL / approvals integration:
- Agents that require human approval create an approval object and write it to `approvals/` (see `_request_approval_node` in `agents_v2/test_planner_agent_v2.py`).
- The `hitl/review_interface.WebReviewer` expects a web UI to pick up these approval JSON files and update them (change `status` to `APPROVED` / `REJECTED` / `MODIFIED`, set `approved_by`, `comments`, etc.). The WebReviewer polls the file and returns the decision to the agent.
- A full-featured **approvals management page** is already implemented at `streamlit_ui/pages/09_Approvals.py` — it lists, approves, rejects, and allows raw JSON editing of approval requests.

### Run Streamlit locally (Windows cmd / PowerShell):
```cmd
# Option 1: Run full UI (recommended)
streamlit run streamlit_ui/app.py --server.port 8501

# Option 2: Run just the approvals page for testing
streamlit run streamlit_ui/pages/09_Approvals.py --server.port 8501

# Option 3: Run with test mode enabled (auto-authenticates as test_user)
set TESTING=1
streamlit run streamlit_ui/app.py --server.port 8501
```

**Environment variables** (Windows set / PowerShell $env:):
```cmd
REM Common settings
set REDIS_HOST=localhost
set REDIS_PORT=6379
set OPENAI_API_KEY=sk-...
set LLM_PROVIDER=openai
set LLM_MODEL=gpt-4

REM Streamlit/approvals specific
set AUTH_COOKIE_KEY=your_secret_key
set ADMIN_PASSWORD=admin
set TESTER_PASSWORD=tester
set APPROVALS_DIR=./approvals
set TESTING=1
```

**Testing the approvals page:**
- When `TESTING=1`, the page auto-authenticates (no login required) and shows test-only approve/reject buttons ([TEST] hook buttons).
- The `APPROVALS_DIR` env var allows tests to use a custom approvals directory (e.g., temp path).
- Run approval tests:
  ```cmd
  python -m pytest tests/unit/test_approvals_*.py -q
  python -m pytest tests/integration/test_streamlit_approvals_e2e.py -q
  ```

### Troubleshooting Streamlit issues:

**Port already in use:**
```cmd
REM Find and use a different port
streamlit run streamlit_ui/app.py --server.port 8502
```

**"Missing env var OPENAI_API_KEY":**
```cmd
REM Set the API key before running
set OPENAI_API_KEY=sk-your-key-here
streamlit run streamlit_ui/app.py
```

**"WebReviewer not picking up approvals":**
- Ensure agents write approvals to `approvals/` directory (check agent logs).
- Verify the Streamlit approvals page is running (`streamlit run streamlit_ui/pages/09_Approvals.py`).
- Manually check `approvals/*.json` and update status to `APPROVED` to test the WebReviewer polling.

**fakeredis warning:**
- This is expected if Redis is not installed. Session data will be lost on Streamlit restart. Install Redis for persistence:
  ```cmd
  pip install redis
  REM Or use WSL: wsl apt-get install redis-server
  ```

Where to extend:
- Integrate real `OrchestratorAgentV2.run_full_workflow()` in `07_🔄_Full_Workflow.py` (currently simulated).
- Add role-based access control to approvals page (only admins can approve, etc.).
- Add pagination and filtering to the approvals page for large approval queues.

Notes & gotchas:
- The Streamlit UI uses `fakeredis` (in-memory) when Redis is not configured — session data is lost on restart.
- Pages may simulate agent stages for demo; check comments before assuming real orchestration is happening.
- To use web-based approvals with agents, ensure `Approval` JSONs are written to `approvals/` and the UI updates them; `WebReviewer` polls that directory.
- The approvals page respects `TESTING` env var and `APPROVALS_DIR` for test isolation.

---

## Running in Production


---

## Troubleshooting & Tips

### Common Issues & Solutions

**Issue: Tool not found in ToolRegistry**
- Solution: Ensure tool is registered in `tools/auto_register.py`
- Check that tool class name matches registration name (kebab-case → snake_case)
- Verify `import tools.auto_register` is called before using tools

**Issue: State mutation errors in LangGraph**
- Solution: Always return NEW state dict, never mutate input
- Use `updated_state = dict(state)` to create shallow copy
- Check that node functions return the modified state

**Issue: Tool execution times out**
- Solution: Check tool's `_process()` method for infinite loops
- Verify external service (LLM, database) is responding
- Use `execution_time` in ToolResult to identify bottlenecks

**Issue: Discovery finds too few/many elements**
- Solution: Adjust `max_depth`, `max_pages`, `exclude_patterns` in DiscoveryConfig
- Check that CSS selectors are correct for target app
- Verify adapter type matches application (web vs API)

**Issue: Generated tests don't pass**
- Solutions:
  - Review generated script syntax (use ScriptValidatorTool)
  - Check test case descriptions are accurate
  - Verify app_profile auth settings are correct
  - Examine test execution logs in `test_results/`

### Performance Optimization Tips

1. **Parallel Execution**: Set `PARALLEL_EXECUTION=true` and `MAX_WORKERS=4`
2. **Discovery Limits**: Use `max_pages=50`, `max_depth=3` for faster discovery
3. **Tool Caching**: Some tools cache results (RAG retriever, web adapter)
4. **Headless Mode**: Always use `HEADLESS_MODE=true` for Playwright tests (2-3x faster)
5. **Batch Processing**: Process multiple test cases in discovery/planning to amortize costs

### Debugging Techniques

1. **Enable Debug Logging**:
    ```python
    import logging
    logging.basicConfig(level=logging.DEBUG)
    ```

2. **Inspect State at Each Step**:
    ```python
    state = agent.run_full_workflow(...)
    print(json.dumps(state, indent=2, default=str))  # Pretty print state
    ```

3. **Test Individual Tools**:
    ```python
    tool = ToolRegistry.get("tool_name")
    result = tool.execute(param="test")
    print(f"Result: {result.data}, Error: {result.error}")
    ```

4. **Check Tool Metadata**:
    ```python
    for tool_name in ToolRegistry.list_tools():
         tool = ToolRegistry.get(tool_name)
         print(f"{tool.metadata.name}: {tool.metadata.description}")
    ```

5. **Profile Execution**:
    ```python
    import time
    start = time.time()
    result = tool.execute(...)
    print(f"Took {time.time() - start}s, Tool reported {result.execution_time}ms")
    ```

### Testing Tips

1. **Mock External Services**: Use `unittest.mock.Mock` for LLM calls, databases, web browsers
2. **Use Fixtures**: Conftest provides `sample_web_app_profile`, `mock_playwright_page`, etc.
3. **Test Tool Logic, Not Integration**: Unit tests should test `_process()` method, not `execute()`
4. **Async Tests**: Some agents use async; mark tests with `@pytest.mark.asyncio`
5. **Isolation**: Reset ToolRegistry between tests using `reset_tool_registry` fixture

### When to Use V2 vs V1

| Task | Version | Location |
|------|---------|----------|
| New agent feature | V2 | `agents_v2/` |
| New tool | V2 | `tools/` |
| New discovery method | V2 | `tools/discovery/` + `DiscoveryAgentV2` |
| New test framework support | V2 | `tools/generation/` + `TestGeneratorAgentV2` |
| Maintenance of existing V1 | V1 | `agents/` (minimal changes) |
| Bug fix in test execution | V2 | `agents_v2/test_executor_agent_v2.py` or tool |

---

## CI/CD and Testing

### GitHub Actions Workflow

A CI workflow is configured in `.github/workflows/ci.yml` to:
1. Install Python dependencies (including Playwright for browser automation)
2. Run unit tests (`tests/unit/`)
3. Run integration tests (`tests/integration/`)

The workflow runs on every push to `main` and on pull requests.

### Running Tests Locally (Windows)

**Setup (one-time):**
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest requests playwright
python -m playwright install --with-deps
```

**Run unit tests:**
```cmd
python -m pytest tests\unit -q
```

**Run integration tests:**
```cmd
python -m pytest tests\integration -q
```

**Run all tests:**
```cmd
python -m pytest tests\unit tests\integration -q
```

**Run with verbose output:**
```cmd
python -m pytest tests\unit tests\integration -v
```

### Approvals Page Tests

Specific tests for the Streamlit approvals page are in:
- `tests/unit/test_approvals_fs.py` — File I/O and approve/reject behavior
- `tests/unit/test_approvals_streamlit_behavior.py` — JSON parsing, file ordering, edit validation
- `tests/integration/test_streamlit_approvals_e2e.py` — Full approvals workflow simulation

Run approvals tests:
```cmd
python -m pytest tests\unit\test_approvals_*.py tests\integration\test_streamlit_approvals_e2e.py -v
```

### Test Environment Variables

- `TESTING=1` — Enable test mode (auto-authenticate Streamlit, show test-only buttons)
- `APPROVALS_DIR=path/to/temp/dir` — Override approvals directory for test isolation
- `REDIS_HOST`, `REDIS_PORT` — Optional Redis for session persistence (fakeredis used by default)

### Test Markers

Tests are marked with pytest markers for organization:
- `@pytest.mark.unit` — Isolated, fast tests (no external services)
- `@pytest.mark.integration` — Tests that integrate multiple components
- `@pytest.mark.slow` — Long-running tests (can be skipped with `-m "not slow"`)
- `@pytest.mark.security` — Security-related tests

Run only fast tests:
```cmd
python -m pytest -m "not slow" -q
```

### Common Testing Patterns

1. **Mock tool registry in tests:**
   ```python
   from unittest.mock import patch
   
   @patch('tools.base.ToolRegistry.get')
   def test_my_function(self, mock_get):
       mock_tool = MagicMock()
       mock_tool.execute.return_value = ToolResult(status=ToolStatus.SUCCESS, data={})
       mock_get.return_value = mock_tool
       # Test function that uses tool
   ```

2. **Use fixtures for app profiles:**
   ```python
   from tests.conftest import sample_web_app_profile
   
   def test_with_profile(sample_web_app_profile):
       # sample_web_app_profile is a pre-configured ApplicationProfile
       discovery = DiscoveryAgentV2(app_profile=sample_web_app_profile)
       # Test logic
   ```

3. **Test approvals file I/O:**
   ```python
   def test_approve_workflow(tmp_path):
       approvals_dir = tmp_path / "approvals"
       # Create test approval JSON, modify status, assert file updated
   ```

---