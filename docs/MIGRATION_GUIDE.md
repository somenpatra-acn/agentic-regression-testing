## Migration Guide: V1 to V2

### Overview

This guide helps you migrate from the V1 architecture (embedded tools in agents) to V2 architecture (separated tools with LangGraph).

---

## Migration Strategy

### Option 1: Gradual Migration (Recommended)

Keep V1 and V2 running side-by-side during transition:

```
agents/          # V1 agents (keep for now)
agents_v2/       # V2 agents (new)
tools/           # Shared tools (used by V2)
```

**Benefits:**
- Low risk
- Can validate V2 behavior against V1
- Gradual user adoption

### Option 2: Big Bang Migration

Replace all agents at once:

**Benefits:**
- Clean break
- Faster completion

**Risks:**
- Higher risk of issues
- Requires extensive testing

---

## Step-by-Step Migration

### Step 1: Install Dependencies

```bash
# Update requirements
pip install -r requirements.txt

# New dependency: langgraph
pip install langgraph>=0.0.40
```

### Step 2: Register Tools

Update your initialization code to register tools:

**Before (V1):**
```python
from agents.discovery import DiscoveryAgent

agent = DiscoveryAgent(app_profile)
result = agent.discover()
```

**After (V2):**
```python
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from tools import register_tool
from tools.validation.input_sanitizer import InputSanitizerTool
from tools.discovery.web_discovery import WebDiscoveryTool

# Register required tools (do this once at startup)
register_tool(InputSanitizerTool)
register_tool(WebDiscoveryTool)

# Create and use agent
agent = DiscoveryAgentV2(app_profile=app_profile)
final_state = agent.discover()
result = agent.get_discovery_result(final_state)
```

### Step 3: Update Configuration

No configuration changes required! V2 uses the same `ApplicationProfile` format.

### Step 4: Update Code Using Agents

**Discovery Agent:**

```python
# V1
from agents.discovery import DiscoveryAgent
agent = DiscoveryAgent(app_profile)
result = agent.discover()

# Access results
elements = result.elements
pages = result.pages

# V2
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
agent = DiscoveryAgentV2(app_profile=app_profile)
final_state = agent.discover()
result = agent.get_discovery_result(final_state)

# Access results (same structure)
elements = result["elements"]
pages = result["pages"]
```

### Step 5: Run Tests

```bash
# Test V2 components
pytest tests/unit/ -m unit
pytest tests/integration/ -m integration

# Compare V1 vs V2 behavior (if both exist)
pytest tests/comparison/ -m comparison
```

---

## Breaking Changes

### 1. Return Format

**V1:** Returns Pydantic model directly
```python
result: DiscoveryResult = agent.discover()
print(result.elements[0].id)
```

**V2:** Returns state dict, use helper to get formatted result
```python
final_state: DiscoveryState = agent.discover()
result: Dict = agent.get_discovery_result(final_state)
print(result["elements"][0]["id"])
```

**Migration:**
```python
# Add helper function for V1 compatibility
def v1_compatible_discover(agent_v2):
    final_state = agent_v2.discover()
    result_dict = agent_v2.get_discovery_result(final_state)

    # Convert to V1 format if needed
    return DiscoveryResult(**result_dict["discovery_result"])
```

### 2. Tool Registration Required

**V1:** Tools embedded, no registration needed

**V2:** Must register tools before use

**Migration:**
Create a startup module:

```python
# startup.py
from tools import register_tool
from tools.validation.input_sanitizer import InputSanitizerTool
from tools.validation.path_validator import PathValidatorTool
from tools.discovery.web_discovery import WebDiscoveryTool
from tools.discovery.api_discovery import APIDiscoveryTool

def register_all_tools():
    """Register all tools at application startup"""
    register_tool(InputSanitizerTool)
    register_tool(PathValidatorTool)
    register_tool(WebDiscoveryTool)
    register_tool(APIDiscoveryTool)
    # ... add more as they're created

# Call once at startup
register_all_tools()
```

### 3. Error Handling

**V1:** Raises exceptions
```python
try:
    result = agent.discover()
except Exception as e:
    print(f"Discovery failed: {e}")
```

**V2:** Returns error in state
```python
final_state = agent.discover()
if final_state["status"] == "failed":
    print(f"Discovery failed: {final_state['error']}")
```

---

## Feature Mapping

### Discovery

| Feature | V1 | V2 |
|---------|----|----|
| Web discovery | `DiscoveryAgent` | `DiscoveryAgentV2` + `WebDiscoveryTool` |
| API discovery | `DiscoveryAgent` | `DiscoveryAgentV2` + `APIDiscoveryTool` |
| Input validation | ❌ Not available | ✅ `InputSanitizerTool` |
| Path validation | ❌ Not available | ✅ `PathValidatorTool` |
| State tracking | Implicit | Explicit `DiscoveryState` |
| HITL | Custom implementation | LangGraph interrupts |

### Test Planning

| Feature | V1 | V2 |
|---------|----|----|
| Test planning | `TestPlannerAgent` | ⏳ `TestPlannerAgentV2` (pending) |
| RAG integration | ✅ Embedded | ⏳ `RAGTool` (pending) |
| Gap analysis | ✅ Built-in | ⏳ `GapAnalysisTool` (pending) |

### Test Generation

