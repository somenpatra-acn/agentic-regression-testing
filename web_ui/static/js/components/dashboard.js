/**
 * Dashboard Component
 * Handles dashboard view and statistics
 */

/**
 * Load dashboard data
 */
async function loadDashboardData() {
    try {
        // Load approval statistics
        const statsResponse = await apiRequest('/approvals/statistics');
        if (statsResponse.success) {
            updateDashboardStats(statsResponse.statistics);
        }

        // Load workflow status
        const workflowResponse = await apiRequest('/workflow/status');
        if (workflowResponse.success) {
            updateWorkflowProgress(workflowResponse.workflow);
        }

    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

/**
 * Update dashboard statistics
 */
function updateDashboardStats(stats) {
    // Update stat cards
    document.getElementById('stat-pending').textContent = stats.pending || 0;
    document.getElementById('stat-approved').textContent = stats.approved || 0;
    document.getElementById('stat-rejected').textContent = stats.rejected || 0;

    // Update pending badge in sidebar
    document.getElementById('pending-count').textContent = stats.pending || 0;

    // Update recent activity
    if (stats.recent_approvals && stats.recent_approvals.length > 0) {
        updateRecentActivity(stats.recent_approvals);
    } else {
        document.getElementById('recent-activity').innerHTML = '<p class="empty-state">No recent activity</p>';
    }
}

/**
 * Update workflow progress on dashboard
 */
function updateWorkflowProgress(workflow) {
    const statusElement = document.getElementById('stat-workflow');
    statusElement.textContent = workflow.status.charAt(0).toUpperCase() + workflow.status.slice(1);

    const progressContainer = document.getElementById('workflow-progress');

    if (workflow.status === 'idle') {
        progressContainer.innerHTML = '<p class="empty-state">No workflow running</p>';
        return;
    }

    // Show current stage and progress
    const completedStages = workflow.completed_stages || [];
    const totalStages = Object.keys(workflow.stages || {}).length;
    const progress = (completedStages.length / totalStages) * 100;

    progressContainer.innerHTML = `
        <div class="progress-info">
            <p><strong>Application:</strong> ${escapeHtml(workflow.app_name || 'N/A')}</p>
            <p><strong>Current Stage:</strong> ${escapeHtml(workflow.current_stage || 'N/A')}</p>
            <p><strong>Progress:</strong> ${completedStages.length}/${totalStages} stages</p>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${progress}%"></div>
        </div>
    `;
}

/**
 * Update recent activity list
 */
function updateRecentActivity(approvals) {
    const container = document.getElementById('recent-activity');

    container.innerHTML = approvals.slice(0, 10).map(approval => `
        <div class="activity-item">
            <div>
                <strong>${escapeHtml(approval.type)}</strong> -
                ${escapeHtml(approval.status)}
            </div>
            <div class="time">${formatTimestamp(approval.requested_at)}</div>
        </div>
    `).join('');
}
