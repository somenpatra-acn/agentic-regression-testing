/**
 * Approval Panel Component
 * Handles approval requests and review
 */

/**
 * Load pending approvals
 */
async function loadPendingApprovals() {
    try {
        const response = await apiRequest('/approvals/pending');

        if (response.success) {
            displayApprovals(response.approvals);
        }
    } catch (error) {
        console.error('Error loading pending approvals:', error);
    }
}

/**
 * Display approvals list
 */
function displayApprovals(approvals) {
    const container = document.getElementById('approvals-list');

    if (approvals.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <p>No pending approvals</p>
            </div>
        `;
        return;
    }

    container.innerHTML = approvals.map(approval => {
        const isUrgent = approval.time_remaining < 300; // Less than 5 minutes
        const timerClass = isUrgent ? 'urgent' : '';

        return `
            <div class="approval-item" onclick="showApprovalDetails('${approval.id}')">
                <div class="approval-header">
                    <span class="approval-type ${approval.type}">${approval.type}</span>
                    <span class="approval-timer ${timerClass}">
                        <i class="fas fa-clock"></i>
                        ${formatTimeRemaining(approval.time_remaining)}
                    </span>
                </div>
                <div class="approval-summary">
                    ${escapeHtml(approval.summary)}
                </div>
                <div class="approval-footer">
                    <span class="approval-id">ID: ${approval.id}</span>
                    <span class="approval-requested">${formatTimestamp(approval.requested_at)}</span>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Show approval details in modal
 */
async function showApprovalDetails(approvalId) {
    try {
        const response = await apiRequest(`/approvals/${approvalId}`);

        if (response.success) {
            const approval = response.approval;
            appState.selectedApprovalId = approvalId;

            // Update modal content
            document.getElementById('modal-title').textContent =
                `${approval.approval_type} - ${approval.item_id}`;

            const modalBody = document.getElementById('modal-body');
            modalBody.innerHTML = `
                <div class="approval-details">
                    <div class="detail-row">
                        <strong>Type:</strong> ${approval.approval_type}
                    </div>
                    <div class="detail-row">
                        <strong>Item ID:</strong> ${approval.item_id}
                    </div>
                    <div class="detail-row">
                        <strong>Summary:</strong> ${escapeHtml(approval.item_summary)}
                    </div>
                    <div class="detail-row">
                        <strong>Requested:</strong> ${formatTimestamp(approval.requested_at)}
                    </div>
                    <div class="detail-row">
                        <strong>Time Remaining:</strong> ${formatTimeRemaining(approval.time_remaining)}
                    </div>
                    <div class="detail-section">
                        <strong>Item Data:</strong>
                        <pre><code class="language-json">${escapeHtml(JSON.stringify(approval.item_data, null, 2))}</code></pre>
                    </div>
                </div>
            `;

            // Highlight code
            hljs.highlightAll();

            // Show modal
            document.getElementById('approval-modal').classList.add('show');
        }
    } catch (error) {
        console.error('Error loading approval details:', error);
    }
}

/**
 * Close approval modal
 */
function closeApprovalModal() {
    document.getElementById('approval-modal').classList.remove('show');
    appState.selectedApprovalId = null;
}

/**
 * Approve the current item
 */
async function approveItem() {
    if (!appState.selectedApprovalId) return;

    const comments = prompt('Add optional comments:');

    try {
        const response = await apiRequest(`/approvals/${appState.selectedApprovalId}/approve`, {
            method: 'POST',
            body: JSON.stringify({
                approved_by: appState.userName,
                comments: comments || ''
            })
        });

        if (response.success) {
            showToast('Approval confirmed', 'success');
            closeApprovalModal();
            loadPendingApprovals();
        } else {
            showToast(response.error || 'Approval failed', 'error');
        }
    } catch (error) {
        console.error('Error approving item:', error);
    }
}

/**
 * Show reject form
 */
function showRejectForm() {
    const reason = prompt('Please provide a reason for rejection:');

    if (reason) {
        rejectItem(reason);
    }
}

/**
 * Reject the current item
 */
async function rejectItem(reason) {
    if (!appState.selectedApprovalId) return;

    try {
        const response = await apiRequest(`/approvals/${appState.selectedApprovalId}/reject`, {
            method: 'POST',
            body: JSON.stringify({
                approved_by: appState.userName,
                rejection_reason: reason
            })
        });

        if (response.success) {
            showToast('Approval rejected', 'success');
            closeApprovalModal();
            loadPendingApprovals();
        } else {
            showToast(response.error || 'Rejection failed', 'error');
        }
    } catch (error) {
        console.error('Error rejecting item:', error);
    }
}

/**
 * Show modify form
 */
function showModifyForm() {
    const modifications = prompt('Describe modifications (JSON format):');

    if (modifications) {
        try {
            const modData = JSON.parse(modifications);
            modifyAndApprove(modData);
        } catch (error) {
            showToast('Invalid JSON format', 'error');
        }
    }
}

/**
 * Modify and approve the current item
 */
async function modifyAndApprove(modifications) {
    if (!appState.selectedApprovalId) return;

    try {
        const response = await apiRequest(`/approvals/${appState.selectedApprovalId}/modify`, {
            method: 'POST',
            body: JSON.stringify({
                approved_by: appState.userName,
                modifications: modifications,
                comments: 'Modified via web UI'
            })
        });

        if (response.success) {
            showToast('Approval modified and confirmed', 'success');
            closeApprovalModal();
            loadPendingApprovals();
        } else {
            showToast(response.error || 'Modification failed', 'error');
        }
    } catch (error) {
        console.error('Error modifying item:', error);
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('approval-modal');
    if (e.target === modal) {
        closeApprovalModal();
    }
});
