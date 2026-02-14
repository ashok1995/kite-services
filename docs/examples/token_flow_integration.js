/**
 * Kite Token Flow Integration
 *
 * Complete token refresh workflow for your UI
 * Handles the full flow: login -> request token -> access token
 */

class KiteTokenFlow {
    constructor(apiBase = 'http://localhost:8079') {
        this.apiBase = apiBase;
        this.loginUrl = null;
        this.callbackUrl = null;
        this.onTokenGenerated = null; // Callback when new token is generated
    }

    /**
     * Initialize the token flow
     */
    async init() {
        await this.loadUrls();
        return this;
    }

    /**
     * Load login and callback URLs
     */
    async loadUrls() {
        try {
            // Get callback URL
            const callbackResponse = await fetch(`${this.apiBase}/api/token/callback-url`);
            const callbackData = await callbackResponse.json();
            this.callbackUrl = callbackData.callback_url;

            // Get login URL
            const refreshResponse = await fetch(`${this.apiBase}/api/token/refresh-info`);
            const refreshData = await refreshResponse.json();
            this.loginUrl = refreshData.login_url;

        } catch (error) {
            console.error('Error loading URLs:', error);
            throw error;
        }
    }

    /**
     * Check if token needs refresh
     * @returns {Promise<boolean>} True if token needs refresh
     */
    async needsRefresh() {
        try {
            const response = await fetch(`${this.apiBase}/api/token/status`);
            const data = await response.json();
            return data.needs_refresh;
        } catch (error) {
            console.error('Error checking token status:', error);
            return true; // Assume needs refresh on error
        }
    }

    /**
     * Get current token status
     * @returns {Promise<Object>} Token status data
     */
    async getTokenStatus() {
        const response = await fetch(`${this.apiBase}/api/token/status`);
        return await response.json();
    }

    /**
     * Open login page to get request token
     * @returns {string} Login URL
     */
    openLoginPage() {
        if (this.loginUrl) {
            window.open(this.loginUrl, '_blank');
            return this.loginUrl;
        }
        throw new Error('Login URL not loaded. Call init() first.');
    }

    /**
     * Extract request token from callback URL
     * @param {string} callbackUrl - The callback URL with request token
     * @returns {string} Request token
     */
    extractRequestToken(callbackUrl) {
        try {
            const url = new URL(callbackUrl);
            const requestToken = url.searchParams.get('request_token');

            if (!requestToken) {
                throw new Error('No request_token found in callback URL');
            }

            return requestToken;
        } catch (error) {
            throw new Error('Invalid callback URL format: ' + error.message);
        }
    }

