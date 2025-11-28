"""
Conversational Orchestrator Agent

LLM-powered orchestrator that understands natural language,
explains reasoning, and intelligently routes to appropriate agents.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2
from agents_v2.discovery_agent_v2 import DiscoveryAgentV2
from agents_v2.test_planner_agent_v2 import TestPlannerAgentV2
from agents_v2.test_generator_agent_v2 import TestGeneratorAgentV2
from agents_v2.test_executor_agent_v2 import TestExecutorAgentV2
from agents_v2.conversational_state import ConversationalState, IntentClassification
from config.llm_config import get_smart_llm
from memory import ConversationMemory, StateManager, get_redis_manager
from models.app_profile import ApplicationProfile, ApplicationType, TestFramework, DiscoveryConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class UserIntent(BaseModel):
    """Structured user intent"""
    intent_type: str = Field(description="Type: discovery, planning, generation, execution, report, question, help")
    confidence: float = Field(description="Confidence score 0-1")
    entities: Dict[str, Any] = Field(description="Extracted entities like URL, feature, framework")
    reasoning: str = Field(description="Why this intent was chosen")
    requires_clarification: bool = Field(description="Whether clarification is needed")
    missing_info: List[str] = Field(default_factory=list, description="What information is missing")
    suggested_questions: List[str] = Field(default_factory=list, description="Questions to ask user")


class ConversationalOrchestratorAgent:
    """
    Intelligent orchestrator that understands natural language
    and manages multi-turn conversations
    """

    INTENT_DETECTION_PROMPT = """You are an intelligent test automation orchestrator. Analyze the user's request and determine their intent.

Available Actions:
- discovery: Explore application to find UI elements, APIs, or database schemas
- planning: Create test plans and test cases from requirements
- generation: Generate executable test scripts (Playwright, Selenium, etc.)
- execution: Run tests and collect results
- report: Generate test reports and analytics
- question: User asking about results, status, or clarifications
- help: User needs guidance on how to use the system

Context from conversation:
{conversation_context}

Current workflow state:
{workflow_state}

User request: "{user_request}"

Analyze the request and respond with:
1. What is the user trying to accomplish?
2. What information do we already have?
3. What information is missing?
4. What should we do next?

Respond in JSON format."""

    AGENT_SELECTION_PROMPT = """You are deciding which agents to invoke for a test automation workflow.

Available Agents:
- DiscoveryAgent: Discovers UI elements, APIs, database schemas from applications
- TestPlannerAgent: Creates comprehensive test plans from feature descriptions and discovered elements
- TestGeneratorAgent: Generates executable test scripts in Playwright, Selenium, or Pytest
- TestExecutorAgent: Executes tests in parallel, captures results and screenshots
- ReportingAgent: Generates HTML, JSON, or Markdown reports with analytics

User Intent: {intent}
Extracted Entities: {entities}

Current State:
- Completed stages: {completed_stages}
- Available data: {available_data}

Which agent(s) should we invoke and why? Consider:
1. What's already been done (don't repeat work)
2. What's the most efficient path forward
3. What dependencies exist between agents

