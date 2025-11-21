# Test Failures Analysis and Corrections

## Summary
- **Total Tests**: 164
- **Passing**: 122 (74%)
- **Failing**: 40 (24%)
- **Skipped**: 2 (1%)

## Critical Issues Identified

### 1. LangGraph Checkpoint Configuration Error
**Affected Tests**: All DiscoveryAgentV2 and TestPlannerAgentV2 integration tests (18 tests)

**Error**: `Checkpointer requires one or more of the following 'configurable' keys: thread_id, checkpoint_ns, checkpoint_id`

**Root Cause**:
- File: `agents_v2/discovery_agent_v2.py:341`
- The graph is compiled with `MemorySaver()` checkpointer (line 113)
- The `discover()` method invokes the graph without providing required configuration

**Fix Required**:
```python
# In agents_v2/discovery_agent_v2.py, line 341
# Change from:
final_state = self.graph.invoke(initial_state)

# To:
final_state = self.graph.invoke(
    initial_state,
    config={"configurable": {"thread_id": "discovery_session"}}
)
```

**Same fix needed for**:
- `agents_v2/test_planner_agent_v2.py` - plan() method
- `agents_v2/test_executor_agent_v2.py` - execute() method (if using checkpointer)

---

### 2. Tool Registry Configuration Handling
**Affected Tests**: 6 tests in `test_tool_framework.py`

**Error**: `ValueError: Could not register ConfigurableTool: required_param is missing from config`

**Root Cause**:
- File: `tools/base.py:230`
- The registry tries to create a dummy instance of tools for registration
- Some tools have custom required config parameters not in the dummy config

**Fix Required**:
```python
# In tools/base.py, around line 220, update dummy_config:
dummy_config = {
    "output_dir": ".",
    "knowledge_base_dir": ".",
    "app_profile": dummy_app_profile,
    "required_param": "dummy_value",  # Add this
}
```

**Alternative Fix** (Better approach):
Allow registration without instantiation for tools with custom config requirements:
```python
@classmethod
def register(cls, tool_class: type, skip_validation: bool = False) -> None:
    """
    Register a tool class

    Args:
        tool_class: Tool class to register
        skip_validation: Skip instantiation validation
    """
    if not issubclass(tool_class, BaseTool):
        raise ValueError(f"{tool_class.__name__} must inherit from BaseTool")

    if skip_validation:
        # Register without instantiation
        tool_name = tool_class.__name__.lower().replace('tool', '')
        cls._registry[tool_name] = tool_class
        logger.debug(f"Registered {tool_name} (validation skipped)")
        return

    # ... rest of existing logic
```

---

### 3. HTML Sanitizer Not Removing Content Inside Tags
**Affected Tests**: 3 tests in `test_validation_tools.py`

**Error**: Test expects `"alert"` to be removed from `<script>alert('xss')</script>`, but only tags are removed

**Output**: `"Hello alert'xss' world"` (should be `"Hello  world"`)

**Root Cause**:
- File: `tools/validation/input_sanitizer.py`
- The HTML removal only strips tags but keeps their content

**Fix Required**:
```python
# In tools/validation/input_sanitizer.py
# Update the HTML removal logic:

def _remove_html_tags(self, text: str) -> str:
    """Remove HTML tags and their content if they're dangerous"""
    import re

    # Dangerous tags to remove completely (including content)
    dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed']

    for tag in dangerous_tags:
        # Remove tag and its content
        pattern = f'<{tag}[^>]*>.*?</{tag}>'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove remaining HTML tags (keep content)
    text = re.sub(r'<[^>]+>', '', text)

    return text.strip()
```

---

### 4. Test Executor Agent Failures
**Affected Tests**: 9 tests in `test_test_executor_agent_v2.py`

**Common Issues**:
1. Mock expectations not matching actual implementation
2. Missing thread_id configuration (if using checkpointer)
3. State transition expectations mismatch

**Investigation Needed**: Check if TestExecutorAgentV2 also uses MemorySaver checkpointer

---

### 5. Oracle Modules Configuration Warning
**Warning**: `error parsing value for field "oracle_modules" from source "DotEnvSettingsSource"`

**Fix**: Already addressed in `.env` file - line 14 commented out

---

## Quick Win Fixes (High Priority)

### Priority 1: Fix LangGraph Configuration
**Impact**: Fixes 18 integration tests
**Effort**: Low (single line change in 3 files)
**Files**:
- `agents_v2/discovery_agent_v2.py:341`
- `agents_v2/test_planner_agent_v2.py` (similar location)
- `agents_v2/test_executor_agent_v2.py` (similar location)

### Priority 2: Fix HTML Sanitizer
**Impact**: Fixes 3 unit tests
**Effort**: Low (update single method)
**File**: `tools/validation/input_sanitizer.py`

### Priority 3: Fix Tool Registry
**Impact**: Fixes 6 unit tests
**Effort**: Medium (add skip_validation parameter)
**File**: `tools/base.py`

---

## Expected Results After Fixes

| Fix Applied | Additional Tests Passing | Total Passing |
|-------------|-------------------------|---------------|
| LangGraph Config | +18 | 140/164 (85%) |
| HTML Sanitizer | +3 | 143/164 (87%) |
| Tool Registry | +6 | 149/164 (91%) |

**Remaining failures** would likely be:
- Test executor integration tests (mock expectations)
- Some RAG tool tests (require actual vector store)
- Discovery tool integration tests (adapter mocking issues)

---

## Implementation Order

1. ✅ **LangGraph Configuration** (Highest Impact)
2. ✅ **HTML Sanitizer** (Quick Win)
3. ✅ **Tool Registry** (Moderate Complexity)
4. 🔍 **Test Executor Mocks** (Requires Investigation)
5. 🔍 **Remaining Integration Tests** (Case-by-case basis)

---

## Notes

- All Pydantic deprecation warnings should be addressed by updating to `ConfigDict` instead of class-based `Config`
- The warning about `schema` field shadowing can be resolved by renaming the field
- Integration tests may need actual LLM mocks or test API keys for full passing