    /**
     * Generate access token from request token
     * @param {string} requestToken - Request token from callback
     * @returns {Promise<Object>} Access token data
     */
    async generateAccessToken(requestToken) {
        try {
            const response = await fetch(`${this.apiBase}/api/token/generate-access-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    request_token: requestToken
                })
            });

            const data = await response.json();

            if (data.success) {
                // Trigger callback if provided
                if (this.onTokenGenerated) {
                    this.onTokenGenerated(data);
                }
                return data;
            } else {
                throw new Error(data.detail || 'Failed to generate access token');
            }

        } catch (error) {
            throw new Error('Token generation failed: ' + error.message);
        }
    }

    /**
     * Complete token refresh flow
     * @param {string} callbackUrl - Callback URL with request token
     * @returns {Promise<Object>} Access token data
     */
    async completeTokenRefresh(callbackUrl) {
        const requestToken = this.extractRequestToken(callbackUrl);
        return await this.generateAccessToken(requestToken);
    }

    /**
     * Set callback for when token is generated
     * @param {Function} callback - Function to call with token data
     */
    onTokenGeneratedCallback(callback) {
        this.onTokenGenerated = callback;
    }

    /**
     * Get callback URL for Kite Connect app configuration
     * @returns {string} Callback URL
     */
    getCallbackUrl() {
        return this.callbackUrl;
    }
}

/**
 * UI Helper Functions
 * Ready-to-use functions for common UI patterns
 */

// Simple token refresh button
function createTokenRefreshButton(containerId, apiBase = 'http://localhost:8079') {
    const container = document.getElementById(containerId);
    const tokenFlow = new KiteTokenFlow(apiBase);

    container.innerHTML = `
        <button id="refresh-token-btn" class="token-refresh-btn" style="
            background: #e67e22;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        ">
            🔄 Refresh Kite Token
        </button>
        <div id="token-instructions" style="display: none; margin-top: 10px; padding: 10px; background: #fff3cd; border-radius: 4px;">
            <p><strong>Steps:</strong></p>
            <ol>
                <li>Click the login button above (opens in new window)</li>
                <li>Login with your Zerodha credentials</li>
                <li>Copy the callback URL and paste it below</li>
            </ol>
            <input type="text" id="callback-input" placeholder="Paste callback URL here..." style="width: 100%; padding: 8px; margin: 10px 0;">
            <button id="generate-token-btn" style="background: #27ae60; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                Generate Access Token
            </button>
            <div id="token-result" style="margin-top: 10px;"></div>
        </div>
    `;

    // Event listeners
    document.getElementById('refresh-token-btn').addEventListener('click', async () => {
        await tokenFlow.init();
        tokenFlow.openLoginPage();
        document.getElementById('token-instructions').style.display = 'block';
    });

    document.getElementById('generate-token-btn').addEventListener('click', async () => {
        const callbackUrl = document.getElementById('callback-input').value.trim();
        const resultDiv = document.getElementById('token-result');

        if (!callbackUrl) {
            resultDiv.innerHTML = '<div style="color: red;">Please paste the callback URL</div>';
            return;
        }

        try {
            const tokenData = await tokenFlow.completeTokenRefresh(callbackUrl);

            resultDiv.innerHTML = `
                <div style="color: green; background: #d5f4e6; padding: 10px; border-radius: 4px; margin-top: 10px;">
                    <strong>✅ Success!</strong><br>
                    <strong>Access Token:</strong><br>
                    <code style="background: #2c3e50; color: white; padding: 5px; display: block; margin: 5px 0; word-break: break-all;">
                        ${tokenData.access_token}
                    </code>
                    <p><strong>Next:</strong> Update your KITE_ACCESS_TOKEN environment variable and restart the service.</p>
                </div>
            `;
        } catch (error) {
            resultDiv.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
        }
    });
}

// Status indicator widget
async function createTokenStatusIndicator(containerId, apiBase = 'http://localhost:8079') {
    const container = document.getElementById(containerId);
    const tokenFlow = new KiteTokenFlow(apiBase);

    try {
        const status = await tokenFlow.getTokenStatus();
        const statusColor = status.kite_token_valid ? '#27ae60' : '#e74c3c';
        const statusText = status.kite_token_valid ? 'Valid' : 'Expired';
        const statusIcon = status.kite_token_valid ? '✅' : '❌';

        container.innerHTML = `
            <div class="token-status-indicator" style="
                display: flex;
                align-items: center;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                border-left: 4px solid ${statusColor};
            ">
                <span style="margin-right: 10px; font-size: 16px;">${statusIcon}</span>
                <div>
                    <strong>Kite Token:</strong> ${statusText}<br>
                    <small>Token: ${status.kite_token_masked || 'Not configured'}</small>
                </div>
                ${status.needs_refresh ? `
                    <button onclick="createTokenRefreshButton('${containerId}', '${apiBase}')" style="
                        margin-left: auto;
                        background: #e67e22;
                        color: white;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 3px;
                        cursor: pointer;
                        font-size: 12px;
                    ">
                        Refresh
                    </button>
                ` : ''}
            </div>
        `;
    } catch (error) {
        container.innerHTML = `<div style="color: red;">Error loading token status: ${error.message}</div>`;
    }
}

// Auto-check token before API calls
async function ensureValidToken(apiBase = 'http://localhost:8079') {
    const tokenFlow = new KiteTokenFlow(apiBase);
    const needsRefresh = await tokenFlow.needsRefresh();

    if (needsRefresh) {
        const shouldRefresh = confirm(
            'Your Kite token has expired. Would you like to refresh it now?\n\n' +
            'Click OK to open the login page, or Cancel to continue (API calls may fail).'
        );

        if (shouldRefresh) {
            await tokenFlow.init();
            tokenFlow.openLoginPage();

            // Return a promise that resolves when user provides new token
            return new Promise((resolve, reject) => {
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0,0,0,0.8); display: flex; align-items: center;
                    justify-content: center; z-index: 10000;
                `;

                modal.innerHTML = `
                    <div style="background: white; padding: 20px; border-radius: 10px; max-width: 500px; width: 90%;">
                        <h3>🔐 Complete Token Refresh</h3>
                        <p>After logging in, paste the callback URL below:</p>
                        <input type="text" id="modal-callback-input" placeholder="Paste callback URL here..." style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px;">
                        <div style="text-align: right;">
                            <button id="modal-cancel" style="background: #95a5a6; color: white; border: none; padding: 10px 15px; border-radius: 4px; margin-right: 10px; cursor: pointer;">Cancel</button>
                            <button id="modal-generate" style="background: #27ae60; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer;">Generate Token</button>
                        </div>
                        <div id="modal-result" style="margin-top: 10px;"></div>
                    </div>
                `;

                document.body.appendChild(modal);

                document.getElementById('modal-cancel').onclick = () => {
                    document.body.removeChild(modal);
                    reject(new Error('Token refresh cancelled'));
                };

                document.getElementById('modal-generate').onclick = async () => {
                    const callbackUrl = document.getElementById('modal-callback-input').value.trim();
                    const resultDiv = document.getElementById('modal-result');

                    if (!callbackUrl) {
                        resultDiv.innerHTML = '<div style="color: red;">Please paste the callback URL</div>';
                        return;
                    }

                    try {
                        const tokenData = await tokenFlow.completeTokenRefresh(callbackUrl);
                        resultDiv.innerHTML = `
                            <div style="color: green; padding: 10px; background: #d5f4e6; border-radius: 4px;">
                                <strong>✅ Token generated!</strong><br>
                                Please update your environment variables and restart the service.
                            </div>
                        `;

                        setTimeout(() => {
                            document.body.removeChild(modal);
                            resolve(tokenData);
                        }, 2000);

                    } catch (error) {
                        resultDiv.innerHTML = `<div style="color: red;">Error: ${error.message}</div>`;
                    }
                };
            });
        } else {
            throw new Error('Token expired and refresh declined');
        }
    }

    return true; // Token is valid
}

