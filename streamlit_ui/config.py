"""
Streamlit UI Configuration
"""

import os
from typing import Dict, Any

# Streamlit configuration
STREAMLIT_CONFIG = {
    "page_title": "AI Regression Testing",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Theme configuration
THEME = {
    "primaryColor": "#1f77b4",
    "backgroundColor": "#ffffff",
    "secondaryBackgroundColor": "#f8f9fa",
    "textColor": "#2c3e50",
    "font": "sans-serif"
}

# Redis configuration (from environment)
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD"),
    "key_prefix": os.getenv("REDIS_KEY_PREFIX", "ai_regression_test")
}

# Authentication configuration
AUTH_CONFIG = {
    "cookie_name": "ai_test_auth",
    "cookie_key": os.getenv("AUTH_COOKIE_KEY", "ai_testing_secret_key"),
    "cookie_expiry_days": 30,
}

# Default users (for initial setup)
DEFAULT_USERS = {
    "admin": {
        "name": "Admin User",
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),  # Change in production!
        "role": "admin"
    },
    "tester": {
        "name": "Test User",
        "password": os.getenv("TESTER_PASSWORD", "tester123"),
        "role": "tester"
    },
    "viewer": {
        "name": "Viewer User",
        "password": os.getenv("VIEWER_PASSWORD", "viewer123"),
        "role": "viewer"
    }
}

# LLM configuration
LLM_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "anthropic"),
    "model": os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1"))
}

# UI Messages
MESSAGES = {
    "welcome": """
    ### Welcome to AI Regression Testing Framework!

    This intelligent system helps you:
    - **Discover** application elements automatically
    - **Plan** comprehensive test scenarios with AI
    - **Generate** executable test scripts
    - **Execute** tests in parallel
    - **Report** results with detailed analytics

    Choose **Interactive Mode** for AI-guided conversations or **Autonomous Mode** for batch processing.
    """,

    "no_redis": """
    ⚠️ **Redis not available** - Using in-memory storage (fakeredis).

    Your data will not persist across restarts. For production use, install and run Redis:
    ```
    # Install Redis
    docker run -d -p 6379:6379 redis:latest
    # Or: brew install redis && brew services start redis
    ```
    """,

    "no_api_key": """
    ⚠️ **LLM API key not configured**

    Interactive mode with AI reasoning requires an API key. Add to `.env`:
    ```
    ANTHROPIC_API_KEY=your_key_here
    # or
    OPENAI_API_KEY=your_key_here
    ```
    """,
}

# Page descriptions
PAGES = {
    "home": {
        "title": "🏠 Home",
        "description": "Dashboard and quick actions"
    },
    "discovery": {
        "title": "🔍 Discovery",
        "description": "Explore and discover application elements"
    },
    "planning": {
        "title": "📋 Test Planning",
        "description": "Create intelligent test plans"
    },
    "generation": {
        "title": "📝 Test Generation",
        "description": "Generate executable test scripts"
    },
    "execution": {
        "title": "▶️ Test Execution",
        "description": "Run tests and collect results"
    },
    "reports": {
        "title": "📊 Reports",
        "description": "View analytics and reports"
    },
    "workflow": {
        "title": "🔄 Full Workflow",
        "description": "End-to-end test automation"
    }
}

def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    configs = {
        "streamlit": STREAMLIT_CONFIG,
        "theme": THEME,
        "redis": REDIS_CONFIG,
        "auth": AUTH_CONFIG,
        "llm": LLM_CONFIG,
        "messages": MESSAGES,
        "pages": PAGES
    }
    return configs.get(key, default)
