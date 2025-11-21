# Demo Scripts Guide

This guide explains the demo scripts available for the Agentic AI Regression Testing Framework V2.

---

## Available Demos

### 1. Complete Orchestrator Workflow Demo
**File**: `demo_orchestrator_v2.py`

**What it shows**: Complete end-to-end workflow with detailed output and progress tracking.

**Features**:
- ✅ Full orchestrator workflow (all 5 agents)
- ✅ Detailed stage-by-stage results
- ✅ Beautiful formatted output
- ✅ Shows all statistics and metrics
- ✅ Lists generated files and reports

**Run it**:
```bash
python demo_orchestrator_v2.py
```

**Best for**: Understanding the complete workflow and seeing detailed results.

---

### 2. Quick Demo
**File**: `demo_quick.py`

**What it shows**: Minimal example of running the complete workflow.

**Features**:
- ✅ Simplified output
- ✅ Quick execution
- ✅ Essential information only
- ✅ Perfect for quick testing

**Run it**:
```bash
python demo_quick.py
```

**Best for**: Quick testing and understanding the basic API.

---

### 3. Individual Agents Demo
**File**: `demo_individual_agents.py`

**What it shows**: How to use each agent independently without orchestration.

**Features**:
- ✅ Shows all 5 agents separately
- ✅ Demonstrates agent-to-agent data flow
- ✅ Explains standalone usage
- ✅ Flexible workflow examples

**Run it**:
```bash
python demo_individual_agents.py
```

**Best for**: Understanding individual agent capabilities and flexible workflows.

---

## Prerequisites

### 1. Install Dependencies
```bash
pip install langgraph langchain-core langchain-openai pydantic-settings pydantic pytest
```

### 2. Set Environment Variables (if needed)
```bash
# For LLM-based features (Test Planner)
export OPENAI_API_KEY="your-api-key"
# or
set OPENAI_API_KEY=your-api-key  # Windows
```

### 3. Ensure Project Structure
Make sure you have the following directories:
- `generated_tests/` - Created automatically for test scripts
- `reports/` - Created automatically for test reports
- `logs/` - For application logs

---

## Demo Outputs

### What Each Demo Creates

#### Demo 1: Complete Orchestrator Workflow
**Output**:
```
reports/
├── report_20250113_120000.html      # Beautiful HTML report
├── report_20250113_120000.json      # JSON data
└── report_20250113_120000.md        # Markdown report

generated_tests/
├── test_login.py                    # Generated test scripts
├── test_checkout.py
└── ...
```

#### Demo 2: Quick Demo
**Output**: Same as Demo 1, but with minimal console output

#### Demo 3: Individual Agents
**Output**:
```
demo_tests/                          # Test scripts in custom directory
└── test_*.py

demo_reports/                        # Reports in custom directory
├── report_*.html
├── report_*.json
└── report_*.md
```

---

## Understanding the Output

### Console Output Sections

#### 1. Initialization
```
🤖 Initializing Orchestrator Agent V2
✅ Orchestrator initialized successfully
ℹ️  Sub-agents loaded: Discovery, Planner, Generator, Executor, Reporter
```

#### 2. Workflow Execution
```
⚙️  Running Complete Workflow
ℹ️  Starting workflow execution...
  1️⃣  Discovery Agent - Discover UI elements
  2️⃣  Test Planner Agent - Create test plan
  3️⃣  Test Generator Agent - Generate test scripts
  4️⃣  Test Executor Agent - Execute tests
  5️⃣  Reporting Agent - Generate reports
```

#### 3. Stage Results
```
▶ Stage-by-Stage Results
1️⃣  DISCOVERY AGENT
✅ Elements Found: 25
✅ Pages Found: 5

2️⃣  TEST PLANNER AGENT
✅ Test Cases Created: 12

3️⃣  TEST GENERATOR AGENT
✅ Scripts Generated: 12
✅ Passed Validation: 12

4️⃣  TEST EXECUTOR AGENT
✅ Total Tests Executed: 12
✅ Tests Passed: 10 ✅
❌ Tests Failed: 2 ❌
ℹ️  Pass Rate: 83.3%

5️⃣  REPORTING AGENT
✅ Reports Generated: 3
ℹ️  Formats: html, json, markdown
```

#### 4. Summary
```
✅ WORKFLOW COMPLETED SUCCESSFULLY! 🎉
  ✅ 5/5 stages completed
  ✅ Executed in 45.67 seconds
  ✅ 10 tests passed
  ✅ 3 reports generated
```

---

## Customizing the Demos

### Modify Application Profile

Edit the demo files to customize the application profile:

```python
app_profile = ApplicationProfile(
    name="Your App Name",
    base_url="https://your-app.com",
    app_type=ApplicationType.WEB,          # or API, DATABASE
    test_framework=TestFramework.PLAYWRIGHT,  # or SELENIUM, PYTEST, ROBOT
    adapter="web",                          # or "api", "database"
    description="Your app description",
    parallel_execution=True,                # Enable parallel execution
    max_workers=4,                          # Number of parallel workers
)
```

