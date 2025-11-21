/**
 * Feedback Form Component
 * Handles feedback submission
 */

/**
 * Submit feedback
 */
async function submitFeedback(event) {
    event.preventDefault();

    const formData = {
        item_id: document.getElementById('feedback-item-id').value,
        item_type: document.getElementById('feedback-item-type').value,
        rating: parseInt(document.getElementById('feedback-rating').value),
        comment: document.getElementById('feedback-comment').value,
        is_false_positive: document.getElementById('feedback-false-positive').checked,
        is_known_issue: document.getElementById('feedback-known-issue').checked,
        needs_investigation: document.getElementById('feedback-needs-investigation').checked,
        provided_by: appState.userName
    };

    try {
        const response = await apiRequest('/feedback/', {
            method: 'POST',
            body: JSON.stringify(formData)
        });

        if (response.success) {
            showToast('Feedback submitted successfully', 'success');
            // Reset form
            document.getElementById('feedback-form').reset();
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
    }
}
