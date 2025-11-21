# Files to Remove After Refactoring

## Summary
After completing the V1 → V2 refactoring, the following files are no longer needed and can be safely removed.

---

## 1. Legacy Agents Directory (7 files)

**Directory**: `agents/`
**Status**: Replaced by `agents_v2/`
**Impact**: Used by `main.py` - needs migration first

### Files:
- ❌ `agents/__init__.py` - Old agent exports
- ❌ `agents/discovery.py` - Replaced by `agents_v2/discovery_agent_v2.py`
- ❌ `agents/orchestrator.py` - Replaced by `agents_v2/orchestrator_agent_v2.py`
- ❌ `agents/reporting.py` - Replaced by `agents_v2/reporting_agent_v2.py`
- ❌ `agents/test_executor.py` - Replaced by `agents_v2/test_executor_agent_v2.py`
- ❌ `agents/test_generator.py` - Replaced by `agents_v2/test_generator_agent_v2.py`
- ❌ `agents/test_planner.py` - Replaced by `agents_v2/test_planner_agent_v2.py`

**⚠️ WARNING**: Cannot remove until `main.py` is updated to use `agents_v2`

---

## 2. Redundant Documentation Files (7 files)

### Refactoring Documentation (Can Consolidate)
These are interim documentation files created during the refactoring process:

- ❓ `REFACTORING_SUMMARY.md` - Superseded by `COMPLETE_REFACTORING_SUMMARY.md`
- ❓ `TEST_EXECUTOR_MIGRATION_SUMMARY.md` - Detailed migration notes (archival value)
- ❓ `TEST_PLANNER_MIGRATION_SUMMARY.md` - Detailed migration notes (archival value)
- ❓ `BUSINESS_ANALYSIS.md` - Initial analysis document (archival value)
- ❓ `DOCUMENTATION_ANALYSIS.md` - Documentation audit (archival value)
- ❓ `EPCC_EXPLORE.md` - Exploration notes (archival value)

### Recent Analysis Files (Keep)
- ✅ `COMPLETE_REFACTORING_SUMMARY.md` - **KEEP** (Primary refactoring doc)
- ✅ `TEST_FAILURES_ANALYSIS.md` - **KEEP** (Current test analysis)
- ✅ `TEST_IMPROVEMENTS_SUMMARY.md` - **KEEP** (Current test status)

### README Files
- ❓ `README.md` - Original README (might need update)
- ✅ `README_V2.md` - **KEEP** (V2 documentation)
- ✅ `QUICKSTART.md` - **KEEP** (User guide)
- ✅ `DEMO_GUIDE.md` - **KEEP** (Demo documentation)
- ✅ `CLAUDE.md` - **KEEP** (Claude-specific notes)

**Recommendation**: Move archival docs to `docs/archive/` instead of deleting

---

## 3. Old Example Files

Check if these use V1 agents:
- ❓ `examples/custom_app_example.py` - **CHECK**: May use old agents
- ❓ `examples/simple_example.py` - **CHECK**: May use old agents

**Action Required**: Verify and update to use `agents_v2` or remove

---

## 4. Temporary/Generated Files

### Pycache Directories
- 🗑️ `agents/__pycache__/` - Python bytecode cache
- 🗑️ `agents_v2/__pycache__/` - Python bytecode cache (can regenerate)
- 🗑️ `*/__pycache__/` - All pycache directories

**Note**: These regenerate automatically, safe to remove

---

## Removal Strategy

### Phase 1: Safe Removals (Do Now) ✅
1. Remove all `__pycache__` directories
2. Move archival documentation to `docs/archive/`:
   - `REFACTORING_SUMMARY.md`
   - `BUSINESS_ANALYSIS.md`
   - `DOCUMENTATION_ANALYSIS.md`
   - `EPCC_EXPLORE.md`
   - `TEST_EXECUTOR_MIGRATION_SUMMARY.md`
   - `TEST_PLANNER_MIGRATION_SUMMARY.md`

### Phase 2: Update Dependencies (Required Before Phase 3) ⚠️
1. Update `main.py` to use `agents_v2.orchestrator_agent_v2.OrchestratorAgentV2`
2. Update `examples/` to use `agents_v2`
3. Run tests to verify everything still works

### Phase 3: Remove Legacy Code (Do After Phase 2) 🔴
1. Remove entire `agents/` directory
2. Remove old example files (if not updated)

---

## Files That MUST Stay ✅

### Core V2 Code
- ✅ `agents_v2/` - New refactored agents
- ✅ `tools/` - Reusable tool framework
- ✅ `tests/` - Test suite

### Shared Infrastructure
- ✅ `adapters/` - Application adapters
- ✅ `models/` - Data models
- ✅ `config/` - Configuration
- ✅ `utils/` - Utilities
- ✅ `rag/` - RAG components
- ✅ `hitl/` - HITL interface

### Current Documentation
- ✅ `README_V2.md`
- ✅ `QUICKSTART.md`
- ✅ `DEMO_GUIDE.md`
- ✅ `COMPLETE_REFACTORING_SUMMARY.md`
- ✅ `TEST_FAILURES_ANALYSIS.md`
- ✅ `TEST_IMPROVEMENTS_SUMMARY.md`

### Configuration Files
- ✅ `.env` - Environment config
- ✅ `.env.example` - Environment template
- ✅ `requirements.txt` - Dependencies
- ✅ `pyproject.toml` - Project config

---

## Disk Space to Reclaim

Estimated space savings:
- `agents/` directory: ~200 KB
- `__pycache__/` directories: ~5-10 MB
- Archival documentation: ~200 KB
- **Total**: ~10-11 MB

---

## Recommendation

### Immediate Actions (Low Risk):
1. ✅ Remove all `__pycache__` directories
2. ✅ Create `docs/archive/` and move old documentation
3. ✅ Update `README.md` to point to `README_V2.md`

### Deferred Actions (Requires Testing):
1. ⏳ Update `main.py` to use `agents_v2`
2. ⏳ Update examples to use `agents_v2`
3. ⏳ Run full test suite to verify
4. ⏳ Remove `agents/` directory once verified

---

## Next Steps

Would you like me to:
1. **Proceed with Phase 1** (safe removals)?
2. **Update main.py first** (Phase 2)?
3. **Create backup** before removal?
4. **Archive instead of delete** legacy agents?

