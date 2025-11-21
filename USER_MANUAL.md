# Agentic AI Regression Testing Framework
## User Manual

**Version:** 2.0
**Last Updated:** January 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Core Concepts](#core-concepts)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [Configuration Guide](#configuration-guide)
7. [Workflows and Use Cases](#workflows-and-use-cases)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)
11. [Appendices](#appendices)

---

## Introduction

### What is the Agentic AI Regression Testing Framework?

The Agentic AI Regression Testing Framework is an intelligent, AI-powered system that autonomously discovers, plans, generates, executes, and reports on regression test cases. Built on LangChain and LangGraph, it uses specialized AI agents to handle different aspects of the testing workflow.

### Key Benefits

- **Autonomous Testing**: AI agents work together to automate the entire testing lifecycle
- **Application-Agnostic**: Support for web apps, APIs, and enterprise applications
- **Human Oversight**: Flexible human-in-the-loop (HITL) modes for control and review
- **RAG-Powered**: Learns from historical tests and improves over time
- **CI/CD Ready**: Seamless integration with Azure DevOps, GitHub Actions, and Jenkins

### Who Should Use This?

- **QA Engineers**: Automate regression testing workflows
- **Test Automation Engineers**: Generate and maintain test scripts
- **DevOps Teams**: Integrate automated testing in CI/CD pipelines
- **Development Teams**: Ensure code quality with comprehensive test coverage

---

## Getting Started

### System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, Linux, or macOS
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Disk Space**: 2GB free space

### Installation

#### 1. Clone or Download the Repository

```bash
# If cloning from GitHub
git clone https://github.com/somenpatra-acn/agentic-regression-testing.git
cd agentic-regression-testing

# Or navigate to your existing directory
cd "C:\Projects\Regression Suite"
```

#### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Install Playwright browsers (for web testing)
playwright install
```

#### 4. Verify Installation

```bash
python main.py check
```

Expected output:
```
✓ Settings loaded
✓ LLM Connection: Working
✓ Configuration check complete
```

### Quick Setup (5 Minutes)

#### Step 1: Configure API Key

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` and add your API key:

```env
# Required: Choose one LLM provider
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4-turbo-preview

# HITL Configuration
HITL_MODE=APPROVE_PLAN

# Test Framework
TEST_FRAMEWORK=playwright
HEADLESS_MODE=true
```

#### Step 2: Run First Test

```bash
# List available applications
python main.py list-apps

# Run a simple test
python main.py run --app web_portal --feature "login functionality"
```

#### Step 3: Review Results

Tests, reports, and logs are saved in:
- **Generated Tests**: `generated_tests/`
- **Reports**: `reports/`
- **Logs**: `logs/regression_suite.log`

---

## Core Concepts

### Architecture Overview

The framework uses a **multi-agent architecture** where specialized AI agents collaborate:

```
User Request
     ↓
Orchestrator Agent (Coordinator)
     ↓
┌────────┬──────────┬───────────┬───────────┬──────────┐
│Discovery│  Test   │   Test    │   Test    │Reporting │
│  Agent │ Planner │ Generator │ Executor  │  Agent   │
└────────┴──────────┴───────────┴───────────┴──────────┘
     ↓
RAG Knowledge Base (Learning & Memory)
```

### The Six Agents

#### 1. Orchestrator Agent
**Role**: Coordinates all other agents and manages workflow

**Responsibilities**:
- Interprets user requests
- Invokes sub-agents in correct sequence
- Manages HITL approval workflows
- Aggregates results

**When to Use Directly**: Never - use it to run complete workflows

#### 2. Discovery Agent
**Role**: Discovers application structure and elements

**Responsibilities**:
- Crawls web applications (URLs, pages, forms)
- Discovers API endpoints (OpenAPI specs, REST APIs)
- Identifies UI elements (buttons, inputs, links)
- Maps application structure

**When to Use Directly**: When you only need discovery without testing

#### 3. Test Planner Agent
**Role**: Creates comprehensive test plans

**Responsibilities**:
- Analyzes discovery results
- Generates test case specifications
- Prioritizes test scenarios
- Creates test data requirements

**When to Use Directly**: When you want to review test plans before generation

#### 4. Test Generator Agent
**Role**: Generates executable test scripts

**Responsibilities**:
- Converts test cases to code
- Applies framework-specific templates (Playwright, Selenium, pytest)
- Validates generated scripts
- Adds proper assertions and error handling

**When to Use Directly**: When you have test cases and need scripts

#### 5. Test Executor Agent
**Role**: Executes test scripts and collects results

**Responsibilities**:
- Runs test scripts using appropriate framework
- Captures screenshots/videos on failure
- Collects execution metrics
- Handles parallel execution

**When to Use Directly**: When you have pre-written scripts to execute

#### 6. Reporting Agent
**Role**: Generates test reports

**Responsibilities**:
- Aggregates test results
- Creates reports (HTML, JSON, Markdown)
- Publishes to CI/CD platforms
- Generates analytics and trends

**When to Use Directly**: When you need to generate reports from existing results

### Human-in-the-Loop (HITL) Modes

HITL modes control when human approval is required:

| Mode | Description | Approval Points | Best For |
|------|-------------|-----------------|----------|
| **FULL_AUTO** | Fully automated | None | CI/CD pipelines, trusted workflows |
| **APPROVE_PLAN** | Approve test plans | After test planning | Reviewing test coverage |
| **APPROVE_TESTS** | Approve generated tests | After test generation | Reviewing test scripts |
| **APPROVE_ALL** | Approve everything | After each stage | Maximum control |
| **INTERACTIVE** | Interactive guidance | Continuous interaction | Exploratory testing, learning |

#### Setting HITL Mode

**Via CLI**:
```bash
python main.py run --app my_app --feature "login" --hitl-mode APPROVE_ALL
```

**Via Environment Variable**:
```env
HITL_MODE=APPROVE_PLAN
```

**Via Python Code**:
```python
orchestrator = OrchestratorAgent(app_profile, hitl_mode="INTERACTIVE")
```

### Application Adapters

Adapters provide application-specific logic for different types of applications:

#### Built-in Adapters

1. **Web Adapter** (`web_adapter`)
   - For web applications
   - Uses Playwright or Selenium
   - Supports SPA and traditional web apps

2. **API Adapter** (`api_adapter`)
   - For REST APIs
   - Supports OpenAPI/Swagger specs
   - Handles authentication (Bearer, Basic, OAuth)

3. **Oracle EBS Adapter** (`oracle_ebs_adapter`)
   - For Oracle E-Business Suite
   - Handles forms-based UI
   - Supports module-specific testing

4. **Custom Adapter** (`custom_adapter`)
   - Template for custom applications
   - Extend for your specific needs
   - Full control over discovery and execution

#### Creating Custom Adapters

See [Advanced Features](#creating-custom-adapters) section.

### RAG Knowledge Base

The framework uses **Retrieval-Augmented Generation (RAG)** to:

- **Store** historical test cases and results
- **Learn** from past test executions
- **Retrieve** similar test patterns
- **Ground** LLM outputs in real application data

**Benefits**:
- Improved test case quality
- Faster test generation
- Pattern recognition across applications
- Continuous learning

---

## Basic Usage

### Command Line Interface (CLI)

The primary way to interact with the framework is through the CLI.

#### General Syntax

```bash
python main.py [COMMAND] [OPTIONS]
```

#### Available Commands

##### 1. Check Configuration

Verify your setup is correct:

```bash
python main.py check
```

##### 2. List Application Profiles

View all configured applications:

```bash
python main.py list-apps
```

Output example:
```
Available application profiles:
  • web_portal      - Generic web portal application
  • oracle_ebs      - Oracle E-Business Suite
  • api_service     - RESTful API service
  • custom_app      - Custom application template
```

##### 3. Run Discovery

Discover application elements without running tests:

```bash
python main.py discover --app web_portal
```

Options:
- `--app`: Application profile name (required)
- `--hitl-mode`: HITL mode override (optional)

##### 4. Create Test Plan

Generate test plan without execution:

```bash
python main.py plan --app web_portal --feature "user login"
```

Options:
- `--app`: Application profile name (required)
- `--feature`: Feature description (required)
- `--hitl-mode`: HITL mode (default: APPROVE_PLAN)

##### 5. Run Complete Workflow

Execute the full testing workflow:

```bash
python main.py run --app web_portal --feature "login functionality"
```

Options:
- `--app`: Application profile name (required)
- `--feature`: Feature description to test (required)
- `--hitl-mode`: HITL mode override (optional)
- `--output`: Output directory for reports (default: reports)

**Examples**:

```bash
# Fully automated testing
python main.py run --app api_service --feature "user authentication API" --hitl-mode FULL_AUTO

# With approval for test plans
python main.py run --app web_portal --feature "checkout process" --hitl-mode APPROVE_PLAN

# Interactive mode
python main.py run --app oracle_ebs --feature "GL journal entry" --hitl-mode INTERACTIVE
```

### Python API

Use the framework programmatically in your Python scripts.

#### Basic Workflow

```python
from models.app_profile import ApplicationProfile, ApplicationType, TestFramework
from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2

# 1. Define application profile
app_profile = ApplicationProfile(
    name="my_app",
    app_type=ApplicationType.WEB,
    adapter="web",
    base_url="https://myapp.com",
    test_framework=TestFramework.PLAYWRIGHT,
    headless=True
)

# 2. Create orchestrator
orchestrator = OrchestratorAgentV2(
    app_profile=app_profile,
    output_dir="generated_tests",
    reports_dir="reports",
    enable_hitl=False  # FULL_AUTO mode
)

# 3. Run workflow
final_state = orchestrator.run_full_workflow(
    feature_description="Test user login and authentication"
)

# 4. Check results
if final_state.get("success"):
    print("✓ Workflow completed successfully!")
    print(f"Test results: {final_state.get('execution_state', {})}")
else:
    print("✗ Workflow failed")
    print(f"Error: {final_state.get('error')}")
```

#### Using Individual Agents

```python
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from agents_v2.test_planner_agent_v2 import TestPlannerAgentV2

# Discovery only
discovery_agent = DiscoveryAgentV2(app_profile=app_profile)
discovery_state = discovery_agent.discover(
    app_profile=app_profile,
    max_depth=3,
    max_pages=50
)

elements = discovery_state["elements"]
pages = discovery_state["pages"]

print(f"Discovered {len(elements)} elements across {len(pages)} pages")

# Test planning only
planner = TestPlannerAgentV2(app_profile=app_profile)
planning_state = planner.create_plan(
    app_profile=app_profile,
    feature_description="User login",
    discovery_result=discovery_state["discovery_result"]
)

test_cases = planning_state["test_cases"]
print(f"Created {len(test_cases)} test cases")
```

#### Working with Test Results

```python
# Access execution results
execution_state = final_state.get("execution_state", {})
test_results = execution_state.get("test_results", [])

# Analyze results
passed = sum(1 for r in test_results if r.status == "PASSED")
failed = sum(1 for r in test_results if r.status == "FAILED")
total = len(test_results)

print(f"Pass rate: {(passed/total)*100:.1f}%")
print(f"Passed: {passed}, Failed: {failed}, Total: {total}")

# Access individual test results
for result in test_results:
    print(f"{result.test_id}: {result.status}")
    if result.status == "FAILED":
        print(f"  Error: {result.error_message}")
        print(f"  Screenshot: {result.screenshot_path}")
```

### Demo Scripts

Three demo scripts are provided to help you learn:

#### 1. Complete Orchestrator Demo

```bash
python demo_orchestrator_v2.py
```

Shows complete workflow with detailed output.

#### 2. Quick Demo

```bash
python demo_quick.py
```

Minimal example with essential output.

#### 3. Individual Agents Demo

```bash
python demo_individual_agents.py
```

Demonstrates using agents independently.

See [DEMO_GUIDE.md](DEMO_GUIDE.md) for details.

---

## Advanced Features

### Creating Custom Adapters

Custom adapters allow you to support any application type.

#### Step 1: Create Adapter Class

```python
from adapters.base_adapter import BaseApplicationAdapter
from models.test_case import TestCase
from models.test_result import TestResult, TestStatus

class MyAppAdapter(BaseApplicationAdapter):
    """Custom adapter for my specific application."""

    def __init__(self, app_profile):
        super().__init__(app_profile)
        # Initialize your resources
        self.connection = None

    def discover_elements(self):
        """
        Discover application elements.

        Returns:
            dict: Discovery results with 'elements' and 'pages'
        """
        elements = []
        pages = []

        # Your discovery logic here
        # Example: Connect to app and find elements

        return {
            "elements": elements,
            "pages": pages,
            "metadata": {"discovered_at": "2025-01-13"}
        }

    def execute_test(self, test_case: TestCase) -> TestResult:
        """
        Execute a single test case.

        Args:
            test_case: Test case to execute

        Returns:
            TestResult with execution details
        """
        try:
            # Your test execution logic
            # Example: Run the test steps

            return TestResult(
                test_id=test_case.test_id,
                test_name=test_case.name,
                status=TestStatus.PASSED,
                duration=1.234,
                message="Test passed successfully"
            )

        except Exception as e:
            return TestResult(
                test_id=test_case.test_id,
                test_name=test_case.name,
                status=TestStatus.FAILED,
                duration=0.5,
                error_message=str(e),
                screenshot_path=self._capture_screenshot()
            )

    def validate_state(self) -> bool:
        """Check if application is ready for testing."""
        # Verify app is accessible
        return True

    def cleanup(self):
        """Clean up resources."""
        if self.connection:
            self.connection.close()
```

#### Step 2: Register Adapter

```python
from adapters import register_adapter

register_adapter("my_app_adapter", MyAppAdapter)
```

#### Step 3: Configure Application Profile

In `config/app_profiles.yaml`:

```yaml
my_custom_app:
  name: "my_custom_app"
  app_type: "custom"
  adapter: "my_app_adapter"  # Your adapter name
  base_url: "https://myapp.com"

  # Custom configuration
  custom_config:
    connection_timeout: 30
    custom_param: "value"
```

#### Step 4: Use the Adapter

```bash
python main.py run --app my_custom_app --feature "my feature"
```

### Using the RAG Knowledge Base

#### Adding Test Cases

```python
from rag.retriever import TestKnowledgeRetriever

retriever = TestKnowledgeRetriever()

# Add test cases to knowledge base
retriever.add_test_cases(test_cases)

# Add test execution results
for result in test_results:
    retriever.add_test_result(result)
```

#### Searching for Similar Tests

```python
# Find similar test cases
similar_tests = retriever.find_similar_tests(
    query="login test with authentication",
    k=5,  # Top 5 results
    application="my_app"  # Filter by application
)

for test in similar_tests:
    print(f"Test: {test.name}")
    print(f"Similarity: {test.score:.2f}")
```

#### Configuring Vector Store

In `.env`:

```env
# Choose vector store: faiss or chroma
VECTOR_STORE=faiss

# Embedding model
EMBEDDING_MODEL=text-embedding-3-small
```

### Web UI for HITL

A modern web interface for human-in-the-loop operations.

#### Starting the Web UI

```bash
# Default (localhost:5000)
python web_ui/app.py

# Custom host/port
WEB_UI_HOST=0.0.0.0 WEB_UI_PORT=8080 python web_ui/app.py
```

Access at: `http://localhost:5000`

#### Features

1. **Dashboard**: Real-time workflow statistics
2. **Approval Management**: Review and approve/reject items
3. **Workflow Monitor**: Live progress tracking
4. **Chat Interface**: Natural language interaction
5. **Feedback System**: Submit feedback on tests
6. **WebSocket Updates**: Real-time notifications

#### Using Web UI with Orchestrator

```python
from hitl.review_interface import WebReviewer
from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2

# Initialize with web reviewer
orchestrator = OrchestratorAgentV2(
    app_profile,
    enable_hitl=True
)

# Set up web reviewer (runs in background)
web_reviewer = WebReviewer(port=5000)
orchestrator.set_reviewer(web_reviewer)

# Run workflow - approvals show in web UI
result = orchestrator.run_full_workflow("Login feature")
```

### CI/CD Integration

#### Azure DevOps

In `.env`:
```env
AZURE_DEVOPS_ORG=your_org
AZURE_DEVOPS_PROJECT=your_project
AZURE_DEVOPS_PAT=your_pat_token
```

In pipeline YAML:
```yaml
- task: PythonScript@0
  displayName: 'Run Regression Tests'
  inputs:
    scriptSource: 'inline'
    script: |
      python main.py run --app web_portal --feature "all features" --hitl-mode FULL_AUTO
```

#### GitHub Actions

Create `.github/workflows/regression-tests.yml`:

```yaml
name: Regression Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        playwright install

    - name: Run tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python main.py run --app web_portal --feature "all features" --hitl-mode FULL_AUTO

    - name: Upload reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-reports
        path: reports/
```

#### Jenkins

```groovy
pipeline {
    agent any

    environment {
        OPENAI_API_KEY = credentials('openai-api-key')
    }

    stages {
        stage('Setup') {
            steps {
                sh 'python -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                sh '. venv/bin/activate && python main.py run --app web_portal --feature "all" --hitl-mode FULL_AUTO'
            }
        }

        stage('Publish') {
            steps {
                publishHTML([
                    reportDir: 'reports',
                    reportFiles: '*.html',
                    reportName: 'Test Report'
                ])
            }
        }
    }
}
```

### Parallel Execution

Enable parallel test execution for faster results:

```python
app_profile = ApplicationProfile(
    name="my_app",
    # ... other config
    parallel_execution=True,
    max_workers=4  # Number of parallel workers
)
```

Or in `app_profiles.yaml`:

```yaml
my_app:
  parallel_execution: true
  max_workers: 4
```

---

## Configuration Guide

### Environment Variables

Complete list of environment variables in `.env`:

#### LLM Configuration

```env
# API Keys (choose one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Provider settings
LLM_PROVIDER=openai  # openai, anthropic
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.1  # 0.0-1.0, lower = more deterministic
```

#### Vector Store

```env
VECTOR_STORE=faiss  # faiss or chroma
EMBEDDING_MODEL=text-embedding-3-small
```

#### Application Settings

```env
APP_URL=https://your-app.example.com
APP_AUTH_TYPE=basic  # basic, oauth2, bearer, custom
APP_USERNAME=test_user
APP_PASSWORD=test_password
```

#### HITL Configuration

```env
HITL_MODE=APPROVE_PLAN  # FULL_AUTO, APPROVE_PLAN, APPROVE_TESTS, APPROVE_ALL, INTERACTIVE
APPROVAL_TIMEOUT=3600  # Timeout in seconds
ENABLE_WEB_INTERFACE=true
```

#### Web UI

```env
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
FLASK_DEBUG=false
SECRET_KEY=your-secret-key-here
```

#### Test Execution

```env
TEST_FRAMEWORK=playwright  # selenium, playwright, pytest, robot
PARALLEL_EXECUTION=true
MAX_WORKERS=4
HEADLESS_MODE=true
SCREENSHOT_ON_FAILURE=true
```

#### Logging

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/regression_suite.log
```

#### CI/CD Integration

```env
# Azure DevOps
AZURE_DEVOPS_ORG=your_org
AZURE_DEVOPS_PROJECT=your_project
AZURE_DEVOPS_PAT=your_pat

# GitHub
GITHUB_TOKEN=your_token
GITHUB_REPO=owner/repo
```

### Application Profiles

Application profiles are defined in `config/app_profiles.yaml`.

#### Profile Structure

```yaml
my_app:
  # Basic Information
  name: "my_app"
  app_type: "web"  # web, api, enterprise, database, custom
  adapter: "web_adapter"  # Adapter to use
  base_url: "https://myapp.com"
  description: "My web application"

  # Authentication
  auth:
    auth_type: "basic"  # basic, bearer, oauth2, custom
    username: "${APP_USERNAME}"  # Environment variable reference
    password: "${APP_PASSWORD}"
    # For bearer tokens:
    # token: "${API_TOKEN}"
    # For OAuth2:
    # oauth_config:
    #   client_id: "${OAUTH_CLIENT_ID}"
    #   client_secret: "${OAUTH_CLIENT_SECRET}"
    #   auth_url: "https://auth.example.com/token"

  # Discovery Settings
  discovery:
    enabled: true
    max_depth: 3  # How deep to crawl
    max_pages: 50  # Maximum pages to discover
    exclude_patterns:  # URL patterns to skip
      - "/logout"
      - "/admin"
    include_patterns:  # Only these patterns (optional)
      - "/app/*"

  # Test Framework
  test_framework: "playwright"  # selenium, playwright, pytest, robot

  # Execution Settings
  parallel_execution: true
  max_workers: 4
  headless: true

  # Application Modules
  modules:
    - "authentication"
    - "dashboard"
    - "reports"

  # Custom Configuration
  custom_config:
    wait_timeout: 30
    screenshot_dir: "screenshots/my_app"
    custom_setting: "value"
```

#### Environment Variable References

Use `${VAR_NAME}` to reference environment variables:

```yaml
auth:
  username: "${APP_USERNAME}"
  token: "${API_TOKEN}"
```

#### Multiple Profiles

Define multiple applications:

```yaml
applications:
  app1:
    name: "app1"
    # ... config

  app2:
    name: "app2"
    # ... config

  app3:
    name: "app3"
    # ... config

# Set default
default_profile: "app1"
```

#### Global Settings

Apply settings to all profiles:

```yaml
global_settings:
  screenshot_on_failure: true
  video_on_failure: false
  retry_failed_tests: 1
  test_timeout: 300
  browser_options:
    - "--no-sandbox"
    - "--disable-dev-shm-usage"
```

---

## Workflows and Use Cases

### Use Case 1: Web Application Testing

**Scenario**: Test a web application's user registration flow.

```bash
# Step 1: Configure application
# Edit config/app_profiles.yaml

python main.py run \
  --app my_web_app \
  --feature "User registration: signup form, email verification, profile creation" \
  --hitl-mode APPROVE_PLAN
```

**What happens**:
1. Discovery crawls the application
2. Test planner creates test scenarios
3. You approve the test plan
4. Tests are generated and executed
5. HTML report is created

### Use Case 2: API Testing

**Scenario**: Test REST API endpoints.

```python
from models.app_profile import ApplicationProfile, ApplicationType, AuthConfig

# Define API profile
api_profile = ApplicationProfile(
    name="my_api",
    app_type=ApplicationType.API,
    adapter="api_adapter",
    base_url="https://api.myapp.com/v1",
    auth=AuthConfig(
        auth_type="bearer",
        token="your_api_token"
    ),
    test_framework=TestFramework.PYTEST
)

# Run tests
orchestrator = OrchestratorAgentV2(api_profile, enable_hitl=False)
result = orchestrator.run_full_workflow(
    "Test all CRUD operations for users endpoint"
)
```

### Use Case 3: Oracle EBS Module Testing

**Scenario**: Test Oracle EBS General Ledger module.

```yaml
# config/app_profiles.yaml
oracle_gl:
  name: "oracle_gl"
  app_type: "enterprise"
  adapter: "oracle_ebs_adapter"
  base_url: "https://ebs.company.com:8000"

  auth:
    auth_type: "custom"
    username: "${ORACLE_USER}"
    password: "${ORACLE_PASSWORD}"

  modules: ["GL"]

  custom_config:
    responsibility: "General Ledger Manager"
    wait_for_forms: true
```

```bash
python main.py run --app oracle_gl --feature "GL journal entry workflow"
```

### Use Case 4: CI/CD Integration

**Scenario**: Run tests in GitHub Actions on every commit.

See [CI/CD Integration](#cicd-integration) section.

### Use Case 5: Exploratory Testing

**Scenario**: Interactively explore and test an application.

```bash
python main.py run \
  --app my_app \
  --feature "Explore checkout process" \
  --hitl-mode INTERACTIVE
```

In INTERACTIVE mode:
- Agent suggests test scenarios
- You provide guidance and feedback
- Tests are refined based on your input
- Flexible, conversational approach

### Use Case 6: Regression Suite Maintenance

**Scenario**: Update regression suite when application changes.

```python
# 1. Rediscover application
discovery_agent.discover(app_profile=app_profile)

# 2. Generate new tests based on changes
orchestrator.run_full_workflow("Retest modified features")

# 3. Update knowledge base
retriever.add_test_cases(new_test_cases)
retriever.add_test_result(results)
```

---

## Troubleshooting

### Installation Issues

#### Issue: "Python version too old"

**Solution**: Upgrade to Python 3.10+:

```bash
# Windows
# Download from python.org

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3.10 python3.10-venv

# Mac
brew install python@3.10
```

#### Issue: "pip install fails"

**Solution**:
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Use --user flag
pip install --user -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

#### Issue: "Playwright installation fails"

**Solution**:
```bash
# Install Playwright separately
pip install playwright
playwright install chromium

# If permission issues (Linux)
sudo playwright install-deps
playwright install
```

### Configuration Issues

#### Issue: "OpenAI API key not found"

**Solution**:
1. Check `.env` file exists
2. Verify `OPENAI_API_KEY` is set correctly
3. No spaces around `=`
4. No quotes needed around key

```env
# Correct
OPENAI_API_KEY=sk-your-key-here

# Incorrect
OPENAI_API_KEY = "sk-your-key-here"
```

#### Issue: "Application profile not found"

**Solution**:
```bash
# List available profiles
python main.py list-apps

# Check config file exists
ls config/app_profiles.yaml

# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('config/app_profiles.yaml'))"
```

#### Issue: "LLM connection fails"

**Solution**:
1. Check API key is valid
2. Verify internet connection
3. Check LLM provider status
4. Try different model:

```env
# For OpenAI
LLM_MODEL=gpt-3.5-turbo  # Cheaper, faster

# For Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
```

### Execution Issues

#### Issue: "Tests fail with timeout"

**Solution**:
```yaml
# Increase timeouts in app profile
custom_config:
  wait_timeout: 60
  page_load_timeout: 90
```

Or in `.env`:
```env
TEST_TIMEOUT=600
```

#### Issue: "Browser crashes"

**Solution**:
```yaml
# Reduce parallel execution
parallel_execution: true
max_workers: 2  # Reduce from 4 to 2

# Use headless mode
headless: true

# Add browser options
custom_config:
  browser_options:
    - "--no-sandbox"
    - "--disable-dev-shm-usage"
    - "--disable-gpu"
```

#### Issue: "Tests pass locally but fail in CI"

**Solution**:
```bash
# Install system dependencies (CI)
sudo apt-get update
sudo apt-get install -y \
  libnss3 \
  libatk-bridge2.0-0 \
  libdrm2 \
  libxkbcommon0 \
  libgbm1

# Use headless mode in CI
HEADLESS_MODE=true python main.py run ...
```

#### Issue: "Import errors"

**Solution**:
```bash
# Verify virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Report Generation Issues

#### Issue: "Reports not generated"

**Solution**:
1. Check reports directory exists and is writable:
```bash
mkdir -p reports
chmod 755 reports
```

2. Check disk space:
```bash
df -h .
```

3. Check logs:
```bash
tail -f logs/regression_suite.log
```

#### Issue: "HTML report is blank"

**Solution**:
- Ensure test results were captured
- Check for JavaScript errors (open browser console)
- Regenerate report:

```python
from agents_v2.reporting_agent_v2 import ReportingAgentV2

reporting_agent = ReportingAgentV2(app_profile)
report_path = reporting_agent.generate_report(
    test_results=results,
    format="html"
)
```

### Performance Issues

#### Issue: "Tests run very slowly"

**Solutions**:

1. **Enable parallel execution**:
```yaml
parallel_execution: true
max_workers: 4
```

2. **Use faster test framework**:
```yaml
test_framework: "pytest"  # Faster than Selenium
```

3. **Reduce discovery scope**:
```yaml
discovery:
  max_depth: 2  # Reduce from 3
  max_pages: 25  # Reduce from 50
```

4. **Use headless mode**:
```yaml
headless: true
```

5. **Skip unnecessary stages**:
```python
# Skip discovery if elements are known
orchestrator.run_workflow_from_planning(
    feature_description="Login test"
)
```

#### Issue: "High memory usage"

**Solutions**:

1. Reduce parallel workers:
```yaml
max_workers: 2
```

2. Close browser after each test:
```python
custom_config:
  reuse_browser: false
```

3. Clean up resources:
```python
orchestrator.cleanup()
```

---

## Best Practices

### Test Design

1. **Write Clear Feature Descriptions**

Good:
```python
feature_description = """
Test user login workflow:
- Valid credentials should authenticate successfully
- Invalid credentials should show error message
- Password reset link should be functional
- Remember me checkbox should persist session
"""
```

Poor:
```python
feature_description = "test login"
```

2. **Use Appropriate HITL Modes**

- Use `FULL_AUTO` in CI/CD pipelines
- Use `APPROVE_PLAN` for new features
- Use `INTERACTIVE` for exploratory testing

3. **Organize Test Outputs**

```python
# Use descriptive output directories
orchestrator = OrchestratorAgentV2(
    app_profile=app_profile,
    output_dir=f"tests/{app_name}/{feature_name}",
    reports_dir=f"reports/{app_name}/{timestamp}"
)
```

### Configuration Management

1. **Use Environment Variables for Secrets**

Never hardcode credentials:

```yaml
# Good
auth:
  username: "${APP_USERNAME}"
  password: "${APP_PASSWORD}"

# Bad
auth:
  username: "admin"
  password: "password123"
```

2. **Separate Profiles per Environment**

```yaml
my_app_dev:
  base_url: "https://dev.myapp.com"

my_app_staging:
  base_url: "https://staging.myapp.com"

my_app_prod:
  base_url: "https://myapp.com"
```

3. **Version Control Configuration**

- Commit `.env.example`, not `.env`
- Commit `app_profiles.yaml`
- Use `.gitignore` for sensitive files

### Performance Optimization

1. **Cache Discovery Results**

```python
# Save discovery results
import json

discovery_state = discovery_agent.discover(...)
with open("discovery_cache.json", "w") as f:
    json.dump(discovery_state, f)

# Reuse later
with open("discovery_cache.json") as f:
    cached_discovery = json.load(f)
```

2. **Reuse Test Plans**

```python
# Generate plan once
planning_state = planner.create_plan(...)

# Use for multiple test generations
for variant in variants:
    generation_state = generator.generate_tests(
        test_cases=planning_state["test_cases"],
        variant=variant
    )
```

3. **Parallel Execution**

```yaml
parallel_execution: true
max_workers: 4  # Adjust based on system resources
```

### Maintenance

1. **Regular Knowledge Base Updates**

```python
# After each test run
retriever.add_test_result(result)
retriever.add_feedback_documents(feedback)
```

2. **Monitor Logs**

```bash
# Watch logs in real-time
tail -f logs/regression_suite.log

# Search for errors
grep ERROR logs/regression_suite.log
```

3. **Clean Up Old Reports**

```bash
# Keep last 30 days of reports
find reports/ -name "*.html" -mtime +30 -delete
```

### Security

1. **Secure API Keys**

- Use environment variables
- Rotate keys regularly
- Use different keys for dev/prod
- Never commit keys to version control

2. **Sanitize Test Data**

```python
# Don't use production data in tests
# Use faker for generating test data
from faker import Faker

fake = Faker()
test_user = fake.email()
test_password = fake.password()
```

3. **Limit Permissions**

- Use read-only accounts for discovery
- Use test accounts for execution
- Avoid admin/privileged accounts

---

## FAQ

### General Questions

**Q: What LLM providers are supported?**

A: OpenAI (GPT-4, GPT-3.5) and Anthropic (Claude). Configure in `.env`:
```env
LLM_PROVIDER=openai  # or anthropic
```

**Q: Can I use local LLMs?**

A: Not directly supported yet, but you can extend `config/llm_config.py` to add support for local models via LangChain's integration.

**Q: Is this framework language-specific?**

A: Generated tests are in Python (using pytest/Playwright/Selenium), but the framework can test applications in any language.

**Q: Does it work with mobile apps?**

A: Not currently. It's designed for web apps, APIs, and enterprise applications. Mobile support (Appium) is on the roadmap.

### Technical Questions

**Q: How does the AI generate test cases?**

A: The Test Planner Agent uses LLMs to analyze application structure (from discovery) and generate comprehensive test scenarios based on best practices.

**Q: Can I modify generated test scripts?**

A: Yes! Generated scripts are standard Python/pytest files. Edit them as needed and run manually or integrate into existing test suites.

**Q: How accurate is the test generation?**

A: Accuracy depends on:
- Quality of discovery results
- Clarity of feature descriptions
- LLM model quality (GPT-4 > GPT-3.5)
- Historical test data in RAG

Typical accuracy: 80-95% for well-defined features.

**Q: Can I use my existing test scripts?**

A: Yes! Use the Test Executor Agent directly:

```python
executor = TestExecutorAgentV2(app_profile)
results = executor.execute_tests(
    test_scripts=your_existing_scripts
)
```

**Q: How does RAG improve test generation?**

A: RAG stores historical tests and retrieves similar patterns when generating new tests. Over time, this improves quality and reduces generation time.

### Troubleshooting Questions

**Q: Tests work locally but fail in CI. Why?**

A: Common causes:
- Missing system dependencies (browsers, libraries)
- Different environment variables
- Network/firewall restrictions
- Headless mode issues

Solution: Use Docker for consistent environments.

**Q: How do I debug test failures?**

A:
1. Check screenshots: `reports/screenshots/`
2. Review logs: `logs/regression_suite.log`
3. Run with more verbose logging:
```env
LOG_LEVEL=DEBUG
```
4. Run single test manually:
```bash
pytest generated_tests/test_login.py -v -s
```

**Q: Why is discovery slow?**

A: Large applications take time. Speed up by:
- Reducing `max_depth` and `max_pages`
- Using `exclude_patterns` to skip irrelevant sections
- Caching discovery results

### Pricing Questions

**Q: How much does it cost to run?**

A: Costs are primarily from LLM API calls:
- Discovery: ~$0.01-0.05 per page
- Planning: ~$0.10-0.50 per feature
- Generation: ~$0.05-0.20 per test

Example: Testing a 10-page app with 20 tests ≈ $1-3 total.

Use cheaper models for lower costs:
```env
LLM_MODEL=gpt-3.5-turbo  # ~10x cheaper than GPT-4
```

**Q: Can I run without API costs?**

A: No, an LLM is required for intelligent test generation. However, you can:
- Use agents selectively (e.g., skip planning if you have test cases)
- Cache LLM responses
- Use cheaper models

---

## Appendices

### Appendix A: Complete Configuration Reference

See [Configuration Guide](#configuration-guide) for detailed explanations.

**Environment Variables**:
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `LLM_PROVIDER` - LLM provider (openai, anthropic)
- `LLM_MODEL` - Model name
- `LLM_TEMPERATURE` - Temperature (0.0-1.0)
- `VECTOR_STORE` - Vector store (faiss, chroma)
- `EMBEDDING_MODEL` - Embedding model
- `HITL_MODE` - HITL mode
- `TEST_FRAMEWORK` - Test framework
- `PARALLEL_EXECUTION` - Enable parallel execution (true/false)
- `MAX_WORKERS` - Number of parallel workers
- `HEADLESS_MODE` - Headless browser mode (true/false)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Appendix B: Application Profile Schema

```yaml
app_name:
  name: string (required)
  app_type: string (web|api|enterprise|database|custom)
  adapter: string (required)
  base_url: string (required)
  description: string

  auth:
    auth_type: string (basic|bearer|oauth2|custom)
    username: string
    password: string
    token: string
    custom_headers: dict
    oauth_config: dict

  discovery:
    enabled: boolean
    max_depth: integer
    max_pages: integer
    exclude_patterns: list
    include_patterns: list

  test_framework: string (playwright|selenium|pytest|robot)
  parallel_execution: boolean
  max_workers: integer
  headless: boolean

  modules: list
  features: list

  custom_config: dict
```

### Appendix C: Test Result Schema

```python
{
    "test_id": "TEST-001",
    "test_name": "test_login_valid_credentials",
    "status": "PASSED",  # PASSED, FAILED, SKIPPED
    "duration": 2.5,  # seconds
    "message": "Test passed successfully",
    "error_message": None,  # if failed
    "screenshot_path": "screenshots/test_001.png",
    "video_path": "videos/test_001.mp4",
    "started_at": "2025-01-13T10:00:00",
    "completed_at": "2025-01-13T10:00:02",
    "metadata": {
        "browser": "chromium",
        "viewport": "1920x1080"
    }
}
```

### Appendix D: CLI Command Reference

```bash
# Configuration
python main.py check                           # Verify configuration
python main.py list-apps                       # List application profiles

# Testing
python main.py discover --app APP_NAME         # Discovery only
python main.py plan --app APP --feature FEAT   # Planning only
python main.py run --app APP --feature FEAT    # Full workflow

# Options
--app APP_NAME                                 # Application profile
--feature "DESCRIPTION"                        # Feature description
--hitl-mode MODE                               # HITL mode
--output DIR                                   # Output directory

# Examples
python main.py run --app web_portal --feature "login" --hitl-mode FULL_AUTO
python main.py discover --app api_service
python main.py plan --app oracle_ebs --feature "GL journals"
```

### Appendix E: Python API Reference

#### OrchestratorAgentV2

```python
from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2

orchestrator = OrchestratorAgentV2(
    app_profile: ApplicationProfile,
    output_dir: str = "generated_tests",
    reports_dir: str = "reports",
    enable_hitl: bool = False
)

# Run complete workflow
final_state = orchestrator.run_full_workflow(
    feature_description: str
) -> dict

# Run individual stages
discovery_state = orchestrator.run_discovery()
planning_state = orchestrator.run_planning(feature_description)
generation_state = orchestrator.run_generation()
execution_state = orchestrator.run_execution()
reporting_state = orchestrator.run_reporting()
```

#### Individual Agents

```python
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from agents_v2.test_planner_agent_v2 import TestPlannerAgentV2
from agents_v2.test_generator_agent_v2 import TestGeneratorAgentV2
from agents_v2.test_executor_agent_v2 import TestExecutorAgentV2
from agents_v2.reporting_agent_v2 import ReportingAgentV2

# Discovery
discovery_agent = DiscoveryAgentV2(app_profile)
discovery_state = discovery_agent.discover(app_profile, max_depth, max_pages)

# Planning
planner = TestPlannerAgentV2(app_profile)
planning_state = planner.create_plan(app_profile, feature_description, discovery_result)

# Generation
generator = TestGeneratorAgentV2(app_profile)
generation_state = generator.generate_tests(test_cases, output_dir)

# Execution
executor = TestExecutorAgentV2(app_profile)
execution_state = executor.execute_tests(test_scripts)

# Reporting
reporter = ReportingAgentV2(app_profile)
reporting_state = reporter.generate_reports(test_results, report_formats)
```

### Appendix F: Glossary

- **Agent**: Specialized AI component responsible for specific task (discovery, planning, etc.)
- **Adapter**: Application-specific connector that handles discovery and test execution
- **Application Profile**: Configuration defining an application's properties and test settings
- **Discovery**: Process of exploring an application to identify testable elements
- **HITL**: Human-in-the-Loop - modes controlling when human approval is required
- **LangChain**: Framework for building LLM-powered applications
- **LangGraph**: State machine framework for multi-agent workflows
- **LLM**: Large Language Model (GPT-4, Claude, etc.)
- **Orchestrator**: Main coordinator agent that manages workflow
- **RAG**: Retrieval-Augmented Generation - technique for grounding LLM outputs
- **Test Case**: Specification of what to test (input, steps, expected output)
- **Test Script**: Executable code that performs a test
- **Vector Store**: Database for storing and retrieving embeddings (FAISS, Chroma)

### Appendix G: Additional Resources

- **README.md**: Quick overview and installation
- **QUICKSTART.md**: 5-minute quick start guide
- **DEMO_GUIDE.md**: Demo scripts documentation
- **CLAUDE.md**: Developer guidance for Claude Code
- **docs/ARCHITECTURE_V2.md**: Technical architecture details
- **docs/MIGRATION_GUIDE.md**: Migration from V1 to V2
- **examples/**: Example scripts and use cases

### Appendix H: Support and Community

- **GitHub Repository**: https://github.com/somenpatra-acn/agentic-regression-testing
- **Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Documentation**: Complete docs in `/docs` folder

---

## Conclusion

This user manual covers the essential aspects of the Agentic AI Regression Testing Framework. For more detailed technical information, refer to the architecture documentation and API references.

### Quick Reference Card

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with API key

# Run tests
python main.py run --app APP_NAME --feature "FEATURE DESCRIPTION"

# Get help
python main.py --help
python main.py COMMAND --help
```

### Next Steps

1. Complete the [Getting Started](#getting-started) section
2. Run the demo scripts to understand the workflow
3. Configure your first application profile
4. Run your first test
5. Explore advanced features as needed

**Happy Testing!** 🧪✨

---

*For the latest updates and information, visit the [GitHub repository](https://github.com/somenpatra-acn/agentic-regression-testing).*
