# Agentic AI Regression Testing Framework

> **An intelligent, agentic AI-powered regression testing framework built with LangChain that autonomously discovers, plans, generates, executes, and reports on test cases with human-in-the-loop oversight.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Key Features

### Intelligent Agentic Architecture
- **6 Specialized AI Agents**: Orchestrator, Discovery, Test Planner, Test Generator, Test Executor, and Reporting
- **LangChain Integration**: Built on LangChain's agent framework for reliable LLM orchestration
- **RAG-Powered**: Uses Retrieval-Augmented Generation with FAISS/Chroma for grounded test generation

### Human-in-the-Loop (HITL)
- **5 HITL Modes**: FULL_AUTO, APPROVE_PLAN, APPROVE_TESTS, APPROVE_ALL, INTERACTIVE
- **Web UI Interface**: Modern web-based interface for approvals and monitoring
- **Approval Workflows**: Human review and approval at critical decision points
- **Feedback Collection**: Capture human feedback on test failures and generated tests
- **Interactive Planning**: Collaborate with AI agents to refine test plans
- **Real-time Monitoring**: WebSocket-powered live updates and notifications

### Application-Agnostic Design
- **Adapter Pattern**: Easily extend to any application type
- **Built-in Adapters**: Web (Playwright), API (REST/OpenAPI), Oracle EBS
- **Custom Adapter Template**: Create adapters for your specific applications
- **Plugin System**: Register custom adapters dynamically

### Multi-Framework Support
- **Web Testing**: Selenium, Playwright
- **API Testing**: pytest, requests
- **Enterprise Apps**: Oracle EBS, custom enterprise applications
- **Extensible**: Add support for any testing framework

### CI/CD Ready
- **Azure DevOps Integration**: Publish results to Azure Pipelines
- **GitHub Actions**: Integrate with GitHub workflows
- **Jenkins Support**: Compatible with Jenkins pipelines
- **Multiple Report Formats**: HTML, JSON, Markdown

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User / CI/CD Trigger                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator Agent                          │
│  • Interprets requests                                       │
│  • Coordinates sub-agents                                    │
│  • Manages HITL workflows                                    │
└───┬─────────┬──────────┬──────────┬──────────┬─────────────┘
    │         │          │          │          │
    ▼         ▼          ▼          ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│Discovery│ │Test  │ │Test    │ │Test    │ │Reporting │
│Agent   │ │Planner│ │Generator│ │Executor│ │Agent     │
└────────┘ └──────┘ └────────┘ └────────┘ └──────────┘
    │         │          │          │          │
    └─────────┴──────────┴──────────┴──────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  RAG Knowledge Base  │
              │  (FAISS/Chroma)      │
              └──────────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd regression-suite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web testing)
playwright install
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: OPENAI_API_KEY or ANTHROPIC_API_KEY
```

Minimal `.env` configuration:
```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# HITL Configuration
HITL_MODE=APPROVE_PLAN

# Test Execution
TEST_FRAMEWORK=playwright
HEADLESS_MODE=true
```

### 3. Run Your First Test

```bash
# Check configuration
python main.py check

# List available application profiles
python main.py list-apps

# Run discovery on a web application
python main.py discover --app web_portal

# Run complete testing workflow
python main.py run --app web_portal --feature "user login functionality"
```

## 📖 Usage Examples

### Example 1: Simple Web Application Testing

```python
from models.app_profile import ApplicationProfile, ApplicationType, TestFramework
from agents.orchestrator import OrchestratorAgent

# Create application profile
app_profile = ApplicationProfile(
    name="my_web_app",
    app_type=ApplicationType.WEB,
    adapter="web_adapter",
    base_url="https://myapp.com",
    test_framework=TestFramework.PLAYWRIGHT,
    headless=True
)

# Initialize orchestrator
orchestrator = OrchestratorAgent(
    app_profile=app_profile,
    hitl_mode="APPROVE_PLAN"  # Require approval for test plans
)

# Run full workflow
result = orchestrator.run_full_workflow(
    feature_description="User authentication and login"
)

print(result)
```

### Example 2: API Testing

```python
from models.app_profile import ApplicationProfile, ApplicationType, AuthConfig

