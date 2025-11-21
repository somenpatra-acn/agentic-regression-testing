/**
 * Workflow Monitor Component
 * Handles workflow visualization and monitoring
 */

/**
 * Load workflow status
 */
async function loadWorkflowStatus() {
    try {
        const response = await apiRequest('/workflow/status');

        if (response.success) {
            displayWorkflowStatus(response.workflow);
        }
    } catch (error) {
        console.error('Error loading workflow status:', error);
    }
}

/**
 * Display workflow status
 */
function displayWorkflowStatus(workflow) {
    // Update header info
    document.getElementById('workflow-app').textContent = workflow.app_name || 'N/A';
    document.getElementById('workflow-feature').textContent = workflow.feature_description || 'N/A';
    document.getElementById('workflow-status-text').textContent =
        workflow.status.charAt(0).toUpperCase() + workflow.status.slice(1);
    document.getElementById('workflow-elapsed').textContent =
        formatDuration(workflow.elapsed_time || 0);

    // Display stages timeline
    displayStagesTimeline(workflow.stages);

    // Display stage details
    displayStagesDetails(workflow.stages);
}

/**
 * Display stages timeline
 */
function displayStagesTimeline(stages) {
    const container = document.getElementById('stages-timeline');

    const stageNames = ['discovery', 'planning', 'generation', 'execution', 'reporting'];

    container.innerHTML = stageNames.map(stageName => {
        const stage = stages[stageName];
        const status = stage ? stage.status : 'pending';

        let icon = 'fa-circle';
        if (status === 'completed') icon = 'fa-check';
        else if (status === 'failed') icon = 'fa-times';
        else if (status === 'in_progress') icon = 'fa-spinner fa-spin';

        return `
            <div class="stage-item ${status}">
                <div class="stage-icon">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="stage-name">${stageName.charAt(0).toUpperCase() + stageName.slice(1)}</div>
            </div>
        `;
    }).join('');
}

/**
 * Display stage details
 */
function displayStagesDetails(stages) {
    const container = document.getElementById('stages-details');

    container.innerHTML = Object.entries(stages).map(([name, stage]) => {
        const statusBadge = getStatusBadge(stage.status);

        return `
            <div class="card">
                <h3>${name.charAt(0).toUpperCase() + name.slice(1)} Stage ${statusBadge}</h3>
                ${renderStageDetails(name, stage)}
            </div>
        `;
    }).join('');
}

/**
 * Render details for a specific stage
 */
function renderStageDetails(name, stage) {
    let details = `
        <div class="stage-detail-grid">
            <div class="detail-item">
                <strong>Status:</strong> ${stage.status}
            </div>
            <div class="detail-item">
                <strong>Duration:</strong> ${formatDuration(stage.duration || 0)}
            </div>
    `;

    // Add stage-specific details
    switch (name) {
        case 'discovery':
            details += `
                <div class="detail-item">
                    <strong>Elements Found:</strong> ${stage.elements_found || 0}
                </div>
                <div class="detail-item">
                    <strong>Pages Found:</strong> ${stage.pages_found || 0}
                </div>
            `;
            break;

        case 'planning':
            details += `
                <div class="detail-item">
                    <strong>Test Cases Created:</strong> ${stage.test_cases_created || 0}
                </div>
            `;
            break;

        case 'generation':
            details += `
                <div class="detail-item">
                    <strong>Scripts Generated:</strong> ${stage.scripts_generated || 0}
                </div>
                <div class="detail-item">
                    <strong>Scripts Validated:</strong> ${stage.scripts_validated || 0}
                </div>
            `;
            break;

        case 'execution':
            details += `
                <div class="detail-item">
                    <strong>Tests Executed:</strong> ${stage.tests_executed || 0}
                </div>
                <div class="detail-item">
                    <strong>Tests Passed:</strong> <span style="color: var(--success-color)">${stage.tests_passed || 0}</span>
                </div>
                <div class="detail-item">
                    <strong>Tests Failed:</strong> <span style="color: var(--danger-color)">${stage.tests_failed || 0}</span>
                </div>
                <div class="detail-item">
                    <strong>Pass Rate:</strong> ${(stage.pass_rate || 0).toFixed(1)}%
                </div>
            `;
            break;

        case 'reporting':
            details += `
                <div class="detail-item">
                    <strong>Reports Generated:</strong> ${stage.reports_generated || 0}
                </div>
                <div class="detail-item">
                    <strong>Formats:</strong> ${(stage.report_formats || []).join(', ') || 'N/A'}
                </div>
            `;
            break;
    }

    if (stage.error) {
        details += `
            <div class="detail-item error" style="grid-column: 1 / -1;">
                <strong>Error:</strong> ${escapeHtml(stage.error)}
            </div>
        `;
    }

    details += '</div>';

    return details;
}

/**
 * Get status badge HTML
 */
function getStatusBadge(status) {
    const badges = {
        'pending': '<span class="badge" style="background: var(--border-color)">Pending</span>',
        'in_progress': '<span class="badge" style="background: var(--primary-color)">In Progress</span>',
        'completed': '<span class="badge" style="background: var(--success-color)">Completed</span>',
        'failed': '<span class="badge" style="background: var(--danger-color)">Failed</span>'
    };
    return badges[status] || '';
}

/**
 * Reset workflow
 */
async function resetWorkflow() {
    if (!confirm('Are you sure you want to reset the workflow?')) {
        return;
    }

    try {
        const response = await apiRequest('/workflow/reset', {
            method: 'POST'
        });

        if (response.success) {
            showToast('Workflow reset successfully', 'success');
            loadWorkflowStatus();
        }
    } catch (error) {
        console.error('Error resetting workflow:', error);
    }
}
