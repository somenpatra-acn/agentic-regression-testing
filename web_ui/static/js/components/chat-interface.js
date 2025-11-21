/**
 * Chat Interface Component
 * Handles chat with orchestrator
 */

/**
 * Load chat history
 */
async function loadChatHistory() {
    try {
        const response = await apiRequest('/chat/history?limit=50');

        if (response.success && response.messages.length > 0) {
            const container = document.getElementById('chat-messages');
            // Clear existing messages except welcome message
            const welcomeMsg = container.querySelector('.chat-message.assistant');
            container.innerHTML = '';
            if (welcomeMsg) {
                container.appendChild(welcomeMsg);
            }

            // Add history messages
            response.messages.forEach(msg => {
                addChatMessage(msg);
            });

            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

/**
 * Send chat message
 */
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to UI
    addChatMessage({
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
    });

    // Clear input
    input.value = '';

    // Send to server
    try {
        const response = await apiRequest('/chat/message', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                context: {}
            })
        });

        if (response.success) {
            addChatMessage(response.response);
        }
    } catch (error) {
        console.error('Error sending chat message:', error);
        addChatMessage({
            role: 'assistant',
            content: 'Sorry, I encountered an error processing your message.',
            timestamp: new Date().toISOString()
        });
    }
}

/**
 * Add message to chat
 */
function addChatMessage(message) {
    const container = document.getElementById('chat-messages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${message.role}`;

    const avatar = message.role === 'user' ?
        '<i class="fas fa-user"></i>' :
        '<i class="fas fa-robot"></i>';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${formatMessageContent(message.content)}
            <div class="message-time">${formatTimestamp(message.timestamp)}</div>
        </div>
    `;

    container.appendChild(messageDiv);

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

/**
 * Format message content (support markdown-like formatting)
 */
function formatMessageContent(content) {
    // Convert newlines to <br>
    let formatted = escapeHtml(content).replace(/\n/g, '<br>');

    // Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Bullet points: •
    formatted = formatted.replace(/^• /gm, '&bull; ');

    return formatted;
}

/**
 * Handle Enter key in chat input
 */
function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}
