# Quick Start Guide

Get up and running with the Agentic AI Regression Testing Framework in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- OpenAI API key (or Anthropic API key)
- Basic understanding of testing concepts

## Step 1: Install Dependencies (2 minutes)

```bash
# Navigate to the project directory
cd "c:\Projects\Regression Suite"

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web testing)
playwright install chromium
```

## Step 2: Configure API Key (1 minute)

Create a `.env` file in the project root:

```bash
# Copy the example file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

Edit `.env` and add your API key:

```env
OPENAI_API_KEY=sk-your-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
HITL_MODE=APPROVE_PLAN
```

## Step 3: Verify Installation (30 seconds)

```bash
python main.py check
```

You should see:
```
✓ Settings loaded
✓ LLM Connection: Working
✓ Configuration check complete
```

## Step 4: Run Your First Test (1.5 minutes)

### Option A: Using the CLI

```bash
# Discover a web application
python main.py discover --app web_portal

# Run complete workflow
python main.py run --app web_portal --feature "login functionality"
```

### Option B: Using Python Script

Create `my_first_test.py`:

```python
from models.app_profile import ApplicationProfile, ApplicationType, TestFramework
from agents.orchestrator import OrchestratorAgent

# Create profile for your application
app_profile = ApplicationProfile(
    name="my_app",
    app_type=ApplicationType.WEB,
    adapter="web_adapter",
    base_url="https://example.com",
    test_framework=TestFramework.PLAYWRIGHT,
    headless=True
)

# Create orchestrator
orchestrator = OrchestratorAgent(
    app_profile=app_profile,
    hitl_mode="FULL_AUTO"  # No human approval needed
)

# Run workflow
result = orchestrator.run_full_workflow("Test the homepage")

print("Success!" if result["success"] else "Failed")
print(result.get("output", ""))

# Cleanup
orchestrator.cleanup()
```

Run it:
```bash
python my_first_test.py
```

## What Happens?

The framework will:

1. **🔍 Discover** your application (UI elements, APIs)
2. **📋 Plan** test cases using AI
3. **⚙️ Generate** executable test scripts
4. **🚀 Execute** the tests
5. **📊 Report** results in HTML/JSON

## Understanding HITL Modes

The framework supports different levels of human oversight:

```python
hitl_mode="FULL_AUTO"      # No approval needed - fully automated
hitl_mode="APPROVE_PLAN"   # Approve test plan before generation
hitl_mode="APPROVE_TESTS"  # Approve generated tests before execution
hitl_mode="APPROVE_ALL"    # Approve everything
hitl_mode="INTERACTIVE"    # Step-by-step interaction
```

## Next Steps

### 1. Configure Your Application

Edit `config/app_profiles.yaml`:

```yaml
my_real_app:
  name: "my_real_app"
  app_type: "web"
  adapter: "web_adapter"
  base_url: "https://yourapp.com"

  auth:
    auth_type: "basic"
    username: "test_user"
    password: "test_pass"

  test_framework: "playwright"
  headless: true
```

### 2. Run Tests on Your App

```bash
python main.py run --app my_real_app --feature "user registration"
```

### 3. Try Different Features

```bash
# Discovery only
python main.py discover --app my_real_app

# Create test plan with approval
python main.py plan --app my_real_app --feature "checkout process" --hitl-mode APPROVE_PLAN

# List available apps
python main.py list-apps
```

### 4. Explore Examples

```bash
# Simple example
python examples/simple_example.py

# Custom adapter example
python examples/custom_app_example.py
```

## Common Issues & Solutions

### Issue: "OpenAI API key not found"
**Solution**: Make sure `.env` file exists and contains valid `OPENAI_API_KEY`

### Issue: "Playwright browsers not installed"
**Solution**: Run `playwright install`

### Issue: "Application not accessible"
**Solution**: Check `base_url` in your application profile and ensure the application is running

### Issue: "Import errors"
**Solution**: Ensure virtual environment is activated and all dependencies are installed

## Getting Help

- 📖 Full documentation: [README.md](README.md)
- 💡 Examples: Check the `/examples` folder
- 🐛 Issues: Report on GitHub
- 💬 Questions: Open a discussion

## Tips for Success

1. **Start Simple**: Begin with `FULL_AUTO` mode and simple tests
2. **Use HITL**: Enable `APPROVE_PLAN` mode to review test plans
3. **Iterate**: Review generated tests and provide feedback
4. **Customize**: Create custom adapters for your specific applications
5. **Monitor**: Check logs in `logs/regression_suite.log`

## What's Next?

- ✅ Set up CI/CD integration
- ✅ Create custom adapters for your applications
- ✅ Build a knowledge base of test cases
- ✅ Integrate with your existing test infrastructure

---

**🎉 Congratulations!** You're now ready to use the Agentic AI Regression Testing Framework!
