"""
Web UI for HITL (Human-in-the-Loop) Regression Testing Framework

This Flask application provides a web interface for:
- Approving test plans, test cases, and execution
- Monitoring workflow progress in real-time
- Submitting feedback on test results
- Managing application profiles and configuration
- Chat interface with the orchestrator
"""

import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_sock import Sock

from config.settings import get_settings
from utils.logger import get_logger

# Import routes
from web_ui.routes.approvals import approvals_bp
from web_ui.routes.workflow import workflow_bp
from web_ui.routes.feedback import feedback_bp
from web_ui.routes.config import config_bp
from web_ui.routes.chat import chat_bp

logger = get_logger(__name__)
settings = get_settings()

# Get the absolute path to the static folder
STATIC_FOLDER = Path(__file__).parent / 'static'

# Initialize Flask app
app = Flask(__name__, static_folder=str(STATIC_FOLDER), static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False

# Enable CORS for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize WebSocket support
sock = Sock(app)

# Register blueprints
app.register_blueprint(approvals_bp, url_prefix='/api/approvals')
app.register_blueprint(workflow_bp, url_prefix='/api/workflow')
app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
app.register_blueprint(config_bp, url_prefix='/api/config')
app.register_blueprint(chat_bp, url_prefix='/api/chat')

# WebSocket clients
ws_clients = set()


@app.route('/')
def index():
    """Serve the main UI page"""
    return send_from_directory(str(STATIC_FOLDER), 'index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'hitl_mode': settings.hitl_mode,
        'web_interface_enabled': settings.enable_web_interface
    })


@sock.route('/ws')
def websocket(ws):
    """WebSocket endpoint for real-time updates"""
    ws_clients.add(ws)
    logger.info(f"WebSocket client connected. Total clients: {len(ws_clients)}")

    try:
        while True:
            # Keep connection alive and receive messages
            data = ws.receive()
            if data:
                logger.debug(f"Received WebSocket message: {data}")
                # Echo back for heartbeat
                ws.send(data)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ws_clients.discard(ws)
        logger.info(f"WebSocket client disconnected. Total clients: {len(ws_clients)}")


def broadcast_event(event_type: str, data: dict):
    """
    Broadcast event to all connected WebSocket clients

    Args:
        event_type: Type of event (approval_requested, workflow_stage_changed, etc.)
        data: Event data to send
    """
    import json

    message = json.dumps({
        'type': event_type,
        'data': data
    })

    disconnected = set()
    for client in ws_clients:
        try:
            client.send(message)
        except Exception as e:
            logger.error(f"Failed to send to WebSocket client: {e}")
            disconnected.add(client)

    # Remove disconnected clients
    ws_clients.difference_update(disconnected)


# Make broadcast_event available globally
app.broadcast_event = broadcast_event


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


def run_server(host='0.0.0.0', port=5000, debug=False):
    """
    Run the Flask development server

    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    logger.info(f"Starting Web UI server on {host}:{port}")
    logger.info(f"HITL Mode: {settings.hitl_mode}")
    logger.info(f"Web Interface Enabled: {settings.enable_web_interface}")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Get configuration from environment
    host = os.environ.get('WEB_UI_HOST', '0.0.0.0')
    port = int(os.environ.get('WEB_UI_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    run_server(host=host, port=port, debug=debug)
