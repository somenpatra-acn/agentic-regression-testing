# Web UI for HITL - Human-in-the-Loop Interface

This is the web-based user interface for the Agentic AI Regression Testing Framework's Human-in-the-Loop (HITL) functionality.

## Features

- **Dashboard**: Real-time statistics and workflow progress monitoring
- **Approval Management**: Review and approve/reject test plans, test cases, and execution requests
- **Workflow Monitor**: Visualize workflow stages and progress in real-time
- **Chat Interface**: Natural language interaction with the orchestrator
- **Feedback System**: Submit feedback on test results and approvals
- **Configuration Management**: View application profiles and settings
- **WebSocket Real-time Updates**: Live notifications for approval requests and workflow changes

## Quick Start

### 1. Install Dependencies

```bash
pip install flask flask-cors flask-sock
```

### 2. Configure Environment

Update your `.env` file with web UI settings:

```env
ENABLE_WEB_INTERFACE=true
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000
SECRET_KEY=your-secret-key-here
```

### 3. Start the Web Server

```bash
python web_ui/app.py
```

Or run programmatically:

```python
from web_ui.app import run_server

run_server(host='0.0.0.0', port=5000, debug=False)
```

### 4. Access the Interface

Open your browser and navigate to:
```
http://localhost:5000
```

## Architecture

### Backend (Flask)

```
web_ui/
├── app.py                      # Main Flask application
├── routes/
│   ├── approvals.py           # Approval API endpoints
│   ├── workflow.py            # Workflow monitoring endpoints
│   ├── feedback.py            # Feedback endpoints
│   ├── config.py              # Configuration endpoints
│   └── chat.py                # Chat interface endpoints
├── services/
│   ├── approval_service.py    # Approval business logic
│   └── workflow_service.py    # Workflow state management
└── static/
    ├── index.html             # Main UI
    ├── css/styles.css         # Styling
    └── js/                    # JavaScript components
```

### Frontend (Vanilla JS)

- **app.js**: Main application logic, WebSocket, navigation
- **dashboard.js**: Dashboard statistics and activity
- **approval-panel.js**: Approval review and management
- **workflow-monitor.js**: Workflow visualization
- **chat-interface.js**: Chat with orchestrator
- **feedback-form.js**: Feedback submission
- **config-manager.js**: Configuration display

## API Endpoints

### Approvals

- `GET /api/approvals/pending` - List pending approvals
- `GET /api/approvals/<id>` - Get approval details
- `POST /api/approvals/<id>/approve` - Approve item
- `POST /api/approvals/<id>/reject` - Reject item
- `POST /api/approvals/<id>/modify` - Approve with modifications
- `GET /api/approvals/statistics` - Get approval statistics

### Workflow

- `GET /api/workflow/status` - Get current workflow status
- `GET /api/workflow/stages` - Get all stage details
- `GET /api/workflow/stages/<name>` - Get specific stage details
- `POST /api/workflow/reset` - Reset workflow

### Feedback

- `POST /api/feedback/` - Submit feedback
- `GET /api/feedback/<id>` - Get feedback by ID
- `GET /api/feedback/item/<item_id>` - Get feedback for item

### Configuration

- `GET /api/config/profiles` - List application profiles
- `GET /api/config/profiles/<name>` - Get specific profile
- `GET /api/config/settings` - Get framework settings

### Chat

- `POST /api/chat/message` - Send message to orchestrator
- `GET /api/chat/history` - Get chat history
- `POST /api/chat/clear` - Clear chat history

### WebSocket

- `ws://host:port/ws` - WebSocket for real-time updates

## Integration with HITL System

### Using WebReviewer

```python
from hitl.review_interface import WebReviewer
from hitl.approval_manager import ApprovalManager

# Initialize web reviewer
reviewer = WebReviewer(port=5000)

# Use with approval manager
approval_manager = ApprovalManager(
    hitl_mode="APPROVE_PLAN",
    interface=reviewer
)

# Request approval (blocks until web user approves/rejects)
approval = approval_manager.request_approval(
    approval_type=ApprovalType.TEST_PLAN,
    item_id="PLAN-001",
    item_data=test_plan_data,
    item_summary="Test plan for login feature"
)
```

