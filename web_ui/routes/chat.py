"""
Chat Routes - API endpoints for chat interface with orchestrator
"""

from flask import Blueprint, jsonify, request, current_app
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import threading

from agents_v2.orchestrator_agent_v2 import OrchestratorAgentV2
from models.app_profile import ApplicationProfile
from config.settings import get_settings
from utils.helpers import load_yaml
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

chat_bp = Blueprint('chat', __name__)

# In-memory chat history (could be persisted to database)
CHAT_HISTORY: List[Dict[str, Any]] = []

# Active workflow tracking
ACTIVE_WORKFLOWS: Dict[str, Dict[str, Any]] = {}


@chat_bp.route('/message', methods=['POST'])
def send_message():
    """
    Send a message to the orchestrator

    Expected request body:
    {
        "message": "Start testing login feature",
        "context": {"app_profile": "web_portal"}
    }
    """
    try:
        data = request.json or {}
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        context = data.get('context', {})

        # Add user message to history
        user_msg = {
            'id': f"msg-{len(CHAT_HISTORY) + 1}",
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat(),
            'context': context
        }
        CHAT_HISTORY.append(user_msg)

        # Process message and generate response
        # TODO: Integrate with actual orchestrator for dynamic responses
        assistant_response = _process_message(user_message, context)

        # Add assistant response to history
        assistant_msg = {
            'id': f"msg-{len(CHAT_HISTORY) + 1}",
            'role': 'assistant',
            'content': assistant_response,
            'timestamp': datetime.now().isoformat()
        }
        CHAT_HISTORY.append(assistant_msg)

        # Broadcast event to WebSocket clients
        current_app.broadcast_event('chat_message', {
            'user_message': user_msg,
            'assistant_message': assistant_msg
        })

        return jsonify({
            'success': True,
            'response': assistant_msg,
            'chat_id': assistant_msg['id']
        })

    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/history', methods=['GET'])
def get_history():
    """Get chat history"""
    try:
        # Optional: limit number of messages returned
        limit = request.args.get('limit', type=int)

        history = CHAT_HISTORY
        if limit:
            history = history[-limit:]

        return jsonify({
            'success': True,
            'count': len(history),
            'messages': history
        })

    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/clear', methods=['POST'])
def clear_history():
    """Clear chat history"""
    try:
        global CHAT_HISTORY
        CHAT_HISTORY = []

        return jsonify({
            'success': True,
            'message': 'Chat history cleared'
        })

    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return jsonify({'error': str(e)}), 500


def _load_application_profile(app_name: str) -> Optional[ApplicationProfile]:
    """
    Load application profile from config

    Args:
        app_name: Application profile name

    Returns:
        ApplicationProfile object or None if not found
    """
    try:
        profiles_path = Path("config/app_profiles.yaml")

        if not profiles_path.exists():
            logger.error("app_profiles.yaml not found")
            return None

        profiles_data = load_yaml(str(profiles_path))
        app_config = profiles_data.get("applications", {}).get(app_name)

        if not app_config:
            logger.error(f"Application profile '{app_name}' not found")
            return None

        return ApplicationProfile(**app_config)
    except Exception as e:
        logger.error(f"Error loading application profile: {e}")
        return None


def _extract_url_from_message(message: str) -> Optional[str]:
    """
    Extract URL from message

    Args:
        message: User message

    Returns:
        Extracted URL or None
    """
    import re
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, message)
    return match.group(0) if match else None


