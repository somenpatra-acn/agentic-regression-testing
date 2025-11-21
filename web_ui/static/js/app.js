/**
 * Main Application JavaScript
 * Handles navigation, WebSocket connections, and global state
 */

// Global state
const appState = {
    currentView: 'dashboard',
    ws: null,
    connected: false,
    userName: 'Web UI User',
    selectedApprovalId: null
};

// API base URL
const API_BASE = window.location.origin + '/api';
const WS_URL = `ws://${window.location.host}/ws`;

/**
 * Initialize the application
 */
function init() {
    console.log('Initializing HITL Web Interface...');

    // Setup navigation
    setupNavigation();

    // Connect WebSocket
    connectWebSocket();

    // Load initial data
    loadDashboardData();

    // Setup auto-refresh
    setInterval(() => {
        if (appState.currentView === 'dashboard') {
            loadDashboardData();
        } else if (appState.currentView === 'approvals') {
            loadPendingApprovals();
        } else if (appState.currentView === 'workflow') {
            loadWorkflowStatus();
        }
    }, 5000); // Refresh every 5 seconds

    console.log('Application initialized');
}

/**
 * Setup navigation between views
 */
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));

            // Add active class to clicked item
            item.classList.add('active');

            // Get view name
            const view = item.dataset.view;

            // Switch view
            switchView(view);
        });
    });
}

/**
 * Switch to a different view
 */
function switchView(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });

    // Show selected view
    const targetView = document.getElementById(`${viewName}-view`);
    if (targetView) {
        targetView.classList.add('active');
        appState.currentView = viewName;

        // Load view-specific data
        switch (viewName) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'approvals':
                loadPendingApprovals();
                break;
            case 'workflow':
                loadWorkflowStatus();
                break;
            case 'chat':
                loadChatHistory();
                break;
            case 'config':
                loadConfiguration();
                break;
        }
    }
}

/**
 * Connect to WebSocket for real-time updates
 */
function connectWebSocket() {
    console.log('Connecting to WebSocket...');

    try {
        appState.ws = new WebSocket(WS_URL);

        appState.ws.onopen = () => {
            console.log('WebSocket connected');
            appState.connected = true;
            updateConnectionStatus(true);
            showToast('Connected to server', 'success');
        };

        appState.ws.onclose = () => {
            console.log('WebSocket disconnected');
            appState.connected = false;
            updateConnectionStatus(false);
            showToast('Disconnected from server', 'warning');

            // Attempt to reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };

        appState.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            showToast('Connection error', 'error');
        };

        appState.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        // Heartbeat to keep connection alive
        setInterval(() => {
            if (appState.ws && appState.ws.readyState === WebSocket.OPEN) {
                appState.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // Every 30 seconds

    } catch (error) {
        console.error('Error creating WebSocket:', error);
        updateConnectionStatus(false);
    }
}

/**
 * Handle WebSocket messages
 */
function handleWebSocketMessage(data) {
    console.log('WebSocket message:', data);

    switch (data.type) {
        case 'approval_requested':
            showToast(`New approval request: ${data.data.approval_type}`, 'info');
            if (appState.currentView === 'approvals') {
                loadPendingApprovals();
            }
            loadDashboardData(); // Update counts
            break;

        case 'approval_updated':
            showToast(`Approval ${data.data.status}: ${data.data.approval_id}`, 'success');
            if (appState.currentView === 'approvals') {
                loadPendingApprovals();
            }
            loadDashboardData();
            break;

        case 'workflow_stage_changed':
            showToast(`Workflow stage: ${data.data.stage}`, 'info');
            if (appState.currentView === 'workflow') {
                loadWorkflowStatus();
            }
            loadDashboardData();
            break;

        case 'workflow_reset':
            showToast(data.data.message, 'info');
            if (appState.currentView === 'workflow') {
                loadWorkflowStatus();
            }
            break;

        case 'feedback_submitted':
            showToast('Feedback submitted successfully', 'success');
            break;

        case 'chat_message':
            if (appState.currentView === 'chat') {
                addChatMessage(data.data.assistant_message);
            }
            break;

        case 'error_occurred':
            showToast(`Error: ${data.data.message}`, 'error');
            break;
    }
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusIndicator = document.getElementById('connection-status');

    if (connected) {
        statusIndicator.classList.add('connected');
        statusIndicator.classList.remove('disconnected');
        statusIndicator.querySelector('span').textContent = 'Connected';
    } else {
        statusIndicator.classList.add('disconnected');
        statusIndicator.classList.remove('connected');
        statusIndicator.querySelector('span').textContent = 'Disconnected';
    }
}

/**
 * Make API request
 */
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showToast(`API error: ${error.message}`, 'error');
        throw error;
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas fa-${getToastIcon(type)}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Remove toast after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Get icon for toast type
 */
function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Format time remaining
 */
function formatTimeRemaining(seconds) {
    if (seconds <= 0) return 'Expired';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}h ${minutes}m remaining`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s remaining`;
    } else {
        return `${secs}s remaining`;
    }
}

/**
 * Format timestamp
 */
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

/**
 * Format duration
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize app when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