/**
 * Export for different module systems
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        KiteTokenFlow,
        createTokenRefreshButton,
        createTokenStatusIndicator,
        ensureValidToken
    };
}

if (typeof window !== 'undefined') {
    window.KiteTokenFlow = KiteTokenFlow;
    window.createTokenRefreshButton = createTokenRefreshButton;
    window.createTokenStatusIndicator = createTokenStatusIndicator;
    window.ensureValidToken = ensureValidToken;
}

/**
 * Usage Examples:
 */

/*
// Example 1: Simple refresh button
createTokenRefreshButton('refresh-container');

// Example 2: Status indicator
createTokenStatusIndicator('status-container');

// Example 3: Check token before API calls
async function makeTradeApiCall() {
    try {
        await ensureValidToken();
        // Proceed with trading API calls
        const response = await fetch('/api/place-order', {...});
    } catch (error) {
        console.error('Cannot make API call:', error.message);
    }
}

// Example 4: Custom flow
const tokenFlow = new KiteTokenFlow();
await tokenFlow.init();

// Check if refresh needed
if (await tokenFlow.needsRefresh()) {
    // Open login page
    tokenFlow.openLoginPage();

    // User provides callback URL
    const callbackUrl = prompt('Paste callback URL:');

    // Generate access token
    const tokenData = await tokenFlow.completeTokenRefresh(callbackUrl);
    console.log('New token:', tokenData.access_token);
}
*/