### Modify Feature Description

Change what gets tested:

```python
final_state = orchestrator.run_full_workflow(
    feature_description="""
    Your custom feature description:
    - Feature 1
    - Feature 2
    - Feature 3
    """,
)
```

### Change Output Directories

```python
orchestrator = OrchestratorAgentV2(
    app_profile=app_profile,
    output_dir="my_custom_tests",      # Custom test directory
    reports_dir="my_custom_reports",   # Custom report directory
    enable_hitl=False,
)
```

### Enable Human-in-the-Loop

```python
orchestrator = OrchestratorAgentV2(
    app_profile=app_profile,
    output_dir="generated_tests",
    reports_dir="reports",
    enable_hitl=True,  # Enable HITL approvals
)
```

---

## Troubleshooting

### Issue: Import Errors

**Problem**: `ModuleNotFoundError: No module named 'langgraph'`

**Solution**:
```bash
pip install langgraph langchain-core langchain-openai
```

### Issue: No Test Results

**Problem**: Tests execute but no results are captured

**Solution**: Check that:
1. Test scripts are in the correct format
2. Test framework (pytest/unittest) is installed
3. Scripts have correct file permissions

### Issue: LLM Errors in Planning

**Problem**: Test Planner fails with API errors

**Solution**:
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-key"

# Or use a different LLM in config/llm_config.py
```

### Issue: Reports Not Generated

**Problem**: Reporting stage completes but no files appear

**Solution**: Check:
1. Reports directory exists and is writable
2. Check `reports/` folder for files
3. Look for any error messages in the output

---

## Advanced Usage

### Run Individual Agents Programmatically

```python
from agents_v2 import DiscoveryAgentV2, TestPlannerAgentV2

# Just discovery
discovery_agent = DiscoveryAgentV2(app_profile=app_profile)
discovery_state = discovery_agent.discover(app_profile=app_profile)

# Discovery + Planning (no generation/execution)
planner = TestPlannerAgentV2(app_profile=app_profile)
planning_state = planner.create_plan(
    app_profile=app_profile,
    feature_description="Login flow",
    discovery_result=discovery_state["discovery_result"],
)

# Use the test cases however you want
test_cases = planning_state["test_cases"]
print(f"Created {len(test_cases)} test cases")
```

### Access State Data

```python
# After running orchestrator
final_state = orchestrator.run_full_workflow(...)

# Access sub-agent states
discovery_state = final_state.get('discovery_state', {})
planning_state = final_state.get('planning_state', {})
generation_state = final_state.get('generation_state', {})
execution_state = final_state.get('execution_state', {})

# Access specific data
elements = discovery_state.get('elements', [])
test_cases = planning_state.get('test_cases', [])
scripts = generation_state.get('generated_scripts', [])
results = execution_state.get('test_results', [])

# Access final report
final_report = final_state.get('final_report', {})
```

### Custom Workflows

```python
# Custom workflow: Skip discovery, start with existing data
orchestrator = OrchestratorAgentV2(app_profile=app_profile)

# Manually run specific stages
planning_state = orchestrator.test_planner.create_plan(
    app_profile=app_profile,
    feature_description="Login",
    discovery_result={},  # Empty discovery
)

generation_state = orchestrator.test_generator.generate_tests(
    test_cases=planning_state["test_cases"],
)

execution_state = orchestrator.test_executor.execute_tests(
    test_scripts=generation_state["generated_scripts"],
)

# Generate report manually
reporting_state = orchestrator.reporting_agent.generate_reports(
    test_results=execution_state["test_results"],
    app_name=app_profile.name,
    report_formats=["html"],
)
```

---

## Performance Tips

### Speed Up Testing

1. **Skip Discovery** if you already know the application structure
2. **Reuse Test Plans** instead of regenerating
3. **Enable Parallel Execution** for faster test execution
4. **Cache LLM Responses** to avoid redundant API calls

### Reduce Resource Usage

1. **Limit max_workers** for parallel execution
2. **Use pytest framework** (faster than others)
3. **Reduce timeout** for test execution
4. **Generate only needed report formats**

---

## Next Steps

After running the demos:

1. ✅ Read [COMPLETE_REFACTORING_SUMMARY.md](COMPLETE_REFACTORING_SUMMARY.md) for full documentation
2. ✅ Check [docs/ARCHITECTURE_V2.md](docs/ARCHITECTURE_V2.md) for architecture details
3. ✅ Review [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) to migrate your code
4. ✅ Explore individual tools in `tools/` directory
5. ✅ Run tests with `pytest tests/` to see comprehensive examples

---

## Support

For issues or questions:
- Check [COMPLETE_REFACTORING_SUMMARY.md](COMPLETE_REFACTORING_SUMMARY.md)
- Review test files in `tests/` for examples
- Examine tool implementations in `tools/`

---

**Happy Testing! 🧪✨**
