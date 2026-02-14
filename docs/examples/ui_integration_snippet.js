/**
 * Kite Token Manager - UI Integration Snippet
 *
 * Simple JavaScript class to integrate Kite token status into your existing UI
 * Usage: Include this in your existing application and initialize with your API base URL
 */

class KiteTokenManager {
    constructor(apiBase = 'http://localhost:8079') {
        this.apiBase = apiBase;
        this.callbackUrl = null;
        this.autoRefreshInterval = null;
        this.onStatusChange = null; // Callback for status changes
    }

    /**
     * Initialize the token manager
     */
    async init() {
        await this.loadCallbackUrl();
        return this;
    }

    /**
     * Check current token status
     * @returns {Promise<Object>} Token status data
     */
    async checkTokenStatus() {
        try {
            const response = await fetch(`${this.apiBase}/api/token/status`);
            const data = await response.json();

            // Trigger callback if provided
            if (this.onStatusChange) {
                this.onStatusChange(data);
            }

            return data;
        } catch (error) {
            console.error('Error checking token status:', error);
            throw error;
        }
    }

    /**
     * Get token refresh information
     * @returns {Promise<Object>} Refresh info with login URL
     */
    async getRefreshInfo() {
        try {
            const response = await fetch(`${this.apiBase}/api/token/refresh-info`);
            return await response.json();
        } catch (error) {
            console.error('Error getting refresh info:', error);
            throw error;
        }
    }

    /**
     * Get callback URL for OAuth configuration
     * @returns {Promise<string>} Callback URL
     */
    async loadCallbackUrl() {
        try {
            const response = await fetch(`${this.apiBase}/api/token/callback-url`);
            const data = await response.json();
            this.callbackUrl = data.callback_url;
            return this.callbackUrl;
        } catch (error) {
            console.error('Error loading callback URL:', error);
            throw error;
        }
    }

    /**
     * Check if token is valid
     * @returns {Promise<boolean>} True if token is valid
     */
    async isTokenValid() {
        const status = await this.checkTokenStatus();
        return status.kite_token_valid;
    }

    /**
     * Get login URL for token refresh
     * @returns {Promise<string>} Kite Connect login URL
     */
    async getLoginUrl() {
        const refreshInfo = await this.getRefreshInfo();
        return refreshInfo.login_url;
    }

    /**
     * Start auto-refresh monitoring
     * @param {number} intervalMs - Refresh interval in milliseconds (default: 30000)
     */
    startAutoRefresh(intervalMs = 30000) {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }

        this.autoRefreshInterval = setInterval(() => {
            this.checkTokenStatus().catch(error => {
                console.error('Auto-refresh error:', error);
            });
        }, intervalMs);
    }

    /**
     * Stop auto-refresh monitoring
     */
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    /**
     * Set callback for status changes
     * @param {Function} callback - Function to call when status changes
     */
    onStatusChanged(callback) {
        this.onStatusChange = callback;
    }

    /**
     * Open token refresh page in new window
     */
    async openRefreshPage() {
        const loginUrl = await this.getLoginUrl();
        if (loginUrl) {
            window.open(loginUrl, '_blank');
        }
    }

    /**
     * Get formatted status for display
     * @returns {Promise<Object>} Formatted status object
     */
    async getFormattedStatus() {
        const status = await this.checkTokenStatus();

        return {
            tokenStatus: status.kite_token_valid ? 'Valid' : 'Expired',
            tokenIcon: status.kite_token_valid ? '✅' : '❌',
            needsRefresh: status.needs_refresh,
            maskedToken: status.kite_token_masked,
            yahooStatus: status.yahoo_finance_available ? 'Available' : 'Unavailable',
            yahooIcon: status.yahoo_finance_available ? '✅' : '❌',
            lastChecked: new Date().toLocaleString()
        };
    }
}

/**
 * Simple UI Helper Functions
 * Use these in your existing UI components
 */

// Create a status widget
async function createTokenStatusWidget(containerId, apiBase = 'http://localhost:8079') {
    const container = document.getElementById(containerId);
    const tokenManager = await new KiteTokenManager(apiBase).init();

    async function updateWidget() {
        const status = await tokenManager.getFormattedStatus();

        container.innerHTML = `
            <div class="token-status-widget">
                <div class="status-item">
                    <span>Kite Token:</span>
                    <span>${status.tokenIcon} ${status.tokenStatus}</span>
                </div>
                <div class="status-item">
                    <span>Yahoo Finance:</span>
                    <span>${status.yahooIcon} ${status.yahooStatus}</span>
                </div>
                ${status.needsRefresh ? `
                    <button onclick="refreshToken('${apiBase}')" class="refresh-btn">
                        🔄 Refresh Token
                    </button>
                ` : ''}
                <div class="last-updated">Updated: ${status.lastChecked}</div>
            </div>
        `;
    }

    // Initial load
    await updateWidget();

    // Auto-refresh every 30 seconds
    setInterval(updateWidget, 30000);

    return tokenManager;
}

// Refresh token function
async function refreshToken(apiBase = 'http://localhost:8079') {
    const tokenManager = new KiteTokenManager(apiBase);
    await tokenManager.openRefreshPage();
}

// Check token before API calls
async function ensureTokenValid(apiBase = 'http://localhost:8079') {
    const tokenManager = new KiteTokenManager(apiBase);
    const isValid = await tokenManager.isTokenValid();

    if (!isValid) {
        const shouldRefresh = confirm('Kite token has expired. Would you like to refresh it now?');
        if (shouldRefresh) {
            await tokenManager.openRefreshPage();
        }
        throw new Error('Kite token expired. Please refresh your token.');
    }

    return true;
}

/**
 * Usage Examples:
 */

// Example 1: Simple status check
/*
const tokenManager = await new KiteTokenManager('http://localhost:8079').init();
const status = await tokenManager.checkTokenStatus();
console.log('Token valid:', status.kite_token_valid);
*/

// Example 2: Auto-refresh monitoring
/*
const tokenManager = await new KiteTokenManager().init();
tokenManager.onStatusChanged((status) => {
    if (!status.kite_token_valid) {
        alert('Token expired! Please refresh.');
    }
});
tokenManager.startAutoRefresh();
*/

// Example 3: Create status widget
/*
createTokenStatusWidget('token-status-container');
*/

// Example 4: Check token before trading operations
/*
async function placeTrade() {
    try {
        await ensureTokenValid();
        // Proceed with trading API calls
        console.log('Token is valid, proceeding with trade...');
    } catch (error) {
        console.error('Cannot place trade:', error.message);
    }
}
*/

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KiteTokenManager, createTokenStatusWidget, refreshToken, ensureTokenValid };
}

// Export for ES6 modules
if (typeof window !== 'undefined') {
    window.KiteTokenManager = KiteTokenManager;
    window.createTokenStatusWidget = createTokenStatusWidget;
    window.refreshToken = refreshToken;
    window.ensureTokenValid = ensureTokenValid;
}
