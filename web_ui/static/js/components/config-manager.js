/**
 * Configuration Manager Component
 * Handles configuration display
 */

/**
 * Load configuration
 */
async function loadConfiguration() {
    try {
        // Load framework settings
        const settingsResponse = await apiRequest('/config/settings');
        if (settingsResponse.success) {
            displaySettings(settingsResponse.settings);
        }

        // Load application profiles
        const profilesResponse = await apiRequest('/config/profiles');
        if (profilesResponse.success) {
            displayProfiles(profilesResponse.profiles);
        }
    } catch (error) {
        console.error('Error loading configuration:', error);
    }
}

/**
 * Display framework settings
 */
function displaySettings(settings) {
    const container = document.getElementById('framework-settings');

    container.innerHTML = Object.entries(settings).map(([key, value]) => `
        <div class="setting-item">
            <strong>${formatSettingKey(key)}</strong>
            <span>${escapeHtml(String(value))}</span>
        </div>
    `).join('');
}

/**
 * Display application profiles
 */
function displayProfiles(profiles) {
    const container = document.getElementById('app-profiles');

    if (profiles.length === 0) {
        container.innerHTML = '<p class="empty-state">No profiles configured</p>';
        return;
    }

    container.innerHTML = profiles.map(profile => `
        <div class="profile-item">
            <div>
                <strong>${escapeHtml(profile.name)}</strong>
                <div style="font-size: 0.875rem; color: var(--text-light);">
                    ${escapeHtml(profile.app_type)} • ${escapeHtml(profile.adapter)} • ${escapeHtml(profile.test_framework)}
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Format setting key
 */
function formatSettingKey(key) {
    return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}