# Create API profile
app_profile = ApplicationProfile(
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
orchestrator = OrchestratorAgent(app_profile, hitl_mode="FULL_AUTO")
result = orchestrator.run_full_workflow("API endpoint testing")
```

### Example 3: Custom Application with Custom Adapter

```python
from adapters.custom_adapter import CustomAdapter
from adapters import register_adapter

# Create custom adapter
class MyAppAdapter(CustomAdapter):
    def discover_elements(self):
        # Your custom discovery logic
        pass

    def execute_test(self, test_case):
        # Your custom execution logic
        pass

# Register adapter
register_adapter("my_app_adapter", MyAppAdapter)

# Use it
app_profile = ApplicationProfile(
    name="custom_app",
    adapter="my_app_adapter",  # Use your custom adapter
    # ... other config
)
```

### Example 4: Oracle EBS Testing

```python
app_profile = ApplicationProfile(
    name="oracle_ebs",
    app_type=ApplicationType.ENTERPRISE,
    adapter="oracle_ebs_adapter",
    base_url="https://ebs.company.com:8000",
    auth=AuthConfig(
        auth_type="custom",
        username="ebs_user",
        password="password"
    ),
    modules=["GL", "AP", "AR"],
    custom_config={
        "responsibility": "System Administrator",
        "wait_for_forms": True
    }
)
```

## 🎯 Human-in-the-Loop (HITL) Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **FULL_AUTO** | No human intervention | CI/CD pipelines, automated regression |
| **APPROVE_PLAN** | Approve test plans only | Review test coverage before generation |
| **APPROVE_TESTS** | Approve generated tests | Review test scripts before execution |
| **APPROVE_ALL** | Approve everything | Maximum control and oversight |
| **INTERACTIVE** | Step-by-step guidance | Exploratory testing, learning |

### Using HITL Modes

```bash
# Command line
python main.py run --app my_app --feature "login" --hitl-mode APPROVE_ALL

# In code
orchestrator = OrchestratorAgent(app_profile, hitl_mode="INTERACTIVE")
```

### Approval Workflow

When approval is required, you'll see prompts like:

```
╔══════════════════════════════════════════════════════════╗
║              Human Review Required                        ║
╚══════════════════════════════════════════════════════════╝

Type: test_plan
Item: PLAN-A1B2C3D4
Timeout: 3600s remaining

Summary: Test plan for login feature with 5 test cases

Options:
  1. Approve
  2. Reject
  3. Approve with modifications

Your decision [1]:
```

### Web UI for HITL

**NEW**: A modern web-based interface is now available for HITL operations!

```bash
# Start the web UI
python web_ui/app.py

# Or specify host/port
WEB_UI_HOST=0.0.0.0 WEB_UI_PORT=8080 python web_ui/app.py
```

Access at: `http://localhost:5000`

**Features**:
- **Dashboard**: Real-time statistics and workflow monitoring
- **Approval Management**: Review and approve/reject with one click
- **Workflow Visualization**: Live progress tracking with stage details
- **Chat Interface**: Natural language interaction with orchestrator
- **Feedback System**: Submit detailed feedback on tests
- **WebSocket Updates**: Instant notifications for new approvals

**Using Web UI with Workflow**:
```python
from hitl.review_interface import WebReviewer
from agents.orchestrator import OrchestratorAgent

# Initialize with web reviewer
orchestrator = OrchestratorAgent(
    app_profile,
    hitl_mode="APPROVE_PLAN",
    interface=WebReviewer(port=5000)  # Uses web UI instead of CLI
)

result = orchestrator.run_full_workflow("Login feature testing")
```

See [`web_ui/README.md`](web_ui/README.md) for detailed documentation.

## 🔌 Creating Custom Adapters

1. **Inherit from BaseApplicationAdapter**:

```python
from adapters.base_adapter import BaseApplicationAdapter, DiscoveryResult, Element
from models.test_case import TestCase
from models.test_result import TestResult

class MyCustomAdapter(BaseApplicationAdapter):
    def discover_elements(self) -> DiscoveryResult:
        """Implement your discovery logic"""
        result = DiscoveryResult()
        # Add elements
        return result

    def execute_test(self, test_case: TestCase) -> TestResult:
        """Implement your test execution logic"""
        # Execute test
        return test_result

    def validate_state(self) -> bool:
        """Check if application is ready"""
        return True

    def cleanup(self) -> None:
        """Clean up resources"""
        pass
```

2. **Register your adapter**:

```python
from adapters import register_adapter

register_adapter("my_adapter", MyCustomAdapter)
```

3. **Use in application profile**:

```yaml
# config/app_profiles.yaml
my_app:
  adapter: "my_adapter"
  # ... other config
```

## 📊 RAG Knowledge Base

The framework uses RAG (Retrieval-Augmented Generation) to:
- Store historical test cases
- Learn from test execution results
- Retrieve similar test patterns
- Ground LLM outputs in real application data

### Adding to Knowledge Base

```python
from rag.retriever import TestKnowledgeRetriever

retriever = TestKnowledgeRetriever()

# Add test cases
retriever.add_test_cases(test_cases)

# Add test results
retriever.add_test_result(test_result)

# Add feedback
retriever.add_feedback_documents(feedback_docs)

# Search for similar tests
similar = retriever.find_similar_tests(
    query="login test",
    k=5,
    application="my_app"
)
```

## 🛠️ Configuration

### Application Profiles (`config/app_profiles.yaml`)

```yaml
my_app:
  name: "my_app"
  app_type: "web"
  adapter: "web_adapter"
  base_url: "https://myapp.com"

  auth:
    auth_type: "basic"
    username: "${APP_USERNAME}"
    password: "${APP_PASSWORD}"

  discovery:
    enabled: true
    max_depth: 3
    max_pages: 50
    exclude_patterns: ["/logout", "/admin"]

  test_framework: "playwright"
  parallel_execution: true
  max_workers: 4
  headless: true

  modules: ["auth", "dashboard", "reports"]
  features: ["login", "logout", "user_management"]
```

### Environment Variables

See [.env.example](.env.example) for all available configuration options.

## 📈 Reporting

The framework generates multiple report formats:

### HTML Reports
```python
report_path = reporting_agent.generate_report(results, format="html")
```

### JSON Reports
```python
report_path = reporting_agent.generate_report(results, format="json")
```

### CI/CD Integration
```python
reporting_agent.publish_to_cicd(results, platform="azure")
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

## 📚 Project Structure

```
regression-suite/
├── config/               # Configuration files
│   ├── settings.py       # Application settings
│   ├── llm_config.py     # LLM configuration
│   └── app_profiles.yaml # Application profiles
├── models/               # Data models
│   ├── test_case.py
│   ├── test_result.py
│   ├── approval.py
│   └── app_profile.py
├── adapters/             # Application adapters
│   ├── base_adapter.py
│   ├── web_adapter.py
│   ├── api_adapter.py
│   ├── oracle_ebs_adapter.py
│   └── custom_adapter.py
├── agents/               # AI agents
│   ├── orchestrator.py
│   ├── discovery.py
│   ├── test_planner.py
│   ├── test_generator.py
│   ├── test_executor.py
│   └── reporting.py
├── hitl/                 # Human-in-the-loop
│   ├── approval_manager.py
│   ├── feedback_collector.py
│   └── review_interface.py
├── rag/                  # RAG system
│   ├── vector_store.py
│   ├── embeddings.py
│   └── retriever.py
├── utils/                # Utilities
│   ├── logger.py
│   └── helpers.py
├── examples/             # Example scripts
├── tests/                # Test suite
├── main.py               # CLI entry point
└── README.md            # This file
```

## 🤝 Contributing

Contributions are welcome! Areas for contribution:
- New application adapters
- Additional test frameworks
- Enhanced HITL interfaces
- Performance optimizations
- Documentation improvements

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - LLM application framework
- [OpenAI](https://openai.com/) - GPT models
- [Playwright](https://playwright.dev/) - Web automation
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/regression-suite/issues)
- **Documentation**: See `/docs` folder
- **Examples**: See `/examples` folder

## 🗺️ Roadmap

- [ ] Web-based HITL interface
- [ ] Mobile app testing support (Appium)
- [ ] Database testing adapters
- [ ] Performance testing integration
- [ ] Test result analytics dashboard
- [ ] Multi-language test generation
- [ ] Advanced RAG with fine-tuned models

---

**Made with ❤️ by the Regression Suite Team**