### Workflow Integration

The workflow service automatically tracks workflow state:

```python
from web_ui.services.workflow_service import WorkflowService

service = WorkflowService()

# Start workflow
service.start_workflow("my_app", "Login functionality")

# Update stage
service.start_stage("discovery")
service.complete_stage("discovery", {
    "elements_found": 25,
    "pages_found": 5
})

# Complete workflow
service.complete_workflow()
```

## WebSocket Events

The web UI receives real-time events via WebSocket:

- `approval_requested` - New approval needs review
- `approval_updated` - Approval status changed
- `workflow_stage_changed` - Workflow progressed to new stage
- `workflow_reset` - Workflow was reset
- `feedback_submitted` - New feedback submitted
- `chat_message` - New chat message
- `error_occurred` - Error notification

## Development

### Running in Debug Mode

```bash
export FLASK_DEBUG=true  # Linux/Mac
set FLASK_DEBUG=true     # Windows

python web_ui/app.py
```

### File Structure

```
web_ui/
├── __init__.py
├── app.py                       # Main Flask app
├── routes/                      # API endpoints
│   ├── __init__.py
│   ├── approvals.py
│   ├── workflow.py
│   ├── feedback.py
│   ├── config.py
│   └── chat.py
├── services/                    # Business logic
│   ├── __init__.py
│   ├── approval_service.py
│   └── workflow_service.py
└── static/                      # Frontend
    ├── index.html
    ├── css/
    │   └── styles.css
    └── js/
        ├── app.js               # Main app
        └── components/
            ├── dashboard.js
            ├── approval-panel.js
            ├── workflow-monitor.js
            ├── chat-interface.js
            ├── feedback-form.js
            └── config-manager.js
```

## Customization

### Changing Port

Update `.env`:
```env
WEB_UI_PORT=8080
```

### Custom Styling

Edit `web_ui/static/css/styles.css` to customize colors, fonts, and layout.

### Adding New Features

1. Add API endpoint in `web_ui/routes/`
2. Register blueprint in `web_ui/app.py`
3. Add frontend component in `web_ui/static/js/components/`
4. Import component in `index.html`

## Security Considerations

### Production Deployment

1. **Change SECRET_KEY**: Use a strong random key
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Disable Debug Mode**: Set `FLASK_DEBUG=false`

3. **Use HTTPS**: Deploy behind a reverse proxy (nginx, Apache) with SSL

4. **Add Authentication**: Implement user authentication (see TODO)

5. **CORS Configuration**: Restrict allowed origins in production

### Current Limitations

- No authentication/authorization system
- No user management
- File-based approval storage (consider database for production)
- No rate limiting on API endpoints

## Troubleshooting

### WebSocket Connection Failed

**Problem**: "Disconnected from server" message

**Solutions**:
1. Check Flask server is running
2. Verify firewall allows WebSocket connections
3. If using reverse proxy, ensure WebSocket upgrade headers are forwarded

### Approvals Not Appearing

**Problem**: Pending approvals don't show in UI

**Solutions**:
1. Check `approvals/` directory exists and is writable
2. Verify approval files are valid JSON
3. Check browser console for API errors

### Workflow Not Updating

**Problem**: Workflow status shows "Idle" when tests are running

**Solutions**:
1. Ensure agents are using WorkflowService to update state
2. Check WebSocket connection is active
3. Verify workflow endpoints return data correctly

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Role-based access control (RBAC)
- [ ] Database backend for approvals/feedback
- [ ] Advanced workflow analytics
- [ ] Export reports from UI
- [ ] Mobile-responsive improvements
- [ ] Dark mode theme
- [ ] Multi-language support

## Support

For issues or questions:
- Check the main project README.md
- Review logs in `logs/` directory
- Examine browser console for frontend errors
- Check Flask logs for backend errors

## License

MIT License - See main project LICENSE file