def _run_orchestrator_workflow(
    workflow_id: str,
    app_profile: ApplicationProfile,
    feature_description: str
):
    """
    Run orchestrator workflow in background thread

    Args:
        workflow_id: Unique workflow ID
        app_profile: Application profile
        feature_description: Feature to test
    """
    try:
        # Update workflow status
        ACTIVE_WORKFLOWS[workflow_id] = {
            'status': 'running',
            'current_stage': 'initializing',
            'start_time': datetime.now().isoformat()
        }

        # Initialize orchestrator with HITL enabled
        orchestrator = OrchestratorAgentV2(
            app_profile=app_profile,
            output_dir="generated_tests",
            reports_dir="reports",
            enable_hitl=True,  # Enable HITL for web interface
        )

        logger.info(f"Starting workflow {workflow_id} for feature: {feature_description}")

        # Run workflow
        final_state = orchestrator.run_full_workflow(
            feature_description=feature_description
        )

        # Update workflow status
        ACTIVE_WORKFLOWS[workflow_id] = {
            'status': 'completed',
            'current_stage': 'finalized',
            'end_time': datetime.now().isoformat(),
            'final_state': final_state
        }

        # Add completion message to chat
        completion_msg = {
            'id': f"msg-{len(CHAT_HISTORY) + 1}",
            'role': 'assistant',
            'content': f"Workflow completed! Status: {final_state.get('workflow_status')}",
            'timestamp': datetime.now().isoformat()
        }
        CHAT_HISTORY.append(completion_msg)

        logger.info(f"Workflow {workflow_id} completed with status: {final_state.get('workflow_status')}")

    except Exception as e:
        logger.error(f"Error in workflow {workflow_id}: {e}")
        ACTIVE_WORKFLOWS[workflow_id] = {
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.now().isoformat()
        }

        # Add error message to chat
        error_msg = {
            'id': f"msg-{len(CHAT_HISTORY) + 1}",
            'role': 'assistant',
            'content': f"Workflow failed: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }
        CHAT_HISTORY.append(error_msg)


def _process_message(message: str, context: Dict[str, Any]) -> str:
    """
    Process user message and invoke orchestrator if needed

    Args:
        message: User message
        context: Message context

    Returns:
        Assistant response
    """
    message_lower = message.lower()

    # Simple command detection
    if any(word in message_lower for word in ['start', 'run', 'execute', 'test']):
        # Extract URL from message if present
        url = _extract_url_from_message(message)

        # Extract feature description
        feature_description = "Complete regression test suite"
        if 'login' in message_lower or 'auth' in message_lower:
            feature_description = "User login and authentication functionality"
        elif 'checkout' in message_lower:
            feature_description = "Checkout flow"
        elif 'discover' in message_lower:
            feature_description = "Application discovery"

        # Get or create application profile
        app_profile = None
        app_name = context.get('app_profile', 'web_portal')  # Default to web_portal

        if url:
            # Create dynamic profile from URL
            from models.app_profile import ApplicationType, TestFramework
            app_profile = ApplicationProfile(
                name="web_app_dynamic",
                app_type=ApplicationType.WEB,
                adapter="web_adapter",
                base_url=url,
                test_framework=TestFramework.PLAYWRIGHT,
                description=f"Dynamic web application at {url}"
            )
        else:
            # Load from config
            app_profile = _load_application_profile(app_name)

        if not app_profile:
            return f"Could not load application profile '{app_name}'. Please check your configuration."

        # Generate workflow ID
        workflow_id = f"workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Start orchestrator workflow in background thread
        workflow_thread = threading.Thread(
            target=_run_orchestrator_workflow,
            args=(workflow_id, app_profile, feature_description),
            daemon=True
        )
        workflow_thread.start()

        # Return immediate response
        return (f"Starting workflow for {feature_description}...\n\n"
                f"I'll run through these stages:\n"
                f"1. Discovery - Find testable elements\n"
                f"2. Planning - Create test plan\n"
                f"3. Generation - Generate test scripts\n"
                f"4. Execution - Run tests\n"
                f"5. Reporting - Generate reports\n\n"
                f"You'll receive approval requests for key stages. Check the Approvals section!")

    elif any(word in message_lower for word in ['status', 'progress', 'where']):
        if ACTIVE_WORKFLOWS:
            latest_workflow_id = list(ACTIVE_WORKFLOWS.keys())[-1]
            workflow = ACTIVE_WORKFLOWS[latest_workflow_id]
            status = workflow.get('status', 'unknown')
            stage = workflow.get('current_stage', 'unknown')
            return f"Current workflow status: **{status}**\nStage: **{stage}**"
        else:
            return "No active workflows at the moment."

    elif any(word in message_lower for word in ['approve', 'approval', 'pending']):
        from web_ui.services.approval_service import ApprovalService
        service = ApprovalService()
        pending = service.get_pending_approvals()

        if pending:
            count = len(pending)
            return f"You have {count} pending approval(s). Please review them in the Approvals section."
        else:
            return "No pending approvals at the moment."

    elif any(word in message_lower for word in ['help', 'what can you']):
        return ("I can help you with:\n\n"
               "• **Start Testing**: \"Start testing login feature for https://example.com\" or \"Run tests for checkout\"\n"
               "• **Check Status**: \"What's the current status?\" or \"Show progress\"\n"
               "• **Approvals**: \"Show pending approvals\" or \"What needs approval?\"\n"
               "• **Discovery**: \"Discover the application\" or \"Find all elements\"\n"
               "• **Reports**: \"Generate report\" or \"Show test results\"\n\n"
               "You can also ask specific questions about the testing process!")

    elif any(word in message_lower for word in ['report', 'results', 'summary']):
        return ("I can generate comprehensive test reports in HTML, JSON, and Markdown formats. "
               "Reports will be available in the reports/ directory after test execution completes.")

    else:
        return ("I understand you're asking about testing. Could you please be more specific? "
               "You can:\n"
               "• Ask me to start testing a feature (e.g., 'Start testing login for https://example.com')\n"
               "• Check workflow status\n"
               "• Review pending approvals\n"
               "• Get help with available commands\n\n"
               f"Type 'help' to see all available commands.")