Explain your reasoning step by step."""

    def __init__(
        self,
        session_id: str,
        user_id: str = "default_user",
        llm_provider: str = "anthropic",
        execution_mode: str = "interactive"
    ):
        """
        Initialize conversational orchestrator

        Args:
            session_id: Unique session ID
            user_id: User identifier
            llm_provider: "anthropic" or "openai"
            execution_mode: "interactive" or "autonomous"
        """
        self.session_id = session_id
        self.user_id = user_id
        self.execution_mode = execution_mode

        # Initialize LLM
        self.llm = get_smart_llm(provider=llm_provider)

        # Initialize memory components
        self.redis = get_redis_manager()
        self.conversation_memory = ConversationMemory(session_id)
        self.state_manager = StateManager()

        # Initialize underlying orchestrator (for actual execution)
        self.orchestrator: Optional[OrchestratorAgentV2] = None

        # State
        self.state: ConversationalState = {
            "session_id": session_id,
            "user_id": user_id,
            "execution_mode": execution_mode,
            "conversation_id": session_id,
            "reasoning_steps": [],
            "clarification_needed": False,
            "awaiting_approval": False,
        }

        logger.info(f"ConversationalOrchestrator initialized for session {session_id}")

    def process_user_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process user message and return response

        Args:
            user_message: Natural language input from user

        Returns:
            Response dict with message, reasoning, and suggested actions
        """
        try:
            # Save user message
            self.conversation_memory.add_user_message(user_message)

            # Check if we're awaiting approval
            if self.state.get("awaiting_approval") and self.state.get("pending_action"):
                # Check if user is confirming
                if self._is_affirmative(user_message):
                    response = self._execute_pending_action()
                else:
                    # User declined
                    self.state["awaiting_approval"] = False
                    self.state["pending_action"] = None
                    response = {
                        "message": "No problem! What would you like to do instead?",
                        "status": "cancelled"
                    }
            else:
                # Detect intent
                intent = self._detect_intent(user_message)

                # Check if clarification needed
                if intent.requires_clarification:
                    response = self._request_clarification(intent)
                else:
                    # Select and execute appropriate agents
                    response = self._execute_workflow(intent)

            # Update state if awaiting approval
            if response.get("awaiting_approval"):
                self.state["awaiting_approval"] = True
                self.state["pending_action"] = response.get("action")
                self.state["pending_params"] = response.get("params")

            # Save assistant response
            self.conversation_memory.add_assistant_message(
                response["message"],
                reasoning=response.get("reasoning"),
                intent=response.get("intent")
            )

            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "message": f"I encountered an error: {str(e)}. Could you try rephrasing your request?",
                "error": str(e),
                "status": "error"
            }

    def _is_affirmative(self, message: str) -> bool:
        """Check if message is affirmative (yes, ok, proceed, etc.)"""
        affirmative_words = ["yes", "ok", "okay", "sure", "proceed", "go ahead", "do it", "confirm", "yep", "yeah"]
        message_lower = message.lower().strip()
        return any(word in message_lower for word in affirmative_words)

    def _execute_pending_action(self) -> Dict[str, Any]:
        """Execute the pending action that was awaiting approval"""
        action = self.state.get("pending_action")
        params = self.state.get("pending_params", {})

        # Clear pending state
        self.state["awaiting_approval"] = False
        self.state["pending_action"] = None
        self.state["pending_params"] = None

        # Execute based on action type
        if action == "discovery":
            return self._execute_discovery(params)
        elif action == "planning":
            return self._execute_planning(params)
        elif action == "generation":
            return self._execute_generation(params)
        elif action == "execution":
            return self._execute_execution(params)
        else:
            return {
                "message": f"I don't know how to execute action: {action}",
                "status": "error"
            }

    def _detect_intent(self, user_message: str) -> UserIntent:
        """
        Detect user intent using LLM

        Args:
            user_message: User's message

        Returns:
            Parsed intent
        """
        # Get conversation context
        recent_messages = self.conversation_memory.get_last_n_messages(5)
        context = "\n".join([
            f"{msg.role.value}: {msg.content}"
            for msg in recent_messages[:-1]  # Exclude current message
        ])

        # Get workflow state
        workflow_state = self.state_manager.get_workflow_state(self.session_id)
        state_summary = "No previous workflow" if not workflow_state else f"Current stage: {workflow_state.current_stage}, Completed: {workflow_state.completed_stages}"

        # Create prompt
        prompt = ChatPromptTemplate.from_template(self.INTENT_DETECTION_PROMPT)

        # Use structured output
        parser = JsonOutputParser(pydantic_object=UserIntent)

        chain = prompt | self.llm | parser

        try:
            result = chain.invoke({
                "user_request": user_message,
                "conversation_context": context or "No previous context",
                "workflow_state": state_summary
            })

            intent = UserIntent(**result)
            logger.info(f"Detected intent: {intent.intent_type} (confidence: {intent.confidence})")

            return intent

        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            # Fallback: basic keyword matching
            return self._fallback_intent_detection(user_message)

    def _fallback_intent_detection(self, message: str) -> UserIntent:
        """Simple keyword-based intent detection fallback"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["discover", "explore", "find elements", "crawl"]):
            intent_type = "discovery"
        elif any(word in message_lower for word in ["plan", "test case", "test plan", "scenarios"]):
            intent_type = "planning"
        elif any(word in message_lower for word in ["generate", "create tests", "write tests", "scripts"]):
            intent_type = "generation"
        elif any(word in message_lower for word in ["run", "execute", "test", "start testing"]):
            intent_type = "execution"
        elif any(word in message_lower for word in ["report", "results", "analytics", "show"]):
            intent_type = "report"
        elif any(word in message_lower for word in ["help", "how", "what", "?"]):
            intent_type = "help"
        else:
            intent_type = "question"

        # Check for URL
        entities = {"original_message": message}
        if "http" in message:
            import re
            urls = re.findall(r'https?://[^\s]+', message)
            if urls:
                entities["url"] = urls[0]

        # For discovery intent, check if we need URL or already have cached discovery
        requires_clarification = False
        missing_info = []
        if intent_type == "discovery" and not entities.get("url"):
            requires_clarification = True
            missing_info = ["url"]

        return UserIntent(
            intent_type=intent_type,
            confidence=0.6,
            entities=entities,
            reasoning="Fallback keyword matching",
            requires_clarification=requires_clarification,
            missing_info=missing_info,
            suggested_questions=["What is the URL of the application you want to test?"] if missing_info else []
        )

    def _request_clarification(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Request clarification from user

        Args:
            intent: Detected intent with missing information

        Returns:
            Response asking for clarification
        """
        questions = intent.suggested_questions

        message = f"I understand you want to {intent.intent_type}, but I need some more information:\n\n"
        message += "\n".join([f"• {q}" for q in questions])

        return {
            "message": message,
            "reasoning": f"Missing information: {', '.join(intent.missing_info)}",
            "requires_input": True,
            "missing_info": intent.missing_info,
            "status": "awaiting_input"
        }

    def _execute_workflow(self, intent: UserIntent) -> Dict[str, Any]:
        """
        Execute appropriate workflow based on intent

        Args:
            intent: User intent

        Returns:
            Execution result with reasoning
        """
        # Route based on intent type
        if intent.intent_type == "discovery":
            return self._handle_discovery(intent)
        elif intent.intent_type == "planning":
            return self._handle_planning(intent)
        elif intent.intent_type == "generation":
            return self._handle_generation(intent)
        elif intent.intent_type == "execution":
            return self._handle_execution(intent)
        elif intent.intent_type == "report":
            return self._handle_reporting(intent)
        elif intent.intent_type == "help":
            return self._handle_help()
        else:
            return self._handle_question(intent)

    def _handle_discovery(self, intent: UserIntent) -> Dict[str, Any]:
        """Handle discovery intent"""
        url = intent.entities.get("url")

        if not url:
            return {
                "message": "I need the URL of the application to discover. What URL should I explore?",
                "status": "awaiting_input"
            }

        reasoning = f"I'll discover elements from {url}. This will help me understand the application structure for test planning."

        if self.execution_mode == "interactive":
            message = f"🔍 **Discovery Plan**\n\n{reasoning}\n\nShould I proceed?"
            return {
                "message": message,
                "reasoning": reasoning,
                "awaiting_approval": True,
                "action": "discovery",
                "params": {"url": url},
                "status": "awaiting_approval"
            }
        else:
            # TODO: Actually invoke discovery agent
            message = f"🔍 Starting discovery of {url}...\n\n{reasoning}"
            return {
                "message": message,
                "reasoning": reasoning,
                "status": "executing"
            }

    def _handle_planning(self, intent: UserIntent) -> Dict[str, Any]:
        """Handle test planning intent"""
        feature = intent.entities.get("feature", "application functionality")

        reasoning = f"I'll create a comprehensive test plan for {feature}."

        # Check if discovery was done
        cached_discovery = self.state_manager.get_cached_discovery(self.session_id)
        if not cached_discovery:
            reasoning += " Note: I don't have discovery data yet, so I'll create a plan based on your description."

        message = f"📋 **Test Planning**\n\n{reasoning}\n\n"

        if self.execution_mode == "interactive":
            message += "What level of coverage do you want? (basic/standard/comprehensive)"
            return {
                "message": message,
                "reasoning": reasoning,
                "awaiting_input": True,
                "status": "awaiting_input"
            }
        else:
            message += "Creating test plan..."
            return {
                "message": message,
                "reasoning": reasoning,
                "status": "executing"
            }

    def _handle_generation(self, intent: UserIntent) -> Dict[str, Any]:
        """Handle test generation intent"""
        framework = intent.entities.get("framework", "playwright")

        reasoning = f"I'll generate {framework} test scripts based on the test plan."

        message = f"📝 **Test Generation**\n\n{reasoning}\n\n"

        if self.execution_mode == "interactive":
            message += f"Generating scripts with {framework}... This may take a moment."

        return {
            "message": message,
            "reasoning": reasoning,
            "status": "executing"
        }

    def _handle_execution(self, intent: UserIntent) -> Dict[str, Any]:
        """Handle test execution intent"""
        reasoning = "I'll execute the generated tests and collect results."

        message = f"🧪 **Test Execution**\n\n{reasoning}\n\n"

        if self.execution_mode == "interactive":
            message += "Ready to run tests. Shall I proceed?"
            return {
                "message": message,
                "reasoning": reasoning,
                "awaiting_approval": True,
                "action": "execution",
                "params": {},
                "status": "awaiting_approval"
            }

        return {
            "message": message + "Starting execution...",
            "reasoning": reasoning,
            "status": "executing"
        }

    def _handle_reporting(self, intent: UserIntent) -> Dict[str, Any]:
        """Handle reporting intent"""
        return {
            "message": "📊 I'll generate a comprehensive test report for you.",
            "reasoning": "Compiling test results into a report",
            "status": "executing"
        }

    def _handle_help(self) -> Dict[str, Any]:
        """Handle help request"""
        help_text = """
**What I Can Help You With:**

🔍 **Discovery** - "Discover elements from myapp.com"
📋 **Test Planning** - "Create test plan for login functionality"
📝 **Test Generation** - "Generate Playwright tests"
🧪 **Test Execution** - "Run the tests"
📊 **Reporting** - "Show me the results"

**Tips:**
• Provide URLs for discovery
• Be specific about features to test
• I'll ask for clarification if needed
• In interactive mode, I'll explain my reasoning at each step
"""

        return {
            "message": help_text,
            "status": "complete"
        }

    def _handle_question(self, intent: UserIntent) -> Dict[str, Any]:
        """Handle general questions"""
        message_lower = intent.entities.get("original_message", "").lower()

        # Check if asking about discovered elements
        if any(word in message_lower for word in ["show", "display", "elements", "found", "discovered", "results"]):
            cached_discovery = self.state_manager.get_cached_discovery(self.session_id)
            if cached_discovery:
                elements = cached_discovery.get("elements", [])
                pages = cached_discovery.get("pages", [])
                url = cached_discovery.get("url", "unknown")

                message = f"📊 **Discovery Results for {url}**\n\n"
                message += f"**Summary:**\n"
                message += f"- Total Elements: {len(elements)}\n"
                message += f"- Total Pages: {len(pages)}\n\n"

                if elements:
                    message += "**Sample Elements:**\n"
                    for i, elem in enumerate(elements[:5]):  # Show first 5
                        elem_type = elem.get("type", "unknown")
                        elem_name = elem.get("name", "unnamed")
                        message += f"{i+1}. {elem_type}: {elem_name}\n"

                    if len(elements) > 5:
                        message += f"\n...and {len(elements) - 5} more elements\n"

                message += "\nWhat would you like to do next?"

                return {
                    "message": message,
                    "status": "complete",
                    "data": cached_discovery
                }

        # Check workflow state
        workflow_state = self.state_manager.get_workflow_state(self.session_id)
        cached_discovery = self.state_manager.get_cached_discovery(self.session_id)

        if cached_discovery:
            url = cached_discovery.get("url", "")
            elements_count = cached_discovery.get("total_elements", 0)
            message = f"I have discovered {elements_count} elements from {url}.\n\n"
            message += "What would you like to do?\n"
            message += "• Create a test plan\n"
            message += "• Show discovered elements\n"
            message += "• Discover a different application"
        elif workflow_state:
            message = f"Current status: Stage {workflow_state.current_stage}, Completed: {', '.join(workflow_state.completed_stages) or 'None'}"
        else:
            message = "No workflow in progress. What would you like to test?\n\n"
            message += "You can:\n"
            message += "• Discover elements from a URL\n"
            message += "• Create test plans\n"
            message += "• Generate test scripts"

        return {
            "message": message,
            "status": "complete"
        }

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation summary"""
        return self.conversation_memory.get_summary()

    def _execute_discovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute discovery workflow"""
        url = params.get("url")

        logger.info(f"Executing discovery for URL: {url}")

        try:
            message = f"🔍 **Discovering elements from {url}...**\n\n"

            # Create a basic application profile for discovery
            logger.info("Creating application profile")
            discovery_config = DiscoveryConfig(
                enabled=True,
                url=url,
                max_depth=2,
                max_pages=10
            )

            app_profile = ApplicationProfile(
                name="discovered_app",
                app_type=ApplicationType.WEB,
                adapter="web",
                base_url=url,
                test_framework=TestFramework.PLAYWRIGHT,
                discovery=discovery_config
            )

            # Initialize and run discovery agent
            logger.info("Initializing discovery agent")
            discovery_agent = DiscoveryAgentV2(app_profile=app_profile)

            message += "⏳ Analyzing application structure...\n\n"

            # Execute discovery
            logger.info("Starting discovery process")
            discovery_state = discovery_agent.discover(
                url=url,
                max_depth=2,
                max_pages=10
            )
            logger.info(f"Discovery completed. State keys: {list(discovery_state.keys())}")

            # Extract results
            elements = discovery_state.get("elements", [])
            pages = discovery_state.get("pages", [])
            logger.info(f"Found {len(elements)} elements and {len(pages)} pages")

            # Cache results
            result_data = {
                "url": url,
                "elements": elements,
                "pages": pages,
                "total_elements": len(elements),
                "total_pages": len(pages)
            }
            self.state_manager.cache_discovery_result(self.session_id, result_data)
            logger.info("Results cached successfully")

            message += f"✅ **Discovery Complete!**\n\n"
            message += f"- **Found {len(elements)} elements**\n"
            message += f"- **Discovered {len(pages)} pages**\n\n"

            # Provide helpful feedback if no elements found
            if len(elements) == 0:
                message += "⚠️ **No elements found.** This could mean:\n"
                message += "• Playwright browsers not installed (run: `playwright install chromium`)\n"
                message += "• URL is not accessible or requires authentication\n"
                message += "• Page uses dynamic loading (JavaScript frameworks)\n"
                message += "• Network/firewall issues\n\n"
                message += "Please check the URL and try again, or provide a different URL.\n"
            else:
                message += "What would you like to do next?\n"
                message += "• Create test plan\n"
                message += "• Show discovered elements\n"

            return {
                "message": message,
                "status": "complete",
                "reasoning": f"Successfully discovered {len(elements)} elements from {url}",
                "data": result_data
            }
        except Exception as e:
            logger.error(f"Discovery execution failed: {e}", exc_info=True)
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Full traceback: {error_details}")
            return {
                "message": f"❌ **Discovery Failed**\n\n{str(e)}\n\nPlease check:\n• URL is accessible\n• Playwright is installed (`playwright install`)\n• No firewall blocking access",
                "status": "error",
                "error": str(e),
                "traceback": error_details
            }

    def _execute_planning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test planning workflow"""
        feature = params.get("feature", "application")

        try:
            message = f"📋 Creating test plan for {feature}...\n\n"

            # TODO: Implement actual test planning agent invocation
            message += "⚠️ Test planning agent integration is in progress.\n\n"
            message += "This will generate comprehensive test cases and scenarios.\n\n"
            message += "What would you like to do next?"

            return {
                "message": message,
                "status": "complete",
                "reasoning": f"Test planning for {feature} initiated"
            }
        except Exception as e:
            logger.error(f"Planning execution failed: {e}")
            return {
                "message": f"❌ Planning failed: {str(e)}",
                "status": "error",
                "error": str(e)
            }

    def _execute_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test generation workflow"""
        framework = params.get("framework", "playwright")

        try:
            message = f"📝 Generating {framework} test scripts...\n\n"

            # TODO: Implement actual test generation agent invocation
            message += "⚠️ Test generation agent integration is in progress.\n\n"
            message += "This will create executable test scripts based on the test plan.\n\n"
            message += "What would you like to do next?"

            return {
                "message": message,
                "status": "complete",
                "reasoning": f"Test generation with {framework} initiated"
            }
        except Exception as e:
            logger.error(f"Generation execution failed: {e}")
            return {
                "message": f"❌ Generation failed: {str(e)}",
                "status": "error",
                "error": str(e)
            }

    def _execute_execution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test execution workflow"""
        try:
            message = "🧪 Executing tests...\n\n"

            # TODO: Implement actual test execution agent invocation
            message += "⚠️ Test execution agent integration is in progress.\n\n"
            message += "This will run the generated tests and collect results.\n\n"
            message += "What would you like to do next?"

            return {
                "message": message,
                "status": "complete",
                "reasoning": "Test execution initiated"
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "message": f"❌ Execution failed: {str(e)}",
                "status": "error",
                "error": str(e)
            }