| Feature | V1 | V2 |
|---------|----|----|
| Test generation | `TestGeneratorAgent` | ⏳ `TestGeneratorAgentV2` (pending) |
| Script validation | ❌ Basic | ⏳ `ScriptValidatorTool` (pending) |
| Multi-framework | ✅ Yes | ⏳ Yes (pending) |

---

## Common Migration Issues

### Issue 1: Tool Not Found

**Error:**
```
ValueError: Tool 'web_discovery' not found
```

**Solution:**
Register the tool before use:
```python
from tools import register_tool
from tools.discovery.web_discovery import WebDiscoveryTool

register_tool(WebDiscoveryTool)
```

### Issue 2: Missing LangGraph Dependency

**Error:**
```
ModuleNotFoundError: No module named 'langgraph'
```

**Solution:**
```bash
pip install langgraph>=0.0.40
```

### Issue 3: State Dict vs Pydantic Model

**Error:**
```
AttributeError: 'dict' object has no attribute 'elements'
```

**Solution:**
V2 returns dicts, not Pydantic models. Use dict access:
```python
# V1
elements = result.elements

# V2
result_dict = agent.get_discovery_result(final_state)
elements = result_dict["elements"]
```

---

## Testing Your Migration

### Unit Tests

Create tests to ensure behavior matches:

```python
def test_v1_v2_equivalence():
    """Test that V2 produces same results as V1"""
    app_profile = load_test_profile()

    # V1 result
    agent_v1 = DiscoveryAgent(app_profile)
    result_v1 = agent_v1.discover()

    # V2 result
    register_all_tools()
    agent_v2 = DiscoveryAgentV2(app_profile=app_profile)
    final_state = agent_v2.discover()
    result_v2 = agent_v2.get_discovery_result(final_state)

    # Compare
    assert len(result_v1.elements) == len(result_v2["elements"])
    assert len(result_v1.pages) == len(result_v2["pages"])
```

### Integration Tests

Run full workflows and compare:

```bash
# Run V1 workflow
python main.py run --app test_app --feature "login" --use-v1

# Run V2 workflow
python main.py run --app test_app --feature "login" --use-v2

# Compare results
python scripts/compare_results.py v1_results.json v2_results.json
```

---

## Rollback Plan

If you need to rollback to V1:

### 1. Keep V1 Code

Don't delete V1 agents during migration:

```
agents/              # Keep V1 (don't delete)
agents_v2/           # V2 (new)
```

### 2. Feature Flag

Use feature flags to switch between versions:

```python
USE_V2_AGENTS = os.getenv("USE_V2_AGENTS", "false").lower() == "true"

if USE_V2_AGENTS:
    from agents_v2.discovery_agent_v2 import DiscoveryAgentV2 as DiscoveryAgent
else:
    from agents.discovery import DiscoveryAgent
```

### 3. Quick Rollback

```bash
# Rollback to V1
export USE_V2_AGENTS=false

# Or update .env file
echo "USE_V2_AGENTS=false" >> .env
```

---

## Migration Checklist

### Pre-Migration

- [ ] Review V2 architecture documentation
- [ ] Understand breaking changes
- [ ] Plan migration timeline
- [ ] Set up V2 test environment
- [ ] Create rollback plan

### During Migration

- [ ] Install LangGraph dependency
- [ ] Register all required tools
- [ ] Update agent instantiation code
- [ ] Update result access patterns
- [ ] Update error handling
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Compare V1 vs V2 behavior

### Post-Migration

- [ ] Monitor production for issues
- [ ] Gather user feedback
- [ ] Update documentation
- [ ] Train team on V2 architecture
- [ ] Plan V1 deprecation timeline

---

## Support

### Getting Help

- **Documentation:** Check `docs/ARCHITECTURE_V2.md`
- **Examples:** See `examples/v2/`
- **Tests:** Review `tests/integration/test_discovery_agent_v2.py`
- **Issues:** Report at GitHub issues

### Common Questions

**Q: Can I use V1 and V2 together?**
A: Yes! They can coexist. Use feature flags to switch.

**Q: Do I need to migrate everything at once?**
A: No. Start with Discovery Agent, then migrate others incrementally.

**Q: Will my YAML configs work with V2?**
A: Yes! V2 uses the same `ApplicationProfile` format.

**Q: How do I know if migration succeeded?**
A: Run comparison tests between V1 and V2 results.

---

## Timeline Estimate

| Component | Effort | Dependencies |
|-----------|--------|--------------|
| Discovery Agent | 1 day | Tools registered |
| Test Planner | 2 days | RAG tools ready |
| Test Generator | 2 days | Validation tools ready |
| Test Executor | 1 day | Sandboxing implemented |
| Orchestrator | 3 days | All agents migrated |
| Testing & Validation | 2 days | All components ready |
| **Total** | **11 days** | Sequential + parallel work |

---

## Success Criteria

Migration is successful when:

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ V2 produces equivalent results to V1
- ✅ Performance is equal or better
- ✅ No regressions in functionality
- ✅ Team trained on new architecture
- ✅ Documentation complete

---

## Next Steps

1. **Start with Discovery Agent** (✅ COMPLETED - PoC ready)
2. **Validate behavior** (⏳ Your task: run comparison tests)
3. **Migrate next agent** (⏳ Test Planner recommended)
4. **Iterate** (⏳ Continue with remaining agents)

Good luck with your migration! 🚀
